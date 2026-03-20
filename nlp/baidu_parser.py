"""Baidu ERNIE (Qianfan) based PDE question parser.

Goal:
Transform a natural-language PDE problem description into a structured JSON used by the framework:
  { physics_params, domain_demand, hardware_info }

Key requirements implemented:
- ERNIE-Speed-8K via Baidu Qianfan SDK (qianfan) with 10s timeout and graceful fallback.
- API keys are obtained from environment variables by default; never hard-coded.
- Thread-safe global key storage for runtime configuration (multi-user safe).
- Enforce "pure JSON" output from the LLM; sanitize code fences / extra text; robust JSON parsing.
- Hardware info auto-detected (CPU cores, GPU VRAM, GPU availability) via existing hardware extractor.
- Deterministic rule-based fallback when API not configured / timeout / parse failure.

Environment variables:
- BAIDU_QIANFAN_API_KEY        : API Key
- BAIDU_QIANFAN_SECRET_KEY     : Secret Key
- BAIDU_QIANFAN_MODEL          : default "ERNIE-Speed-8K"
- BAIDU_QIANFAN_TIMEOUT_S      : default "10"
- BAIDU_QIANFAN_MOCK           : "1" to force offline mock parsing (for tests)
"""

from __future__ import annotations

import json
import os
import re
import threading
from dataclasses import dataclass
from typing import Any, Dict, Optional

from feature.extractor import HardwareFeatureExtractor
from api.llm.llm_base import BaseParser
from api.llm.universal_parser import _rule_based_parse, _sanitize_to_json_text, UniversalParserError


class BaiduParserError(UniversalParserError):
    """Raised when parsing fails and no fallback is possible."""


class BaiduApiNotConfiguredError(UniversalParserError):
    """Raised when Baidu API key/secret are missing."""


class BaiduApiCallError(UniversalParserError):
    """Raised when Baidu API call fails."""


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.environ.get(name)
    if v is None:
        return default
    v = v.strip()
    return v if v else default


@dataclass
class BaiduKeyConfig:
    api_key: Optional[str]
    secret_key: Optional[str]


class GlobalBaiduKeyStore:
    """Thread-safe in-memory key store.

    - Defaults to env vars
    - Can be updated at runtime (not persisted to disk)
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._cfg = BaiduKeyConfig(
            api_key=_env("BAIDU_QIANFAN_API_KEY"),
            secret_key=_env("BAIDU_QIANFAN_SECRET_KEY"),
        )

    def get(self) -> BaiduKeyConfig:
        with self._lock:
            # Always re-check env so users can set it before startup without needing UI.
            api_key = _env("BAIDU_QIANFAN_API_KEY", self._cfg.api_key)
            secret_key = _env("BAIDU_QIANFAN_SECRET_KEY", self._cfg.secret_key)
            return BaiduKeyConfig(api_key=api_key, secret_key=secret_key)

    def set(self, api_key: str, secret_key: str) -> None:
        with self._lock:
            self._cfg = BaiduKeyConfig(api_key=api_key.strip(), secret_key=secret_key.strip())

    def is_configured(self) -> bool:
        cfg = self.get()
        return bool(cfg.api_key) and bool(cfg.secret_key)


GLOBAL_BAIDU_KEY_STORE = GlobalBaiduKeyStore()


class PDEQuestionBaiduParser(BaseParser):
    """PDE question parser backed by Baidu Qianfan (ERNIE-Speed-8K)."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: Optional[float] = None,
    ) -> None:
        cfg = GLOBAL_BAIDU_KEY_STORE.get()
        self.api_key = (api_key or cfg.api_key)
        self.secret_key = (secret_key or cfg.secret_key)
        self.model = model or _env("BAIDU_QIANFAN_MODEL", "ERNIE-Speed-8K") or "ERNIE-Speed-8K"
        self.timeout_s = float(timeout_s or float(_env("BAIDU_QIANFAN_TIMEOUT_S", "10") or "10"))

    def _call_qianfan(self, question: str) -> str:
        """Call Baidu Qianfan chat completion and return raw text."""
        if _env("BAIDU_QIANFAN_MOCK", "0") == "1":
            # Mock mode for tests/offline runs
            if (self.api_key or "").lower() == "bad":
                raise BaiduApiCallError("模拟：API Key 无效。")
            obj = _rule_based_parse(question)
            obj["parser_mode"] = "baidu_llm"
            return json.dumps(obj, ensure_ascii=False)

        if not self.api_key or not self.secret_key:
            raise BaiduApiNotConfiguredError(
                "百度 API Key 未配置。请设置环境变量 BAIDU_QIANFAN_API_KEY / BAIDU_QIANFAN_SECRET_KEY。"
            )

        try:
            import qianfan  # type: ignore
        except Exception as e:  # noqa: BLE001
            raise BaiduApiCallError("缺少 qianfan 依赖，请执行 pip install -r requirements.txt") from e

        # Prefer explicit key/secret per-request (avoid global mutation in multi-user scenarios).
        # DEBUG_BREAKPOINT_BAIDU_CALL: set breakpoint here.
        try:
            chat = qianfan.ChatCompletion(
                ak=self.api_key,
                sk=self.secret_key,
                timeout=self.timeout_s,
            )
            system_prompt = (
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
                "  },\n"
                '  "domain_demand": {\n'
                '    "accuracy": number(0-1),\n'
                '    "realtime": number(0-1),\n'
                '    "resource_budget": number(0-1)\n'
                "  },\n"
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
            resp = chat.do(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
            )
            # SDK returns dict; extract text content robustly
            if isinstance(resp, dict):
                if "result" in resp and isinstance(resp["result"], str):
                    return resp["result"]
                # Some SDK variants return choices
                if "body" in resp and isinstance(resp["body"], dict):
                    body = resp["body"]
                    if "result" in body and isinstance(body["result"], str):
                        return body["result"]
            return str(resp)
        except BaiduParserError:
            raise
        except Exception as e:  # noqa: BLE001
            raise BaiduApiCallError(f"百度 API 调用失败(可能超时/Key错误)：{e}") from e

    def parse(self, question: str) -> Dict[str, Any]:
        """Parse natural-language question into structured JSON.

        Returns:
            {
              "physics_params": {...},
              "domain_demand": {...},
              "hardware_info": {...},
              "parser_mode": "baidu_llm"|"rule_based"
            }
        """
        q = (question or "").strip()
        if not q:
            raise BaiduParserError("question 不能为空。")

        # 1) Try LLM parse
        try:
            raw = self._call_qianfan(q)
            txt = _sanitize_to_json_text(raw)
            obj = json.loads(txt)
            if not isinstance(obj, dict):
                raise ValueError("LLM did not return a JSON object.")
            # 2) Inject local hardware info (always authoritative)
            hw_raw = HardwareFeatureExtractor.extract()
            hw = {
                "cpu_cores": int(hw_raw["vector"][1]),
                "gpu_available": bool(hw_raw.get("gpu_name")),
                "gpu_name": hw_raw.get("gpu_name"),
                "vram_gb": float(hw_raw["vector"][3]),
            }
            obj["hardware_info"] = hw
            obj["parser_mode"] = obj.get("parser_mode") or "baidu_llm"
            return obj
        except BaiduApiNotConfiguredError:
            # Friendly fallback
            fb = _rule_based_parse(q)
            fb["fallback_reason"] = "百度API未配置，已降级为规则解析。"
            return fb
        except (BaiduApiCallError, json.JSONDecodeError, ValueError) as e:
            fb = _rule_based_parse(q)
            fb["fallback_reason"] = f"大模型解析失败/超时，已降级为规则解析。原因：{e}"
            return fb

