from abc import ABC, abstractmethod
import httpx
from redis.asyncio import Redis
from typing import List, Dict, Optional, Any
import functools
import asyncio
import json
from config import settings
from models import SourceType
import structlog

logger = structlog.get_logger()

class SearchProvider(ABC):
    """Abstract base class for search providers."""
    @abstractmethod
    async def search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        pass

class GoogleSearch(SearchProvider):
    """Google Custom Search implementation."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
    async def search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.base_url,
                params={
                    "key": self.api_key,
                    "q": query,
                    "num": max_results
                }
            )
            response.raise_for_status()
            return response.json()["items"]

class DuckDuckGoSearch(SearchProvider):
    """DuckDuckGo search implementation."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    async def search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        # Implement DuckDuckGo search logic
        pass

class SerperSearch(SearchProvider):
    """Serper.dev search implementation."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.serper.dev/search"
        
    async def search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={"X-API-KEY": self.api_key},
                json={"q": query, "num": max_results}
            )
            response.raise_for_status()
            return response.json()["organic"]

class SearchTool:
    def __init__(self):
        self._semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)
        self.providers: Dict[str, SearchProvider] = {}
        self.redis = Redis.from_url(settings.search_engines.redis_url, decode_responses=True)
        
        # Before performing operations, you might want to check/clear the key
        def clear_key(key: str) -> None:
            if self.redis.exists(key):
                self.redis.delete(key)
                
    @functools.lru_cache(maxsize=100)
    async def run(self, query: str, source: SourceType) -> List[Dict[str, Any]]:
        cache_key = f"search:{query}"
        
        # Try to get from cache first
        cached_result = self.redis.get(cache_key)
        if cached_result:
            return json.loads(cached_result)
            
        async with self._semaphore:
            results = []
            for provider in self.providers.values():
                try:
                    provider_results = await provider.search(query, max_results=5)
                    results.extend(provider_results)
                except Exception as e:
                    logger.error(f"Search provider error: {e}")
            
            final_results = results[:5]
            # Cache the results
            self.redis.setex(
                cache_key,
                3600,  # expire in 1 hour
                json.dumps(final_results)
            )
            
            return final_results
            
class AnalyzeTool:
    """Tool for analyzing search results and extracting relevant information."""
    
    async def run(self, content: str) -> Dict[str, Any]:
        """Analyze content and return structured results."""
        try:
            # Extract key information and calculate relevance score
            analysis = {
                "text": content[:500],  # Truncate long content
                "relevance": self._calculate_relevance(content),
                "summary": self._extract_summary(content)
            }
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {
                "text": content,
                "relevance": 0.0,
                "summary": None
            }
            
    def _calculate_relevance(self, content: str) -> float:
        """Calculate relevance score between 0 and 1."""
        # Basic implementation - could be enhanced with ML/NLP
        if not content:
            return 0.0
        # Simple scoring based on content length
        return min(len(content) / 1000, 1.0)
        
    def _extract_summary(self, content: str) -> str:
        """Extract a brief summary of the content."""
        # Basic implementation - first few sentences
        sentences = content.split('.')
        return '. '.join(sentences[:3]) + '.'
