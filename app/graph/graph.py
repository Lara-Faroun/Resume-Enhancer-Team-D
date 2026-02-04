"""
LangGraph workflow wiring for the resume enhancer.

This module builds a StateGraph with the following flow:

    START -> mapping -> (feedback | enhance) -> format -> report -> END

- mapping, enhance, feedback use the shared LLM (Gemini or OpenAI) created
  once in main.py and injected here when building the graph.
- format is pure Python; report uses the shared LLM to summarize changes.
"""
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from graph.gate import route_after_mapping
from graph.nodes import (
    mapping_node,
    enhance_node,
    format_node,
    report_node,
    feedback_node,
)
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
    graph.add_node("mapping", lambda state: mapping_node(state, llm))
    graph.add_node("enhance", lambda state: enhance_node(state, llm))
    graph.add_node("feedback", lambda state: feedback_node(state, llm))

    graph.add_node("format", format_node)
    graph.add_node("report", lambda state: report_node(state, llm))

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


def run_resume_enhancer(
    graph, resume: Resume, job_description: JobDescription
) -> Dict[str, Any]:
    """
    Entry helper for running the compiled graph.

    The API layer is responsible for parsing the raw inputs into Resume and
    JobDescription instances, then calling this function with the compiled
    graph stored on app.state.graph.
    """
    initial_state: Dict[str, Any] = {
        "resume": resume,
        "job_description": job_description,
    }
    return graph.invoke(initial_state)

