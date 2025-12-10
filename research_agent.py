"""
Research Agent - Specialized in information gathering and web search
"""
import logging
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

from base_agent import ToolUsingAgent, AgentState
from config import settings

logger = logging.getLogger(__name__)


class ResearchAgent(ToolUsingAgent):
    """Agent specialized in research and information gathering"""
    
    def __init__(self):
        super().__init__("research")
        
        # Register tools
        self.register_tool("web_search", self._web_search)
        self.register_tool("web_scrape", self._web_scrape)
        self.register_tool("extract_facts", self._extract_facts)
    
    def execute(self, task: str, state: AgentState) -> Dict[str, Any]:
        """
        Execute research task
        
        Args:
            task: Research task description
            state: Shared agent state
        
        Returns:
            Research results with sources
        """
        try:
            logger.info(f"{self.name}: Starting research task")
            
            # Think about the research approach
            approach = self.think(
                f"Plan research approach for: {task}",
                context=state.context
            )
            
            # Perform web search
            search_query = self._extract_search_query(task)
            search_results = self._web_search(search_query)
            
            # Extract and synthesize information
            synthesized = self._synthesize_information(
                task=task,
                search_results=search_results,
                context=state.context
            )
            
            # Store in state
            state.update_context({
                "research_results": synthesized,
                "sources": search_results.get("sources", [])
            })
            
            return self.format_result(
                output=synthesized,
                success=True,
                metadata={
                    "approach": approach,
                    "sources_count": len(search_results.get("sources", [])),
                    "query": search_query
                }
            )
            
        except Exception as e:
            logger.error(f"{self.name}: Execution failed: {e}")
            return self.format_result(
                output=None,
                success=False,
                error=str(e)
            )
    
    def _extract_search_query(self, task: str) -> str:
        """Extract optimal search query from task"""
        prompt = f"""Extract the best search query for this task: {task}

Respond with ONLY the search query, no explanation."""
        
        messages = self._build_messages(prompt)
        query = self._call_llm(messages, temperature=0.3, max_tokens=100)
        
        return query.strip().strip('"\'')
    
    def _web_search(
        self,
        query: str,
        num_results: int = 5
    ) -> Dict[str, Any]:
        """
        Perform web search
        
        Args:
            query: Search query
            num_results: Number of results to return
        
        Returns:
            Search results with URLs and snippets
        """
        logger.info(f"{self.name}: Searching for '{query}'")
        
        # Try SerpAPI if key available
        if settings.serpapi_api_key:
            return self._serpapi_search(query, num_results)
        
        # Fallback to DuckDuckGo (free)
        return self._duckduckgo_search(query, num_results)
    
    def _serpapi_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using SerpAPI (Google)"""
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": settings.serpapi_api_key,
                "num": num_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for result in data.get("organic_results", [])[:num_results]:
                results.append({
                    "title": result.get("title"),
                    "url": result.get("link"),
                    "snippet": result.get("snippet"),
                    "source": "Google"
                })
            
            return {
                "query": query,
                "sources": results,
                "search_engine": "Google (SerpAPI)"
            }
            
        except Exception as e:
            logger.error(f"{self.name}: SerpAPI search failed: {e}")
            return self._duckduckgo_search(query, num_results)
    
    def _duckduckgo_search(self, query: str, num_results: int) -> Dict[str, Any]:
        """Search using DuckDuckGo (free alternative)"""
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                for result in ddgs.text(query, max_results=num_results):
                    results.append({
                        "title": result.get("title"),
                        "url": result.get("href"),
                        "snippet": result.get("body"),
                        "source": "DuckDuckGo"
                    })
            
            return {
                "query": query,
                "sources": results,
                "search_engine": "DuckDuckGo"
            }
            
        except Exception as e:
            logger.error(f"{self.name}: DuckDuckGo search failed: {e}")
            # Return minimal result
            return {
                "query": query,
                "sources": [],
                "search_engine": "None",
                "error": str(e)
            }
    
    def _web_scrape(self, url: str) -> str:
        """
        Scrape content from URL
        
        Args:
            url: URL to scrape
        
        Returns:
            Scraped text content
        """
        try:
            logger.info(f"{self.name}: Scraping {url}")
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Limit length
            return text[:5000]
            
        except Exception as e:
            logger.error(f"{self.name}: Web scraping failed: {e}")
            return f"Error scraping {url}: {str(e)}"
    
    def _extract_facts(self, text: str) -> List[str]:
        """Extract key facts from text"""
        prompt = f"""Extract 5-10 key facts from this text:

{text[:2000]}

List each fact as a bullet point."""
        
        messages = self._build_messages(prompt)
        response = self._call_llm(messages, temperature=0.3)
        
        # Parse bullet points
        facts = [
            line.strip().lstrip('-*•').strip()
            for line in response.split('\n')
            if line.strip() and any(c in line for c in ['-', '*', '•'])
        ]
        
        return facts
    
    def _synthesize_information(
        self,
        task: str,
        search_results: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """
        Synthesize information from search results
        
        Args:
            task: Original research task
            search_results: Search results
            context: Additional context
        
        Returns:
            Synthesized research output
        """
        # Prepare sources text
        sources_text = ""
        for i, source in enumerate(search_results.get("sources", []), 1):
            sources_text += f"\nSource {i}:\n"
            sources_text += f"Title: {source.get('title')}\n"
            sources_text += f"Content: {source.get('snippet')}\n"
            sources_text += f"URL: {source.get('url')}\n"
        
        if not sources_text:
            sources_text = "No sources found."
        
        # Synthesize
        synthesis_prompt = f"""Based on the following sources, provide a comprehensive answer to the research task.

Research Task: {task}

Sources:
{sources_text}

Provide a well-structured response with:
1. Summary of findings
2. Key points with source citations
3. Additional context if needed

Always cite sources using [Source N] format."""
        
        messages = self._build_messages(
            synthesis_prompt,
            context=context
        )
        
        synthesized = self._call_llm(messages, max_tokens=1500)
        
        return synthesized