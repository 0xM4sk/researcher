import asyncio
import streamlit as st
import sys
from pathlib import Path
from engine import ResearchAgent
from models import ResearchQuery, SourceType, TaskStatus
from tracing import telemetry_context

async def main():
    async with telemetry_context() as logger:
        agent = ResearchAgent()
        
        try:
            # Start queue processor
            queue_processor = asyncio.create_task(
                agent.queue.process_queue({
                    "research": agent._execute_research
                })
            )
            
            st.title("Research Assistant")
            
            selected_sources = []
            for source in SourceType:
                if st.checkbox(source.value.capitalize(), value=True):
                    selected_sources.append(source)
            
            query = st.text_input("Enter your research query")
            max_results = st.slider("Maximum results", 1, 10, 5)
            
            if st.button("Research") and query and selected_sources:
                with st.spinner("Researching..."):
                    try:
                        research_query = ResearchQuery(
                            query=query,
                            sources=selected_sources,
                            max_results=max_results
                        )
                        
                        task_id = await agent.execute(research_query)
                        
                        # Poll for results
                        while True:
                            state = await agent.get_research_status(task_id)
                            if state.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                                break
                            await asyncio.sleep(1)
                        
                        if state.status == TaskStatus.COMPLETED:
                            results = state.data["result"]
                            for result in results:
                                with st.expander(f"Result from {result.source.value}"):
                                    st.markdown(result.content)
                                    st.json(result.metadata)
                                    st.metric("Relevance Score", f"{result.relevance_score:.2f}")
                        else:
                            st.error(f"Research failed: {state.error}")
                            
                    except Exception as e:
                        st.error(f"Research failed: {str(e)}")
                        logger.error("streamlit_error", error=str(e), exc_info=True)
        
        finally:
            # Cleanup
            await agent.cleanup()
            if 'queue_processor' in locals():
                queue_processor.cancel()
                try:
                    await queue_processor
                except asyncio.CancelledError:
                    pass

if __name__ == "__main__":
    asyncio.run(main())# Add parent directory to Python path to import local module