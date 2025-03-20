"""
YCM Academic Researcher Agent
"""
from typing import Any, List, Dict, Optional, Set
import json
import logging
import asyncio

from .config.config import Config
from .vector_store import VectorStoreWrapper

# Configure logging
logger = logging.getLogger(__name__)

class YCMResearcher:
    """
    YCM Academic Researcher Agent
    
    This agent is responsible for:
    1. Conducting academic research using multiple sources (Arxiv, Semantic Scholar, etc.)
    2. Integrating with YCM's RAG vector database
    3. Generating comprehensive research reports
    4. Providing an interactive chat interface for knowledge exploration
    """
    
    def __init__(
        self,
        query: str,
        report_type: str = "research_report",
        report_format: str = "markdown",
        source_urls: List[str] = None,
        query_domains: List[str] = None,
        vector_store = None,
        vector_store_filter = None,
        config_path: str = None,
        websocket = None,
        verbose: bool = True,
        context: List[str] = None,
        headers: Dict[str, str] = None,
        max_results: int = 10,
        log_handler = None,
    ):
        self.query = query
        self.report_type = report_type
        self.report_format = report_format
        self.source_urls = source_urls or []
        self.query_domains = query_domains or []
        self.cfg = Config(config_path)
        self.websocket = websocket
        self.verbose = verbose
        self.context = context or []
        self.headers = headers or {}
        self.max_results = max_results
        self.log_handler = log_handler
        
        # Research data
        self.research_sources = []  # The list of scraped sources
        self.research_costs = 0.0
        self.visited_urls = set()
        
        # Initialize vector store
        self.vector_store = vector_store
        self.vector_store_filter = vector_store_filter
        
        # Initialize retrievers
        self.retrievers = self._get_retrievers()
        
        # Initialize LLM provider
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM provider based on configuration"""
        try:
            from openai import OpenAI
            self.llm_client = OpenAI(api_key=self.cfg.openai_api_key)
            logger.info(f"Initialized OpenAI client with model: {self.cfg.openai_model}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM provider: {str(e)}")
            raise
    
    def _get_retrievers(self) -> Dict[str, Any]:
        """Get retrievers based on configuration"""
        retrievers = {}
        
        for provider in self.cfg.search_providers:
            try:
                if provider == "arxiv":
                    from .retrievers.arxiv_retriever import ArxivRetriever
                    retrievers["arxiv"] = ArxivRetriever(self.query)
                
                elif provider == "semantic_scholar":
                    from .retrievers.semantic_scholar_retriever import SemanticScholarRetriever
                    retrievers["semantic_scholar"] = SemanticScholarRetriever(self.query)
                
                elif provider == "tavily":
                    from .retrievers.tavily_retriever import TavilyRetriever
                    retrievers["tavily"] = TavilyRetriever(self.query, api_key=self.cfg.tavily_api_key)
                
                # Add more retrievers as needed
                
            except Exception as e:
                logger.error(f"Failed to initialize {provider} retriever: {str(e)}")
        
        return retrievers
    
    async def _log_event(self, event_type: str, **kwargs):
        """Helper method to handle logging events"""
        if self.log_handler:
            await self.log_handler(event_type, **kwargs)
        
        if self.websocket:
            await self.websocket.send_json({
                "type": event_type,
                **kwargs
            })
    
    async def _search_sources(self) -> List[Dict[str, Any]]:
        """Search for sources using configured retrievers"""
        all_results = []
        
        for name, retriever in self.retrievers.items():
            try:
                logger.info(f"Searching with {name}...")
                await self._log_event("status_update", message=f"Searching with {name}...")
                
                results = await retriever.search(max_results=self.cfg.max_search_results_per_provider)
                
                for result in results:
                    result["source"] = name
                    all_results.append(result)
                
                logger.info(f"Found {len(results)} results from {name}")
                await self._log_event("search_results", provider=name, count=len(results))
                
            except Exception as e:
                logger.error(f"Error searching with {name}: {str(e)}")
                await self._log_event("error", message=f"Error searching with {name}: {str(e)}")
        
        return all_results
    
    async def _process_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process search results to extract relevant information"""
        processed_results = []
        
        for result in results:
            try:
                # Skip already visited URLs
                if result.get("href") in self.visited_urls:
                    continue
                
                self.visited_urls.add(result.get("href", ""))
                
                # Extract content from the result
                content = result.get("body", "")
                title = result.get("title", "")
                url = result.get("href", "")
                source = result.get("source", "unknown")
                
                processed_results.append({
                    "title": title,
                    "url": url,
                    "content": content,
                    "source": source,
                    "raw_content": content
                })
                
            except Exception as e:
                logger.error(f"Error processing result: {str(e)}")
        
        return processed_results
    
    async def _generate_summary(self, sources: List[Dict[str, Any]]) -> str:
        """Generate a summary of the research using LLM"""
        try:
            # Prepare context for the LLM
            context = "\n\n".join([
                f"Title: {source['title']}\nSource: {source['source']}\nURL: {source['url']}\n\nContent: {source['content'][:1000]}..."
                for source in sources[:5]  # Limit to top 5 sources to avoid token limits
            ])
            
            # Generate summary using LLM
            prompt = f"""
            You are an academic researcher for {self.cfg.company_name}, a company that {self.cfg.company_description}
            
            Based on the following research sources, create a comprehensive summary about: "{self.query}"
            
            RESEARCH SOURCES:
            {context}
            
            Your summary should:
            1. Be comprehensive and academic in tone
            2. Cite the sources appropriately
            3. Highlight key findings and implications
            4. Be structured with clear sections
            5. Include areas for further research
            
            FORMAT YOUR RESPONSE IN {self.report_format.upper()}
            """
            
            response = self.llm_client.chat.completions.create(
                model=self.cfg.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert academic researcher specializing in creating comprehensive research summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.cfg.temperature
            )
            
            summary = response.choices[0].message.content
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    async def _save_to_vector_store(self, sources: List[Dict[str, Any]]):
        """Save research sources to vector store for future retrieval"""
        if not self.cfg.rag_enabled or not sources:
            return
        
        try:
            # Initialize vector store if not provided
            if not self.vector_store:
                # Implementation depends on the vector store type
                # This is a placeholder - actual implementation would depend on your RAG system
                logger.info("Vector store not provided, skipping saving to vector store")
                return
            
            # Save sources to vector store
            vector_store_wrapper = VectorStoreWrapper(self.vector_store)
            vector_store_wrapper.load(sources)
            
            logger.info(f"Saved {len(sources)} sources to vector store")
            await self._log_event("status_update", message=f"Saved {len(sources)} sources to vector store")
            
        except Exception as e:
            logger.error(f"Error saving to vector store: {str(e)}")
            await self._log_event("error", message=f"Error saving to vector store: {str(e)}")
    
    async def _save_report(self, report: str) -> str:
        """Save the research report to a file"""
        try:
            import os
            from datetime import datetime
            
            # Create output directory if it doesn't exist
            os.makedirs(self.cfg.output_dir, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_{timestamp}.{self.report_format}"
            filepath = os.path.join(self.cfg.output_dir, filename)
            
            # Save report to file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(report)
            
            logger.info(f"Saved report to {filepath}")
            await self._log_event("status_update", message=f"Saved report to {filepath}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            await self._log_event("error", message=f"Error saving report: {str(e)}")
            return ""
    
    async def research(self) -> Dict[str, Any]:
        """Conduct research and generate a report"""
        try:
            # Log start of research
            logger.info(f"Starting research on: {self.query}")
            await self._log_event("status_update", message=f"Starting research on: {self.query}")
            
            # Search for sources
            search_results = await self._search_sources()
            
            if not search_results:
                message = "No search results found. Please try a different query or search provider."
                logger.warning(message)
                await self._log_event("status_update", message=message)
                return {"success": False, "message": message}
            
            # Process search results
            sources = await self._process_search_results(search_results)
            self.research_sources = sources
            
            # Save to vector store for future retrieval
            await self._save_to_vector_store(sources)
            
            # Generate summary
            summary = await self._generate_summary(sources)
            
            # Save report
            report_path = await self._save_report(summary)
            
            # Return research results
            result = {
                "success": True,
                "query": self.query,
                "sources": [{"title": s["title"], "url": s["url"], "source": s["source"]} for s in sources],
                "summary": summary,
                "report_path": report_path
            }
            
            logger.info(f"Research completed successfully: {self.query}")
            await self._log_event("research_complete", result=result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error conducting research: {str(e)}")
            await self._log_event("error", message=f"Error conducting research: {str(e)}")
            return {"success": False, "message": f"Error conducting research: {str(e)}"}
    
    async def chat(self, message: str) -> str:
        """Chat with the researcher about the research or ask follow-up questions"""
        try:
            # Prepare context from research sources
            context = ""
            if self.research_sources:
                context = "\n\n".join([
                    f"Title: {source['title']}\nSource: {source['source']}\nURL: {source['url']}\n\nContent: {source['content'][:500]}..."
                    for source in self.research_sources[:3]  # Limit to top 3 sources
                ])
            
            # If RAG is enabled, retrieve relevant documents from vector store
            rag_context = ""
            if self.cfg.rag_enabled and self.vector_store:
                vector_store_wrapper = VectorStoreWrapper(self.vector_store)
                try:
                    results = await vector_store_wrapper.asimilarity_search(
                        query=message,
                        k=self.cfg.rag_top_k,
                        filter=self.vector_store_filter
                    )
                    
                    if results:
                        rag_context = "\n\n".join([
                            f"Content: {doc.page_content}\nSource: {doc.metadata.get('source', 'unknown')}"
                            for doc in results
                        ])
                except Exception as e:
                    logger.error(f"Error retrieving from vector store: {str(e)}")
            
            # Combine contexts
            combined_context = ""
            if context and rag_context:
                combined_context = f"RESEARCH SOURCES:\n{context}\n\nADDITIONAL RELEVANT INFORMATION:\n{rag_context}"
            elif context:
                combined_context = f"RESEARCH SOURCES:\n{context}"
            elif rag_context:
                combined_context = f"RELEVANT INFORMATION:\n{rag_context}"
            
            # Generate response using LLM
            prompt = f"""
            You are an academic research assistant for {self.cfg.company_name}, a company that {self.cfg.company_description}
            
            The user is asking: "{message}"
            
            {combined_context if combined_context else "You don't have specific research sources for this query yet."}
            
            Provide a helpful, accurate, and academic response based on the available information.
            If you don't know the answer or don't have enough information, suggest conducting more specific research.
            """
            
            response = self.llm_client.chat.completions.create(
                model=self.cfg.openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert academic researcher specializing in providing accurate and helpful information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.cfg.temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    async def conduct_research(self) -> Dict[str, Any]:
        """
        Conduct research and ensure the result is returned as a dictionary.
        This method is a wrapper around the research method to ensure compatibility
        with the main.py conduct_research function.
        """
        try:
            # Call the research method
            result = await self.research()
            
            # Ensure the result is a dictionary
            if isinstance(result, dict):
                return result
            elif isinstance(result, str):
                # If the result is a string, convert it to a dictionary
                logger.warning("Research result is a string, converting to dictionary")
                return {
                    "success": True,
                    "query": self.query,
                    "summary": result,
                    "sources": self.research_sources
                }
            else:
                # If the result is neither a dictionary nor a string, create a new dictionary
                logger.warning(f"Research result is of type {type(result).__name__}, converting to dictionary")
                return {
                    "success": True,
                    "query": self.query,
                    "summary": str(result),
                    "sources": self.research_sources
                }
        except Exception as e:
            logger.error(f"Error in conduct_research: {str(e)}")
            return {"success": False, "message": f"Error conducting research: {str(e)}"}
