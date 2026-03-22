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

import logging
import logging.handlers
from contextlib import asynccontextmanager
from typing import Any, Dict
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from api.websocket_routes import router as websocket_router
from api.llm.llm_routes import router as llm_router
from services.hardware import hardware_info_dict
from config.app_config import get_config


def setup_logging():
    """设置日志系统"""
    cfg = get_config()
    log_dir = Path(cfg.logging.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{cfg.logging.level.lower()}.log"
    
    logging.basicConfig(
        level=getattr(logging, cfg.logging.level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=cfg.logging.max_bytes,
                backupCount=cfg.logging.backup_count,
                encoding='utf-8'
            )
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()
cfg = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup initialization without deprecated startup hooks."""
    logger.info("Starting ML-Driven PDE Solver Selection Framework...")

    hw = hardware_info_dict()
    logger.info(f"Hardware detected: {hw}")

    logger.info("Baidu Qianfan config:")
    logger.info("  - Set env BAIDU_QIANFAN_API_KEY / BAIDU_QIANFAN_SECRET_KEY to enable ERNIE-Speed-8K parsing.")
    logger.info("  - Test parse: http://127.0.0.1:8001/docs -> /api/parse_question")
    logger.info("  - Auto solve: http://127.0.0.1:8001/docs -> /api/auto_solve")
    logger.info("  - Swagger:    http://127.0.0.1:8001/docs")
    logger.info("  - Redoc:      http://127.0.0.1:8001/redoc")
    logger.info("  - Key config: http://127.0.0.1:8001/api/baidu/config")
    logger.info("  - LLM admin:  http://127.0.0.1:8001/llm/admin")

    logger.info(f"Server running on http://{cfg.server.host}:{cfg.server.port}")
    logger.info(f"Debug mode: {cfg.server.debug}")
    logger.info(f"Proxy enabled: {cfg.proxy.enabled}")
    yield

app = FastAPI(
    title="ML-Driven PDE Solver Selection Framework",
    version="1.0.0",
    description="论文框架工程化实现：特征提取→算法选择→方程求解→结果评估/自优化（Swagger/Redoc 可调试）。",
    debug=cfg.server.debug,
    lifespan=lifespan,
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
    """通用异常处理器"""
    import traceback
    error_msg = f"Unhandled exception: {str(exc)}"
    logger.error(f"{error_msg}\n{traceback.format_exc()}")
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

# ========== 路由注册 ==========
# Register API routes
app.include_router(api_router)
# Register WebSocket routes (路由本身已包含 /ws 前缀)
app.include_router(websocket_router)
# Register LLM routes
app.include_router(llm_router, prefix="/llm")

# ========== 原有健康检查 ==========
@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}

# ========== 静态文件挂载 ==========
# 挂载 React 前端构建文件
react_dist_path = Path("static/dist")
if react_dist_path.exists():
    app.mount(
        "/app",
        StaticFiles(directory=str(react_dist_path), html=True),
        name="react_frontend"
    )
    logger.info(f"React frontend mounted from: {react_dist_path} at /app")
else:
    logger.warning(f"React frontend dist not found at: {react_dist_path}")

# 挂载 LLM 管理前端（向后兼容）
llm_admin_path = Path("static/llm_admin_frontend")
if llm_admin_path.exists():
    app.mount(
        "/llm_admin_static",
        StaticFiles(directory=str(llm_admin_path)),
        name="llm_admin_static"
    )
    logger.info(f"LLM admin frontend mounted from: {llm_admin_path}")

# LLM 管理页面路由（向后兼容）
@app.get("/llm/admin")
async def llm_admin_page():
    try:
        return FileResponse(str(llm_admin_path / "index.html"))
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="LLM admin page not found! Please check if static/llm_admin_frontend/index.html exists."
        )

# 根路径重定向到 React 前端
@app.get("/")
async def root():
    return {"message": "PDE Solver API", "frontend": "/app", "docs": "/docs", "llm_admin": "/llm/admin"}

# ========== 原有启动逻辑（新增 LLM 页面提示） ==========


def run() -> None:
    """运行服务"""
    import uvicorn
    
    logger.info(f"Starting server on {cfg.server.host}:{cfg.server.port}")
    uvicorn.run(
        "main:app",
        host=cfg.server.host,
        port=cfg.server.port,
        reload=cfg.server.reload,
        log_level=cfg.logging.level.lower()
    )


if __name__ == "__main__":
    run()
