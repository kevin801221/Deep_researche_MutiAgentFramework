"""
Arxiv Retriever for YCM Academic Researcher
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ArxivRetriever:
    """
    Arxiv API Retriever for academic papers
    """
    def __init__(self, query: str, sort: str = 'Relevance', query_domains: Optional[List[str]] = None):
        self.query = query
        self.sort = sort
        self.query_domains = query_domains or []
        
        # Import arxiv here to avoid import errors if the package is not installed
        try:
            import arxiv
            self.arxiv = arxiv
            self.sort_criterion = arxiv.SortCriterion.SubmittedDate if sort == 'SubmittedDate' else arxiv.SortCriterion.Relevance
            self.client = arxiv.Client()
            logger.info("Arxiv retriever initialized successfully")
        except ImportError:
            logger.error("Failed to import arxiv package. Please install it with 'pip install arxiv'")
            raise

    async def search(self, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Performs the search on Arxiv
        
        Args:
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, href, and body
        """
        try:
            # Run the search in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            arxiv_results = await loop.run_in_executor(
                None,
                self._search_sync,
                max_results
            )
            
            return arxiv_results
        except Exception as e:
            logger.error(f"Error searching Arxiv: {str(e)}")
            return []
    
    def _search_sync(self, max_results: int) -> List[Dict[str, Any]]:
        """
        Synchronous version of the search method
        
        Args:
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, href, and body
        """
        # Prepare query with domain filters if provided
        query = self.query
        if self.query_domains:
            domain_filters = " OR ".join([f"cat:{domain}" for domain in self.query_domains])
            query = f"({query}) AND ({domain_filters})"
        
        # Execute search
        search_query = self.arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=self.sort_criterion,
        )
        
        arxiv_gen = list(self.client.results(search_query))
        
        # Process results
        search_result = []
        for result in arxiv_gen:
            # Extract authors
            authors = ", ".join([author.name for author in result.authors])
            
            # Extract categories
            categories = ", ".join(result.categories)
            
            # Create result entry
            search_result.append({
                "title": result.title,
                "href": result.pdf_url,
                "body": result.summary,
                "authors": authors,
                "published": result.published.strftime("%Y-%m-%d") if result.published else "",
                "categories": categories,
                "entry_id": result.entry_id,
                "comment": result.comment or "",
                "journal_ref": result.journal_ref or "",
                "primary_category": result.primary_category,
                "source": "arxiv"
            })
        
        return search_result
