"""
WebSocket Manager for YCM Academic Researcher
處理 WebSocket 連接和消息廣播
"""
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

# 配置日誌
logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    WebSocket 連接管理器
    """
    
    def __init__(self):
        """初始化 WebSocket 管理器"""
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """
        連接 WebSocket
        
        Args:
            websocket: WebSocket 連接
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"新的 WebSocket 連接，當前連接數: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """
        斷開 WebSocket 連接
        
        Args:
            websocket: WebSocket 連接
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket 連接斷開，當前連接數: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        向特定 WebSocket 發送消息
        
        Args:
            message: 要發送的消息
            websocket: 目標 WebSocket 連接
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"發送個人消息時出錯: {str(e)}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        向所有活躍的 WebSocket 連接廣播消息
        
        Args:
            message: 要廣播的消息
        """
        disconnected_websockets = []
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"廣播消息時出錯: {str(e)}")
                disconnected_websockets.append(websocket)
        
        # 移除斷開的連接
        for websocket in disconnected_websockets:
            self.disconnect(websocket)
    
    async def broadcast_research_update(self, status: str, message: str = None):
        """
        廣播研究更新
        
        Args:
            status: 研究狀態
            message: 可選的狀態消息
        """
        await self.broadcast({
            "type": "research_update",
            "status": status,
            "message": message
        })
    
    async def broadcast_research_complete(self, result: Dict[str, Any]):
        """
        廣播研究完成
        
        Args:
            result: 研究結果
        """
        await self.broadcast({
            "type": "research_complete",
            **result
        })
    
    async def broadcast_chat_message(self, sender: str, message: str):
        """
        廣播聊天消息
        
        Args:
            sender: 發送者
            message: 消息內容
        """
        await self.broadcast({
            "type": "chat_message",
            "sender": sender,
            "message": message
        })
