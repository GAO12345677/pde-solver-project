"""Service entrypoint (API service layer).

Requirements satisfied:
- Windows 10/11, Python 3.10 compatible
- host=127.0.0.1, port=8001
- reload disabled (to avoid repeated CUDA context allocations / VRAM leaks)
- On startup: detect hardware and print hardware features
- Register routes from `api/routes.py`
- Health check: GET /health
- LLM admin frontend: GET /llm/admin (static files mount)
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles  # 新增：静态文件服务
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from services.hardware import hardware_info_dict


app = FastAPI(
    title="ML-Driven PDE Solver Selection Framework",
    version="1.0.0",
    description="论文框架工程化实现：特征提取→算法选择→方程求解→结果评估/自优化（Swagger/Redoc 可调试）。",
)

# ========== 新增：挂载 LLM 前端静态文件 ==========
# 挂载你解压后的 llm_admin_frontend 文件夹
app.mount(
    "/llm_admin_static",
    StaticFiles(directory="static/llm_admin_frontend"),
    name="llm_admin_static"
)

# 新增：LLM 管理页面路由（访问 http://127.0.0.1:8001/llm/admin）
@app.get("/llm/admin")
async def llm_admin_page():
    try:
        return FileResponse("static/llm_admin_frontend/index.html")
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="LLM admin page not found! Please check if static/llm_admin_frontend/index.html exists."
        )

# ========== 原有异常处理逻辑 ==========
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None,
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # For debugging, log the full traceback
    import traceback
    print(f"Unhandled exception: {traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"Internal Server Error: {str(exc)}",
            "data": None,
        },
    )

# ========== 原有 CORS 配置 ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 原有路由注册 ==========
# Register API routes
app.include_router(api_router)

# ========== 原有健康检查 ==========
@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}

# ========== 原有启动逻辑（新增 LLM 页面提示） ==========
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
    # 新增：LLM 管理页面提示
    print("  - LLM admin:  http://127.0.0.1:8001/llm/admin")

# ========== 原有启动函数 ==========
def run() -> None:
    """Run the service with fixed host/port and reload disabled."""
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)


if __name__ == "__main__":
    run()