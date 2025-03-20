"""
RAG Connector for YCM Academic Researcher
連接 YCM-Researcher 和 YCM 的 RAG 向量數據庫
"""
import os
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加載環境變量
load_dotenv()

# 導入快取管理器
from ycm_integration.cache_manager import CacheManager

class RAGConnector:
    """
    RAG 連接器，用於連接 YCM-Researcher 和 YCM 的 RAG 向量數據庫
    """
    
    def __init__(self):
        """初始化 RAG 連接器"""
        self.vector_db_type = os.getenv("VECTOR_DB_TYPE", "chroma")
        self.vector_db_url = os.getenv("VECTOR_DB_URL", "")
        self.vector_db_api_key = os.getenv("VECTOR_DB_API_KEY", "")
        self.vector_db_namespace = os.getenv("VECTOR_DB_NAMESPACE", "ycm_academic")
        self.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        
        # 初始化快取管理器
        self.cache_manager = CacheManager()
        
        # 初始化向量數據庫連接
        self._initialize_vector_db()
    
    def _initialize_vector_db(self):
        """初始化向量數據庫連接"""
        try:
            if self.vector_db_type == "chroma":
                self._initialize_chroma()
            elif self.vector_db_type == "pinecone":
                self._initialize_pinecone()
            elif self.vector_db_type == "qdrant":
                self._initialize_qdrant()
            else:
                logger.warning(f"不支持的向量數據庫類型: {self.vector_db_type}，使用內存向量存儲")
                self._initialize_memory_vector_store()
                
            logger.info(f"成功初始化向量數據庫: {self.vector_db_type}")
        except Exception as e:
            logger.error(f"初始化向量數據庫時出錯: {str(e)}")
            logger.info("使用內存向量存儲作為備用")
            self._initialize_memory_vector_store()
    
    def _initialize_chroma(self):
        """初始化 Chroma 向量數據庫"""
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_community.embeddings import OpenAIEmbeddings
            
            # 初始化嵌入模型
            embedding_function = OpenAIEmbeddings(
                model=self.embedding_model,
                openai_api_key=os.getenv("OPENAI_API_KEY", "")
            )
            
            # 初始化 Chroma 客戶端
            self.vector_store = Chroma(
                collection_name=self.vector_db_namespace,
                embedding_function=embedding_function,
                persist_directory="./chroma_db"
            )
            
            logger.info("成功初始化 Chroma 向量數據庫")
        except Exception as e:
            logger.error(f"初始化 Chroma 向量數據庫時出錯: {str(e)}")
            raise
    
    def _initialize_pinecone(self):
        """初始化 Pinecone 向量數據庫"""
        try:
            from langchain_community.vectorstores import Pinecone
            from langchain_community.embeddings import OpenAIEmbeddings
            import pinecone
            
            # 初始化 Pinecone
            pinecone.init(
                api_key=self.vector_db_api_key,
                environment=self.vector_db_url
            )
            
            # 初始化嵌入模型
            embedding_function = OpenAIEmbeddings(
                model=self.embedding_model,
                openai_api_key=os.getenv("OPENAI_API_KEY", "")
            )
            
            # 初始化 Pinecone 向量存儲
            self.vector_store = Pinecone.from_existing_index(
                index_name=self.vector_db_namespace,
                embedding=embedding_function
            )
            
            logger.info("成功初始化 Pinecone 向量數據庫")
        except Exception as e:
            logger.error(f"初始化 Pinecone 向量數據庫時出錯: {str(e)}")
            raise
    
    def _initialize_qdrant(self):
        """初始化 Qdrant 向量數據庫"""
        try:
            from langchain_community.vectorstores import Qdrant
            from langchain_community.embeddings import OpenAIEmbeddings
            
            # 初始化嵌入模型
            embedding_function = OpenAIEmbeddings(
                model=self.embedding_model,
                openai_api_key=os.getenv("OPENAI_API_KEY", "")
            )
            
            # 初始化 Qdrant 客戶端
            self.vector_store = Qdrant.from_existing_collection(
                collection_name=self.vector_db_namespace,
                embedding=embedding_function,
                url=self.vector_db_url,
                api_key=self.vector_db_api_key,
            )
            
            logger.info("成功初始化 Qdrant 向量數據庫")
        except Exception as e:
            logger.error(f"初始化 Qdrant 向量數據庫時出錯: {str(e)}")
            raise
    
    def _initialize_memory_vector_store(self):
        """初始化內存向量存儲作為備用"""
        try:
            from langchain_community.vectorstores import FAISS
            from langchain_community.embeddings import OpenAIEmbeddings
            
            # 初始化嵌入模型
            embedding_function = OpenAIEmbeddings(
                model=self.embedding_model,
                openai_api_key=os.getenv("OPENAI_API_KEY", "")
            )
            
            # 初始化內存向量存儲
            self.vector_store = FAISS(
                embedding_function=embedding_function,
                index_name=self.vector_db_namespace
            )
            
            logger.info("成功初始化內存向量存儲")
        except Exception as e:
            logger.error(f"初始化內存向量存儲時出錯: {str(e)}")
            self.vector_store = None
    
    async def save_research_to_vector_db(self, research_result: Dict[str, Any]) -> bool:
        """
        將研究結果保存到向量數據庫
        
        Args:
            research_result: 研究結果，包含查詢、來源和摘要
            
        Returns:
            保存是否成功
        """
        # 檢查 research_result 是否為字典
        if not isinstance(research_result, dict):
            logger.warning(f"研究結果不是字典類型，而是 {type(research_result).__name__}")
            # 如果不是字典，嘗試將其轉換為字典
            try:
                if isinstance(research_result, str):
                    import json
                    research_result = json.loads(research_result)
                    if not isinstance(research_result, dict):
                        raise ValueError("轉換後的結果不是字典")
                else:
                    raise TypeError(f"無法處理 {type(research_result).__name__} 類型的研究結果")
            except Exception as e:
                logger.error(f"轉換研究結果為字典時出錯: {str(e)}")
                # 如果轉換失敗，創建一個基本的字典
                research_result = {
                    "summary": str(research_result),
                    "query": "unknown_query",
                    "sources": []
                }
        
        # 創建一個副本，避免修改原始對象
        result_copy = dict(research_result)
        
        # 首先嘗試保存到快取
        cache_path = await self.cache_manager.save_research_result(result_copy)
        
        # 如果向量數據庫未初始化，則只保存到快取
        if not self.vector_store:
            logger.warning("向量數據庫未初始化，研究結果已保存到快取")
            return True
        
        try:
            # 從研究結果中提取數據
            query = result_copy.get("query", "unknown_query")
            sources = result_copy.get("sources", [])
            
            # 優先使用格式化的報告作為摘要
            summary = result_copy.get("formatted_report", "")
            if not summary:
                summary = result_copy.get("summary", "")
            
            # 準備文檔
            from langchain_community.docstore.document import Document
            
            documents = []
            
            # 添加摘要文檔
            if summary:
                documents.append(
                    Document(
                        page_content=summary,
                        metadata={
                            "type": "summary",
                            "query": query,
                            "source": "ycm_academic_researcher"
                        }
                    )
                )
            
            # 添加來源文檔
            if isinstance(sources, list):
                for source in sources:
                    if isinstance(source, dict):
                        # 獲取內容，可能在 "content" 或 "raw_content" 中
                        content = source.get("content", source.get("raw_content", ""))
                        if not content and "title" in source:
                            # 如果沒有內容但有標題，使用標題作為內容
                            content = source["title"]
                        
                        if content:
                            documents.append(
                                Document(
                                    page_content=content,
                                    metadata={
                                        "type": "source",
                                        "query": query,
                                        "title": source.get("title", ""),
                                        "url": source.get("url", ""),
                                        "source": source.get("source", "unknown")
                                    }
                                )
                            )
            
            # 保存文檔到向量數據庫
            if documents:
                self.vector_store.add_documents(documents)
                logger.info(f"成功將 {len(documents)} 個文檔保存到向量數據庫")
                return True
            else:
                logger.warning("沒有文檔可保存到向量數據庫")
                return False
            
        except Exception as e:
            logger.error(f"保存研究結果到向量數據庫時出錯: {str(e)}")
            return True  # 返回 True 因為我們已經保存到了快取
    
    async def query_vector_db(self, query: str, top_k: int = 5, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        查詢向量數據庫
        
        Args:
            query: 查詢字符串
            top_k: 返回的結果數量
            filter_dict: 過濾條件
            
        Returns:
            查詢結果列表
        """
        results = []
        
        # 如果向量數據庫未初始化，則從快取中檢索
        if not self.vector_store:
            logger.warning("向量數據庫未初始化，從快取中檢索研究結果")
            cache_results = await self.cache_manager.get_research_result(query=query, limit=top_k)
            
            # 格式化快取結果
            for result in cache_results:
                results.append({
                    "content": result.get("summary", ""),
                    "metadata": {
                        "type": "cached_research",
                        "query": result.get("query", ""),
                        "timestamp": result.get("_cache_metadata", {}).get("timestamp", ""),
                        "source": "cache"
                    }
                })
            
            logger.info(f"從快取中檢索到 {len(results)} 個結果")
            return results
        
        try:
            # 執行相似度搜索
            vector_results = self.vector_store.similarity_search(
                query=query,
                k=top_k,
                filter=filter_dict
            )
            
            # 格式化結果
            for doc in vector_results:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            
            logger.info(f"成功從向量數據庫查詢到 {len(results)} 個結果")
            
            # 如果向量數據庫結果不足，則從快取中補充
            if len(results) < top_k:
                remaining = top_k - len(results)
                logger.info(f"向量數據庫結果不足，從快取中補充 {remaining} 個結果")
                
                cache_results = await self.cache_manager.get_research_result(query=query, limit=remaining)
                
                # 格式化快取結果
                for result in cache_results:
                    results.append({
                        "content": result.get("summary", ""),
                        "metadata": {
                            "type": "cached_research",
                            "query": result.get("query", ""),
                            "timestamp": result.get("_cache_metadata", {}).get("timestamp", ""),
                            "source": "cache"
                        }
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"查詢向量數據庫時出錯: {str(e)}")
            
            # 從快取中檢索
            logger.info("嘗試從快取中檢索研究結果")
            cache_results = await self.cache_manager.get_research_result(query=query, limit=top_k)
            
            # 格式化快取結果
            for result in cache_results:
                results.append({
                    "content": result.get("summary", ""),
                    "metadata": {
                        "type": "cached_research",
                        "query": result.get("query", ""),
                        "timestamp": result.get("_cache_metadata", {}).get("timestamp", ""),
                        "source": "cache"
                    }
                })
            
            logger.info(f"從快取中檢索到 {len(results)} 個結果")
            return results
