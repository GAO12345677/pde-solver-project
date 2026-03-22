import json
import re
from typing import Any, Dict

from api.llm.llm_base import BaseParser
from feature.extractor import HardwareFeatureExtractor


class UniversalParserError(RuntimeError):
    """Raised when parsing fails and no fallback is possible."""


class UniversalApiCallError(UniversalParserError):
    """Raised when LLM API call fails."""


def _sanitize_to_json_text(text: str) -> str:
    """Remove markdown fences and extract the first JSON object."""
    s = text.strip()
    s = re.sub(r"^```json\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^```\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start : end + 1]
    return s.strip()


def _rule_based_parse(question: str) -> Dict[str, Any]:
    """Offline fallback parser implementing the mapping rules required."""
    q = question.strip().lower()
    q_text = question.strip()

    dim = 1
    if "二维" in q_text or "2d" in q or "[0,1]x[0,1]" in q.replace(" ", "") or "x[0,1]" in q.replace(" ", ""):
        dim = 2
    if "三维" in q_text or "3d" in q:
        dim = 3

    linear = True
    if "非线性" in q_text or "nonlinear" in q:
        linear = False

    stationary = True
    if (
        "非定常" in q_text
        or "瞬态" in q_text
        or "unsteady" in q
        or "transient" in q
        or "u_t" in q
        or "u_tt" in q
        or "初始条件" in q_text
        or "u(x,0)" in q
    ):
        stationary = False

    def map_accuracy() -> float:
        if "很准" in q_text:
            return 0.95
        if "一般" in q_text or "不用太高" in q_text:
            return 0.8
        if "90%" in q_text or "0.9" in q or "90" in q:
            return 0.9
        return 0.9

    def map_realtime() -> float:
        if "不急" in q_text or "不着急" in q_text:
            return 0.7
        if "快" in q_text or "尽快" in q_text:
            return 0.9
        return 0.8

    def map_resource() -> float:
        if "不限" in q_text or "不限制" in q_text:
            return 1.0
        if "省资源" in q_text or "别太耗资源" in q_text:
            return 0.7
        return 0.7

    equation_type = (
        "wave1d"
        if ("波动" in q_text or "wave" in q or "u_tt" in q)
        else "heat1d"
        if ("热传导" in q_text or "热方程" in q_text or "heat" in q)
        else "poisson2d_nonlinear"
        if ("泊松" in q_text or "poisson" in q)
        else "heat1d"
    )

    if equation_type == "poisson2d_nonlinear" and dim == 1:
        equation_type = "poisson1d"
    if equation_type == "poisson2d_nonlinear" and dim == 3:
        equation_type = "poisson3d"
    if equation_type == "heat1d" and dim == 2:
        equation_type = "heat2d"
    if equation_type == "heat1d" and dim == 3:
        equation_type = "heat3d"
    if equation_type == "wave1d":
        stationary = False
        if dim == 2:
            equation_type = "wave2d"

    physics_params = {
        "dimension": dim,
        "linear": linear,
        "stationary": stationary,
        "equation_type": equation_type,
        "boundary_condition": "dirichlet",
        "problem_size": (
            101
            if equation_type in ("heat1d", "wave1d", "poisson1d")
            else 11 * 11 * 11
            if equation_type == "heat3d"
            else 21 * 21 * 21
            if equation_type == "poisson3d"
            else 41 * 41
        ),
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

    return {
        "physics_params": physics_params,
        "domain_demand": domain_demand,
        "hardware_info": hw,
        "parser_mode": "rule_based",
    }


class PDEQuestionUniversalParser(BaseParser):
    """PDE question parser backed by any BaseLLM compliant model."""

    _SYSTEM_PROMPT = (
        "你是一个 PDE/物理方程题目解析器。你的任务：只输出一个 JSON 对象，禁止输出任何解释文字。\n"
        "JSON schema:\n"
        "{\n"
        '  "physics_params": {\n'
        '    "dimension": 1|2|3,\n'
        '    "linear": true|false,\n'
        '    "stationary": true|false,\n'
        '    "equation_type": "heat1d"|"heat2d"|"heat3d"|"wave1d"|"wave2d"|"poisson1d"|"poisson3d"|"poisson2d_nonlinear",\n'
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
        "- dimension: 一维->1，二维->2，三维->3，默认 1\n"
        "- linear: 线性->true，非线性->false，默认 true\n"
        "- stationary: 定常/稳态->true，非定常/瞬态->false，默认 true\n"
        "- accuracy: 准->0.9，很准->0.95，一般->0.8，默认 0.9\n"
        "- realtime: 快->0.9，不急->0.7，默认 0.8\n"
        "- resource_budget: 省资源->0.7，不限->1.0，默认 0.7\n"
        "只输出 JSON，不要包含 ```json 或其他文本。"
    )

    def __init__(self, llm_instance: Any) -> None:
        self.llm_instance = llm_instance

    async def parse(self, question: str) -> Dict[str, Any]:
        q = (question or "").strip()
        if not q:
            raise UniversalParserError("question 不能为空。")

        try:
            prompt_messages = [
                {"role": "system", "content": self._SYSTEM_PROMPT},
                {"role": "user", "content": q},
            ]
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

            hw_raw = HardwareFeatureExtractor.extract()
            obj["hardware_info"] = {
                "cpu_cores": int(hw_raw["vector"][1]),
                "gpu_available": bool(hw_raw.get("gpu_name")),
                "gpu_name": hw_raw.get("gpu_name"),
                "vram_gb": float(hw_raw["vector"][3]),
            }
            obj["parser_mode"] = f"{getattr(self.llm_instance, 'model_name', 'llm')}_llm"
            return obj
        except UniversalParserError:
            raise
        except Exception as e:
            fb = _rule_based_parse(q)
            fb["fallback_reason"] = f"大模型解析失败/超时，已降级为规则解析。原因：{e}"
            return fb
