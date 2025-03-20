"""
Semantic Scholar Retriever for YCM Academic Researcher
"""
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SemanticScholarRetriever:
    """
    Semantic Scholar API Retriever for academic papers
    """
    def __init__(self, query: str, api_key: Optional[str] = None):
        self.query = query
        self.api_key = api_key
        self.base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.headers = {}
        
        if api_key:
            self.headers["x-api-key"] = api_key
    
    async def search(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Performs the search on Semantic Scholar
        
        Args:
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, href, and body
        """
        try:
            # Prepare query parameters
            params = {
                "query": self.query,
                "limit": max_results,
                "fields": "title,url,abstract,authors,venue,year,citationCount,influentialCitationCount,openAccessPdf"
            }
            
            # Execute search
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, headers=self.headers) as response:
                    if response.status != 200:
                        logger.error(f"Error searching Semantic Scholar: {response.status} {await response.text()}")
                        return []
                    
                    data = await response.json()
                    
                    # Process results
                    search_result = []
                    for paper in data.get("data", []):
                        # Extract authors
                        authors = ", ".join([author.get("name", "") for author in paper.get("authors", [])])
                        
                        # Get PDF URL if available
                        pdf_url = paper.get("openAccessPdf", {}).get("url", "")
                        
                        # Create result entry
                        search_result.append({
                            "title": paper.get("title", ""),
                            "href": pdf_url if pdf_url else paper.get("url", ""),
                            "body": paper.get("abstract", ""),
                            "authors": authors,
                            "year": paper.get("year", ""),
                            "venue": paper.get("venue", ""),
                            "citation_count": paper.get("citationCount", 0),
                            "influential_citation_count": paper.get("influentialCitationCount", 0),
                            "paper_id": paper.get("paperId", ""),
                            "source": "semantic_scholar"
                        })
                    
                    return search_result
                    
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {str(e)}")
            return []
