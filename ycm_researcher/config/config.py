"""
Configuration for YCM Academic Researcher
"""
import os
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration for YCM Academic Researcher"""
    
    def __init__(self, config_path: Optional[str] = None):
        # LLM Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.temperature = float(os.getenv("TEMPERATURE", "0.5"))
        
        # Vector Database Configuration
        self.vector_db_type = os.getenv("VECTOR_DB_TYPE", "chroma")  # Options: chroma, pinecone, qdrant
        self.vector_db_url = os.getenv("VECTOR_DB_URL", "")
        self.vector_db_api_key = os.getenv("VECTOR_DB_API_KEY", "")
        self.vector_db_namespace = os.getenv("VECTOR_DB_NAMESPACE", "ycm_academic")
        
        # Embedding Configuration
        self.embedding_provider = os.getenv("EMBEDDING_PROVIDER", "openai")
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        self.embedding_kwargs = {}
        
        # Search Configuration
        self.search_providers = os.getenv("SEARCH_PROVIDERS", "arxiv,semantic_scholar,tavily").split(",")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY", "")
        self.max_search_results_per_provider = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
        
        # Output Configuration
        self.output_dir = os.getenv("OUTPUT_DIR", "./outputs")
        self.log_dir = os.getenv("LOG_DIR", "./logs")
        
        # RAG Configuration
        self.rag_enabled = os.getenv("RAG_ENABLED", "true").lower() == "true"
        self.rag_chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
        self.rag_chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))
        self.rag_top_k = int(os.getenv("RAG_TOP_K", "5"))
        
        # Custom YCM Configuration
        self.company_name = os.getenv("COMPANY_NAME", "YCM")
        self.company_description = os.getenv("COMPANY_DESCRIPTION", "YCM is a leading research company specializing in academic knowledge collection and analysis.")
        self.company_domain = os.getenv("COMPANY_DOMAIN", "")
        
        # Override with config file if provided
        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
    
    def _load_from_file(self, config_path: str) -> None:
        """Load configuration from a file"""
        with open(config_path, 'r', encoding='utf-8') as f:
            import json
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
