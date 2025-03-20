"""
YCM Academic Researcher - Main Entry Point
基於 YCM-Researcher 的學術知識蒐集工具
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Union, Dict, Any
import json

# 添加父目錄到 Python 路徑，以便導入 YCM-Researcher 模塊
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# 創建日誌目錄
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

# 抑制過於詳細的日誌
logging.getLogger('fontTools').setLevel(logging.WARNING)
logging.getLogger('fontTools.subset').setLevel(logging.WARNING)
logging.getLogger('fontTools.ttLib').setLevel(logging.WARNING)

# 創建日誌實例
logger = logging.getLogger(__name__)

# 加載環境變量
load_dotenv()

try:
    # 導入必要的庫
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from pydantic import BaseModel
    import uvicorn
    
    # 導入 YCM-Researcher 模塊
    from ycm_researcher.agent import YCMResearcher
    from ycm_researcher.config import Config
    from ycm_researcher.utils.enum import ReportType, ReportSource, Tone
    
    # 導入 RAG 集成模塊 (如果存在)
    try:
        from ycm_integration.rag_connector import RAGConnector
        rag_available = True
    except ImportError:
        logger.warning("RAG 連接器未找到，將禁用 RAG 功能")
        rag_available = False
    
    # WebSocket 管理器
    class WebSocketManager:
        def __init__(self):
            self.active_connections = []
        
        async def connect(self, websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
        
        def disconnect(self, websocket: WebSocket):
            self.active_connections.remove(websocket)
        
        async def broadcast(self, message: dict):
            for connection in self.active_connections:
                await connection.send_json(message)
    
    # 研究進度處理器
    class ResearchProgressHandler:
        def __init__(self, websocket_manager):
            self.websocket_manager = websocket_manager
        
        async def on_tool_start(self, tool_name, **kwargs):
            await self.websocket_manager.broadcast({
                "type": "research_update",
                "status": "in_progress",
                "message": f"使用工具: {tool_name}",
                "details": kwargs
            })
        
        async def on_agent_action(self, action, **kwargs):
            await self.websocket_manager.broadcast({
                "type": "research_update",
                "status": "in_progress",
                "message": f"執行動作: {action}",
                "details": kwargs
            })
        
        async def on_research_step(self, step, details):
            await self.websocket_manager.broadcast({
                "type": "research_update",
                "status": "in_progress",
                "message": f"研究步驟: {step}",
                "details": details
            })
        
        async def send_progress(self, message):
            await self.websocket_manager.broadcast({
                "type": "research_update",
                "status": "in_progress",
                "message": message
            })
    
    # 創建 WebSocket 管理器實例
    manager = WebSocketManager()
    progress_handler = ResearchProgressHandler(manager)
    
    # 創建 FastAPI 應用
    app = FastAPI(title="YCM Academic Researcher")
    
    # 靜態文件和模板
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    templates = Jinja2Templates(directory="frontend")
    
    # 常量
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")
    DOCS_DIR = os.getenv("DOCS_DIR", "./docs")
    
    # 啟動事件
    @app.on_event("startup")
    async def startup_event():
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")
        os.makedirs(DOCS_DIR, exist_ok=True)
        logger.info("YCM Academic Researcher 啟動完成")
    
    # 路由
    @app.get("/", response_class=HTMLResponse)
    async def read_root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})
    
    # 研究請求模型
    class ResearchRequest(BaseModel):
        query: str
        report_type: str = ReportType.ResearchReport.value
        agent: str = "researcher"
    
    # 格式化研究報告
    async def format_research_report(research_result: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        使用 OpenAI API 美化研究報告
        
        Args:
            research_result: 研究結果，可能是字典或字符串
        
        Returns:
            美化後的研究結果字典
        """
        try:
            # 檢查 research_result 是否為字典
            if not isinstance(research_result, dict):
                logger.warning(f"研究結果不是字典類型，而是 {type(research_result).__name__}，嘗試轉換")
                # 如果是字符串，嘗試解析為 JSON
                if isinstance(research_result, str):
                    try:
                        research_result = json.loads(research_result)
                    except json.JSONDecodeError:
                        # 如果無法解析為 JSON，則創建一個新的字典
                        research_result = {
                            "success": True,
                            "query": "unknown_query",
                            "summary": research_result,
                            "sources": []
                        }
                else:
                    # 如果不是字符串，則創建一個新的字典
                    research_result = {
                        "success": True,
                        "query": "unknown_query",
                        "summary": str(research_result),
                        "sources": []
                    }
            
            # 獲取摘要
            summary = research_result.get("summary", "")
            query = research_result.get("query", "unknown_query")
            sources = research_result.get("sources", [])
            
            # 構建提示詞
            prompt = f"""
            請將以下研究報告美化並格式化為專業的學術報告格式：
            
            查詢: {query}
            
            摘要:
            {summary}
            
            來源:
            {json.dumps(sources, ensure_ascii=False, indent=2)}
            
            請使用 Markdown 格式，確保報告結構清晰、內容專業、易於閱讀。
            """
            
            # 調用 OpenAI API
            from openai import OpenAI
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.warning("未設置 OpenAI API 密鑰，無法美化報告")
                return research_result
            client = OpenAI(api_key=openai_api_key)
            response = client.chat.completions.create(
                model="gpt-4",  # 使用適當的模型
                messages=[
                    {"role": "system", "content": "你是一位專業的學術研究助手，擅長整理和美化研究報告。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )
            
            # 獲取美化後的報告
            formatted_report = response.choices[0].message.content
            
            # 更新研究結果
            formatted_result = dict(research_result)
            formatted_result["formatted_report"] = formatted_report
            
            logger.info("研究報告美化成功")
            return formatted_result
            
        except Exception as e:
            logger.error(f"美化研究報告時出錯: {str(e)}")
            # 如果出錯，返回原始研究結果
            if isinstance(research_result, dict):
                return research_result
            else:
                return {
                    "success": True,
                    "query": "unknown_query",
                    "summary": str(research_result),
                    "sources": [],
                    "error": f"美化研究報告時出錯: {str(e)}"
                }
    
    # 研究路由
    @app.post("/api/research")
    async def conduct_research(request: ResearchRequest):
        try:
            logger.info(f"開始研究: {request.query}")
            
            # 通知前端研究已開始
            await manager.broadcast({
                "type": "research_update",
                "status": "in_progress",
                "message": f"開始研究: {request.query}"
            })
            
            # 創建 YCM-Researcher 實例
            researcher = YCMResearcher(
                query=request.query,
                report_type=request.report_type,
                report_source=ReportSource.Web.value,
                tone=Tone.Formal.value,  # 使用 Formal 代替 Academic
                config_path=None,  # 使用默認配置
                verbose=True,
                log_handler=progress_handler  # 添加進度處理器
            )
            
            # 執行研究
            result = await researcher.conduct_research()
            
            # 確保結果是字典類型
            if not isinstance(result, dict):
                logger.warning(f"研究結果不是字典類型，而是 {type(result).__name__}，嘗試轉換")
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        # 如果無法解析為 JSON，則創建一個新的字典
                        result = {
                            "success": True,
                            "query": request.query,
                            "summary": result,
                            "sources": []
                        }
                else:
                    # 如果不是字符串，則創建一個新的字典
                    result = {
                        "success": True,
                        "query": request.query,
                        "summary": str(result),
                        "sources": []
                    }
            
            # 通知前端研究已完成
            await manager.broadcast({
                "type": "research_complete",
                "message": "研究已完成",
                "data": result
            })
            
            # 美化研究報告
            formatted_result = await format_research_report(result)
            
            # 如果啟用了 RAG 並且 RAG 可用，將結果保存到向量數據庫
            rag_enabled = os.getenv("RAG_ENABLED", "true").lower() == "true"
            if rag_enabled and rag_available:
                try:
                    rag_connector = RAGConnector()
                    save_success = await rag_connector.save_research_to_vector_db(formatted_result)
                    if save_success:
                        await progress_handler.send_progress("研究結果已保存成功")
                    else:
                        await progress_handler.send_progress("保存研究結果失敗")
                except Exception as e:
                    logger.error(f"保存研究結果到向量數據庫時出錯: {str(e)}")
                    await progress_handler.send_progress(f"保存研究結果時出錯: {str(e)}")
            
            return formatted_result
        
        except Exception as e:
            logger.error(f"研究過程中出錯: {str(e)}")
            # 通知前端研究出錯
            await manager.broadcast({
                "type": "research_error",
                "message": f"研究過程中出錯: {str(e)}"
            })
            return {"success": False, "message": f"研究過程中出錯: {str(e)}"}
    
    # API 測試路由
    @app.get("/api/test")
    async def test_api():
        return {"message": "API 測試成功"}
    
    # WebSocket 端點
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_json()
                logger.info(f"收到 WebSocket 消息: {data}")
                await manager.broadcast(data)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
            logger.info("WebSocket 連接已關閉")
        except Exception as e:
            logger.error(f"WebSocket 處理時出錯: {str(e)}")
    
    # 主函數
    if __name__ == "__main__":
        logger.info("啟動 YCM Academic Researcher 服務器...")
        uvicorn.run(app, host="localhost", port=8080)
        
except ImportError as e:
    logger.error(f"導入錯誤: {e}")
    print(f"導入錯誤: {e}")
    print("請確保已安裝所有必要的依賴項: pip install fastapi uvicorn")
    sys.exit(1)
except Exception as e:
    logger.error(f"啟動服務器時出錯: {e}")
    print(f"啟動服務器時出錯: {e}")
    sys.exit(1)
