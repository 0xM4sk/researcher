from base import Agent
from tools import SearchTool, AnalyzeTool
from models import ResearchQuery, ResearchResult, TaskStatus, SearchProvider, SourceType
from task_queue import MessageQueue
from state import StateManager
import structlog
from opentelemetry import trace
from typing import Dict, Any, List
import asyncio

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)

class ResearchAgent(Agent):
    """Agent responsible for conducting research tasks."""
    
    def __init__(self):
        super().__init__()
        self.tools = {
            "search": SearchTool(),
            "analyze": AnalyzeTool()
        }
        # Initialize with default search provider
        self.policy = ResearchQuery(
            query="default",  # Non-empty required field
            sources=[SourceType.WEB],  # At least one source required
            search_params={"provider": SearchProvider.GOOGLE}  # Set default provider
        )
        self.logger = logger.bind(component="research_agent")
        self.queue = MessageQueue()
        self.state_manager = StateManager()

    async def execute(self, query: ResearchQuery) -> str:
        """Execute a research task and return task ID."""
        # Ensure search provider is set
        if not query.search_params:
            query.search_params = {"provider": SearchProvider.GOOGLE}
        elif not query.search_params.provider:
            query.search_params.provider = SearchProvider.GOOGLE
            
        task_id = await self.queue.enqueue_task(
            "research",
            {"query": query.dict()}
        )
        return task_id

    async def _execute_research(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Internal method to execute the research process."""
        query = ResearchQuery(**payload["query"])
        state = {"searched": False, "analyzed": False}
        results = []
        
        while action := self.policy.select_action(state):
            if action.name == "search":
                search_tasks = [
                    self.tools["search"].run(query.query, source)
                    for source in query.sources
                ]
                try:
                    search_results = await asyncio.gather(*search_tasks)
                    results.extend([item for sublist in search_results for item in sublist])
                except Exception as e:
                    self.logger.error("Search failed", error=str(e))
                    raise
                state["searched"] = True
                
            elif action.name == "analyze":
                analysis_tasks = [
                    self.tools["analyze"].run(result["content"])
                    for result in results
                ]
                analyses = await asyncio.gather(*analysis_tasks)
                
                analyzed_results = [
                    {
                        "source": results[i]["source"],
                        "content": analysis["text"],
                        "metadata": {**results[i]["metadata"], "analysis": analysis},
                        "relevance_score": analysis.get("relevance", 0.0)
                    }
                    for i, analysis in enumerate(analyses)
                ]
                
                results = sorted(
                    analyzed_results,
                    key=lambda x: x["relevance_score"],
                    reverse=True
                )[:query.max_results]
                state["analyzed"] = True
                
            elif action.name == "summarize":
                break
                
        return results

    async def get_research_status(self, task_id: str) -> TaskStatus:
        """Get the status of a research task."""
        return await self.state_manager.get_state(task_id)

    async def cleanup(self):
        """Cleanup agent resources."""
        await self.queue.cleanup()
        await self.state_manager.cleanup()
        for tool in self.tools.values():
            if hasattr(tool, 'cleanup'):
                await tool.cleanup()