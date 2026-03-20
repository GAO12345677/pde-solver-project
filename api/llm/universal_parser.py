import json
import os
import re
from typing import Any, Dict, Optional

from feature.extractor import HardwareFeatureExtractor
from api.llm.llm_base import BaseParser

class UniversalParserError(RuntimeError):
    """Raised when parsing fails and no fallback is possible."""

class UniversalApiCallError(UniversalParserError):
    """Raised when LLM API call fails."""

def _sanitize_to_json_text(text: str) -> str:
    """Remove markdown fences and extract the first JSON object."""
    s = text.strip()
    s = re.sub(r"^```json\\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^```\\s*", "", s)
    s = re.sub(r"\\s*```$", "", s)
    # Find first {...} block (greedy but bounded by last brace)
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start : end + 1]
    return s.strip()

def _rule_based_parse(question: str) -> Dict[str, Any]:
    """Offline fallback parser implementing the mapping rules required."""
    q = question.strip().lower()

    # dimension mapping
    dim = 1
    if "二维" in question or "2维" in question or "2d" in q:
        dim = 2
    if "三维" in question or "3维" in question or "3d" in q:
        dim = 3

    # linear mapping (requirement: 线性->true, 非线性->false)
    linear = True
    if "非线性" in question or "nonlinear" in q:
        linear = False

    # stationary mapping (定常/稳态->true, 非定常/瞬态->false)
    stationary = True
    if "非定常" in question or "瞬态" in question or "unsteady" in q or "transient" in q:
        stationary = False

    # domain numeric thresholds
    def map_accuracy() -> float:
        if "很准" in question:
            return 0.95
        if "一般" in question or "不用太高" in question:
            return 0.8
        if "90%" in question or "0.9" in q or "90" in q:
            return 0.9
        return 0.9

    def map_realtime() -> float:
        if "不急" in question or "不着急" in question:
            return 0.7
        if "快" in question or "尽快" in question:
            return 0.9
        return 0.8

    def map_resource() -> float:
        if "不限" in question or "不限制" in question:
            return 1.0
        if "省资源" in question or "别太耗资源" in question:
            return 0.7
        return 0.7

    # equation hints
    equation_type = "heat1d" if ("热传导" in question or "heat" in q) else "poisson2d_nonlinear" if ("泊松" in question or "poisson" in q) else "heat1d"

    physics_params = {
        "dimension": dim,
        "linear": linear,
        "stationary": stationary,
        # Provide minimal defaults for our demo solvers:
        "equation_type": equation_type,
        "boundary_condition": "dirichlet",
        "problem_size": 101 if equation_type == "heat1d" else 41 * 41,
    }

    domain_demand = {
        "accuracy": map_accuracy(),
        "realtime": map_realtime(),
        "resource_budget": map_resource(),
    }

    hw_raw = HardwareFeatureExtractor.extract()
    hw = {
        "cpu_cores": int(hw_raw["vector"][1]),
        "gpu_available": bool(hw_raw.get("gpu_name")),
        "gpu_name": hw_raw.get("gpu_name"),
        "vram_gb": float(hw_raw["vector"][3]),
    }

    return {"physics_params": physics_params, "domain_demand": domain_demand, "hardware_info": hw, "parser_mode": "rule_based"}


class PDEQuestionUniversalParser(BaseParser):
    """PDE question parser backed by any BaseLLM compliant model."""

    _SYSTEM_PROMPT = (
        "你是一个 PDE/物理方程题目解析器。你的任务：只输出一个 JSON 对象，禁止输出任何解释文字。"
        "JSON schema:\n"
        "{\n"
        '  "physics_params": {\n'
        '    "dimension": 1|2|3,\n'
        '    "linear": true|false,\n'
        '    "stationary": true|false,\n'
        '    "equation_type": "heat1d"|"poisson2d_nonlinear",\n'
        '    "boundary_condition": "dirichlet"|"neumann"|"mixed",\n'
        '    "problem_size": integer\n'
        '  },\n'
        '  "domain_demand": {\n'
        '    "accuracy": number(0-1),\n'
        '    "realtime": number(0-1),\n'
        '    "resource_budget": number(0-1)\n'
        '  },\n'
        '  "hardware_info": {"note": "leave empty, it will be detected locally"}\n'
        "}\n"
        "规则映射：\n"
        "- dimension: 1维/一维→1，2维/二维→2，3维/三维→3，默认1\n"
        "- linear: 线性→true，非线性→false，默认true\n"
        "- stationary: 定常/稳态→true，非定常/瞬态→false，默认true\n"
        "- accuracy: 准→0.9，很准→0.95，一般→0.8，默认0.9\n"
        "- realtime: 快→0.9，不急→0.7，默认0.8\n"
        "- resource_budget: 省资源→0.7，不限→1.0，默认0.7\n"
        "只输出 JSON，不要包含 ```json 或其他文本。"
    )

    def __init__(self, llm_instance: Any) -> None:
        self.llm_instance = llm_instance

    async def parse(self, question: str) -> Dict[str, Any]:
        q = (question or "").strip()
        if not q:
            raise UniversalParserError("question 不能为空。")

        try:
            # Construct the prompt for the LLM
            prompt_messages = [
                {"role": "system", "content": self._SYSTEM_PROMPT},
                {"role": "user", "content": q},
            ]
            # Call the generic LLM generate method
            llm_kwargs: Dict[str, Any] = {}
            model_id = getattr(self.llm_instance, "model_id", None)
            if model_id:
                llm_kwargs["model_id"] = model_id
            llm_response = await self.llm_instance.generate(prompt=prompt_messages, **llm_kwargs)
            raw = llm_response.get("result") or llm_response.get("text", "")
            if not raw:
                raise ValueError(llm_response.get("error", "LLM returned empty content."))
            
            txt = _sanitize_to_json_text(raw)
            obj = json.loads(txt)
            if not isinstance(obj, dict):
                raise ValueError("LLM did not return a JSON object.")
            
            # Inject local hardware info (always authoritative)
            hw_raw = HardwareFeatureExtractor.extract()
            hw = {
                "cpu_cores": int(hw_raw["vector"][1]),
                "gpu_available": bool(hw_raw.get("gpu_name")),
                "gpu_name": hw_raw.get("gpu_name"),
                "vram_gb": float(hw_raw["vector"][3]),
            }
            obj["hardware_info"] = hw
            obj["parser_mode"] = f"{getattr(self.llm_instance, 'model_name', 'llm')}_llm"
            return obj
        except UniversalParserError:
            raise
        except Exception as e:
            # Fallback to rule-based parser if LLM parsing fails
            fb = _rule_based_parse(q)
            fb["fallback_reason"] = f"大模型解析失败/超时，已降级为规则解析。原因：{e}"
            return fb
