"""
快取管理器，用於在向量數據庫不可用時保存研究結果
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CacheManager:
    """快取管理器，用於在向量數據庫不可用時保存研究結果"""
    
    def __init__(self, cache_dir: str = None):
        """初始化快取管理器"""
        if cache_dir is None:
            # 默認快取目錄
            cache_dir = os.getenv("CACHE_DIR", "./cache")
        
        self.cache_dir = Path(cache_dir)
        self.research_cache_dir = self.cache_dir / "research"
        
        # 確保快取目錄存在
        self._ensure_dirs()
        
        logger.info(f"快取管理器初始化完成，快取目錄: {self.cache_dir}")
    
    def _ensure_dirs(self):
        """確保所有必要的目錄都存在"""
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.research_cache_dir.mkdir(exist_ok=True, parents=True)
    
    async def save_research_result(self, research_result: Dict[str, Any]) -> str:
        """
        保存研究結果到快取
        
        Args:
            research_result: 研究結果，包含查詢、來源和摘要
            
        Returns:
            快取文件的路徑
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
                            "content": research_result,
                            "query": "unknown_query",
                            "timestamp": datetime.now().isoformat()
                        }
                else:
                    # 如果不是字符串，則創建一個新的字典
                    research_result = {
                        "content": str(research_result),
                        "query": "unknown_query",
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 生成文件名
            query = research_result.get("query", "unknown_query")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = "".join(c if c.isalnum() else "_" for c in query[:50])
            filename = f"{safe_query}_{timestamp}.json"
            
            # 完整路徑
            file_path = self.research_cache_dir / filename
            
            # 創建一個新的字典，避免修改原始對象
            cache_data = dict(research_result)
            
            # 添加快取元數據
            cache_data["_cache_metadata"] = {
                "timestamp": datetime.now().isoformat(),
                "cached": True,
                "filename": filename
            }
            
            # 保存到文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"研究結果已保存到快取: {file_path}")
            return str(file_path)
        
        except Exception as e:
            logger.error(f"保存研究結果到快取時出錯: {str(e)}")
            return ""
    
    async def get_research_result(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        從快取中獲取研究結果
        
        Args:
            query: 可選的查詢字符串，用於過濾結果
            limit: 返回的最大結果數量
            
        Returns:
            研究結果列表
        """
        try:
            results = []
            
            # 列出所有快取文件
            cache_files = list(self.research_cache_dir.glob("*.json"))
            
            # 按修改時間排序（最新的在前）
            cache_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 限制數量
            cache_files = cache_files[:limit]
            
            for file_path in cache_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # 如果指定了查詢，則過濾結果
                    if query:
                        file_query = data.get("query", "").lower()
                        if query.lower() not in file_query:
                            continue
                    
                    results.append(data)
                except Exception as e:
                    logger.error(f"讀取快取文件 {file_path} 時出錯: {str(e)}")
            
            logger.info(f"從快取中獲取了 {len(results)} 個研究結果")
            return results
        
        except Exception as e:
            logger.error(f"從快取中獲取研究結果時出錯: {str(e)}")
            return []
    
    async def get_latest_research_result(self) -> Optional[Dict[str, Any]]:
        """
        獲取最新的研究結果
        
        Returns:
            最新的研究結果，如果沒有則返回 None
        """
        results = await self.get_research_result(limit=1)
        return results[0] if results else None
    
    async def clear_cache(self, days: int = None) -> int:
        """
        清理快取
        
        Args:
            days: 可選，刪除幾天前的快取，如果為 None 則刪除所有快取
            
        Returns:
            刪除的文件數量
        """
        try:
            count = 0
            
            # 列出所有快取文件
            cache_files = list(self.research_cache_dir.glob("*.json"))
            
            # 當前時間
            now = datetime.now().timestamp()
            
            for file_path in cache_files:
                try:
                    # 如果指定了天數，則只刪除指定天數前的文件
                    if days is not None:
                        file_time = file_path.stat().st_mtime
                        days_diff = (now - file_time) / (24 * 3600)
                        
                        if days_diff < days:
                            continue
                    
                    # 刪除文件
                    file_path.unlink()
                    count += 1
                except Exception as e:
                    logger.error(f"刪除快取文件 {file_path} 時出錯: {str(e)}")
            
            logger.info(f"清理了 {count} 個快取文件")
            return count
        
        except Exception as e:
            logger.error(f"清理快取時出錯: {str(e)}")
            return 0
