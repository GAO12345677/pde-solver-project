"""Service entrypoint (API service layer).

Requirements satisfied:
- Windows 10/11, Python 3.10 compatible
- host=127.0.0.1, port=8001
- reload disabled (to avoid repeated CUDA context allocations / VRAM leaks)
- On startup: detect hardware and print hardware features
- Register routes from `api/routes.py`
- Health check: GET /health
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from services.hardware import hardware_info_dict


app = FastAPI(
    title="ML-Driven PDE Solver Selection Framework",
    version="1.0.0",
    description="论文框架工程化实现：特征提取→算法选择→方程求解→结果评估/自优化（Swagger/Redoc 可调试）。",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}


@app.on_event("startup")
def on_startup() -> None:
    # DEBUG_BREAKPOINT_STARTUP: set breakpoint here.
    hw = hardware_info_dict()
    print("[startup] hardware:", hw)
    print("[startup] Baidu Qianfan config:")
    print("  - Set env BAIDU_QIANFAN_API_KEY / BAIDU_QIANFAN_SECRET_KEY to enable ERNIE-Speed-8K parsing.")
    print("  - Test parse: http://127.0.0.1:8001/docs -> /api/parse_question")
    print("  - Auto solve: http://127.0.0.1:8001/docs -> /api/auto_solve")
    print("  - Swagger:    http://127.0.0.1:8001/docs")
    print("  - Redoc:      http://127.0.0.1:8001/redoc")
    print("  - Key config: http://127.0.0.1:8001/api/baidu/config")


def run() -> None:
    """Run the service with fixed host/port and reload disabled."""
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)


if __name__ == "__main__":
    run()

