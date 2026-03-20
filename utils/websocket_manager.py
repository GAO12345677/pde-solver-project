"""WebSocket管理器

管理WebSocket连接和消息广播
"""
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import asyncio


logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.task_connections: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str) -> None:
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[task_id] = websocket
        if task_id not in self.task_connections:
            self.task_connections[task_id] = set()
        self.task_connections[task_id].add(task_id)
        logger.info(f"WebSocket连接已建立: task_id={task_id}")
    
    def disconnect(self, task_id: str) -> None:
        """断开WebSocket连接"""
        if task_id in self.active_connections:
            del self.active_connections[task_id]
        if task_id in self.task_connections:
            self.task_connections[task_id].discard(task_id)
            if not self.task_connections[task_id]:
                del self.task_connections[task_id]
        logger.info(f"WebSocket连接已断开: task_id={task_id}")
    
    async def send_personal_message(self, message: dict, task_id: str) -> None:
        """向特定任务发送消息"""
        if task_id in self.active_connections:
            websocket = self.active_connections[task_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败: task_id={task_id}, error={e}")
                self.disconnect(task_id)
    
    async def broadcast(self, message: dict) -> None:
        """向所有连接广播消息"""
        disconnected = []
        for task_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败: task_id={task_id}, error={e}")
                disconnected.append(task_id)
        
        for task_id in disconnected:
            self.disconnect(task_id)
    
    async def send_progress(self, task_id: str, progress: float, message: str, status: str = "running") -> None:
        """发送进度消息"""
        await self.send_personal_message({
            "type": "progress",
            "task_id": task_id,
            "progress": progress,
            "message": message,
            "status": status,
            "timestamp": asyncio.get_event_loop().time()
        }, task_id)
    
    async def send_complete(self, task_id: str, result: dict) -> None:
        """发送完成消息"""
        await self.send_personal_message({
            "type": "complete",
            "task_id": task_id,
            "result": result,
            "timestamp": asyncio.get_event_loop().time()
        }, task_id)
    
    async def send_error(self, task_id: str, error: str) -> None:
        """发送错误消息"""
        await self.send_personal_message({
            "type": "error",
            "task_id": task_id,
            "error": error,
            "timestamp": asyncio.get_event_loop().time()
        }, task_id)


# 全局连接管理器实例
manager = ConnectionManager()
