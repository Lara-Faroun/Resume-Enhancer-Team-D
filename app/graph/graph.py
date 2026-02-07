"""
LangGraph workflow wiring for the resume enhancer.

This module builds a StateGraph with the following flow:

    START -> mapping -> (feedback | enhance) -> format -> report -> END

- mapping, enhance, feedback use the shared LLM (Gemini or OpenAI) created
  once in main.py and injected here when building the graph.
- format is pure Python; report uses the shared LLM to summarize changes.
"""
import logging
from typing import Any, Dict
import asyncio

from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)

from graph.gate import route_after_mapping
from graph.nodes import (
    mapping_node,
    enhance_node,
    format_node,
    report_node,
    feedback_node,
)
from graph.nodes.enhance_incremental import enhance_incremental_node
from graph.nodes.enhance_sectional import enhance_sectional_node
from graph.state import ResumeEnhancerState
from schemas.resume import Resume
from schemas.job_description import JobDescription


def build_graph(llm: Any):
    """
    Build and compile the LangGraph for the resume enhancer.

    The llm argument is a LangChain chat model (Gemini or OpenAI) created once
    in main.py and reused across nodes that require it.
    """
    graph = StateGraph(ResumeEnhancerState)

    # Nodes that require LLM are wrapped to accept only `state`.
    async def mapping_with_llm(state):
        return await mapping_node(state, llm)

    async def enhance_router(state):
        """Route to legacy, incremental, or sectional enhance based on state.mode."""
        mode = state.get("mode", "legacy") if isinstance(state, dict) else getattr(state, "mode", "legacy")
        if mode == "incremental":
            logger.info("enhance_router: using incremental mode")
            return enhance_incremental_node(state, llm)
        elif mode == "sectional":
            logger.info("enhance_router: using sectional mode")
            return enhance_sectional_node(state, llm)
        else:
            logger.info("enhance_router: using legacy mode")
            return await enhance_node(state, llm)

    async def feedback_with_llm(state):
        return await feedback_node(state, llm)

    async def report_with_llm(state):
        return await report_node(state, llm)

    graph.add_node("mapping", mapping_with_llm)
    graph.add_node("enhance", enhance_router)
    graph.add_node("feedback", feedback_with_llm)
    graph.add_node("format", format_node)
    graph.add_node("report", report_with_llm)

    # Entry point
    graph.set_entry_point("mapping")

    # Conditional routing after mapping
    # route_after_mapping(state) -> "feedback" or "enhance"
    graph.add_conditional_edges(
        "mapping",
        route_after_mapping,
        {
            "feedback": "feedback",
            "enhance": "enhance",
        },
    )

    # High-score path: enhance -> format -> report -> END
    graph.add_edge("enhance", "format")
    graph.add_edge("format", "report")
    graph.add_edge("report", END)

    # Low-score path: feedback -> END
    graph.add_edge("feedback", END)

    return graph.compile()


async def run_resume_enhancer_async(
    graph, resume: Resume, job_description: JobDescription
) -> Dict[str, Any]:
    """
    Async entry helper for running the compiled graph.

    The API layer is responsible for parsing the raw inputs into Resume and
    JobDescription instances, then calling this function with the compiled
    graph stored on app.state.graph.

    Initial state is a dict conforming to ResumeEnhancerState (resume and
    job_description set). LangGraph merges node outputs into this state;
    nodes receive the current state (as dict) and should normalize via
    normalize_state() for consistent attribute access.
    """
    initial_state: Dict[str, Any] = {
        "resume": resume,
        "job_description": job_description,
    }
    return await graph.ainvoke(initial_state)


def run_resume_enhancer(
    graph, resume: Resume, job_description: JobDescription
) -> Dict[str, Any]:
    """
    Sync helper retained for tests and backward compatibility.

    Internally runs the async graph entry point.
    """
    return asyncio.run(run_resume_enhancer_async(graph, resume, job_description))

