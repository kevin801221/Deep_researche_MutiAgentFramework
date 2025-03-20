"""
Vector Store Wrapper for YCM Academic Researcher
"""
from typing import List, Dict, Any, Optional
import logging

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class VectorStoreWrapper:
    """
    A Wrapper for Vector Store to handle YCM Academic Researcher Document Type
    Supports integration with various vector stores (Chroma, Pinecone, Qdrant, etc.)
    """
    def __init__(self, vector_store):
        self.vector_store = vector_store

    def load(self, documents: List[Dict[str, Any]], chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        """
        Load the documents into vector_store
        Translate to langchain doc type, split to chunks then load
        
        Args:
            documents: List of documents to load
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
        """
        langchain_documents = self._create_langchain_documents(documents)
        splitted_documents = self._split_documents(langchain_documents, chunk_size, chunk_overlap)
        self.vector_store.add_documents(splitted_documents)
        logger.info(f"Loaded {len(splitted_documents)} document chunks into vector store")
    
    def _create_langchain_documents(self, data: List[Dict[str, str]]) -> List[Document]:
        """
        Convert YCM Academic Researcher Document to Langchain Document
        
        Args:
            data: List of documents
            
        Returns:
            List of Langchain Documents
        """
        return [
            Document(
                page_content=item.get("raw_content", item.get("content", "")), 
                metadata={
                    "source": item.get("url", ""),
                    "title": item.get("title", ""),
                    "provider": item.get("source", "unknown")
                }
            ) 
            for item in data
        ]

    def _split_documents(
        self, 
        documents: List[Document], 
        chunk_size: int = 1000, 
        chunk_overlap: int = 200
    ) -> List[Document]:
        """
        Split documents into smaller chunks
        
        Args:
            documents: List of documents to split
            chunk_size: Size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of split documents
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return text_splitter.split_documents(documents)

    async def asimilarity_search(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Return query by vector store
        
        Args:
            query: Query string
            k: Number of results to return
            filter: Filter to apply to search
            
        Returns:
            List of documents
        """
        try:
            if hasattr(self.vector_store, "asimilarity_search"):
                results = await self.vector_store.asimilarity_search(query=query, k=k, filter=filter)
            else:
                # Fallback for vector stores that don't support async search
                results = self.vector_store.similarity_search(query=query, k=k, filter=filter)
            
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
    
    def similarity_search(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Synchronous version of similarity search
        
        Args:
            query: Query string
            k: Number of results to return
            filter: Filter to apply to search
            
        Returns:
            List of documents
        """
        try:
            results = self.vector_store.similarity_search(query=query, k=k, filter=filter)
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            return []
