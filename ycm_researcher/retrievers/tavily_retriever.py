"""
Tavily Retriever for YCM Academic Researcher
"""
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class TavilyRetriever:
    """
    Tavily API Retriever for web search
    """
    def __init__(self, query: str, api_key: Optional[str] = None):
        self.query = query
        self.api_key = api_key
        self.base_url = "https://api.tavily.com/search"
        
        if not api_key:
            logger.warning("Tavily API key not provided. Search will not work.")
    
    async def search(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Performs the search using Tavily API
        
        Args:
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, href, and body
        """
        if not self.api_key:
            logger.error("Tavily API key not provided")
            return []
        
        try:
            # Prepare request data
            data = {
                "api_key": self.api_key,
                "query": self.query,
                "search_depth": "advanced",
                "include_domains": [],
                "exclude_domains": [],
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
                "include_images": False
            }
            
            # Execute search
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=data) as response:
                    if response.status != 200:
                        logger.error(f"Error searching Tavily: {response.status} {await response.text()}")
                        return []
                    
                    data = await response.json()
                    
                    # Process results
                    search_result = []
                    for result in data.get("results", []):
                        search_result.append({
                            "title": result.get("title", ""),
                            "href": result.get("url", ""),
                            "body": result.get("content", ""),
                            "source": "tavily"
                        })
                    
                    # Add the answer if available
                    if "answer" in data and data["answer"]:
                        search_result.append({
                            "title": "Tavily Answer",
                            "href": "",
                            "body": data["answer"],
                            "source": "tavily_answer"
                        })
                    
                    return search_result
                    
        except Exception as e:
            logger.error(f"Error searching Tavily: {str(e)}")
            return []
