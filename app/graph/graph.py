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
    report_node,
    feedback_node,
    reflection_node,
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
    
    # Reflection node
    graph.add_node("reflection", lambda state: reflection_node(state, llm))

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

    # High-score path: enhance -> reflection
    graph.add_edge("enhance", "reflection")
    
    # Conditional routing after reflection
    graph.add_conditional_edges(
        "reflection",
        route_after_reflection,
        {
            "format": "format",
            "enhance": "enhance"
        }
    )

    graph.add_edge("format", "report")
    graph.add_edge("report", END)

    # Low-score path: feedback -> END
    graph.add_edge("feedback", END)


    return graph.compile()


def route_after_reflection(state: ResumeEnhancerState) -> str:
    """
    Determine next step after reflection:
    - If valid/sufficient or max iterations reached -> format (proceed)
    - Else -> enhance (loop back)
    """
    # Safe access helper for dict or object state
    def get_attr(obj, key, default=None):
        return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

    is_sufficient = get_attr(state, "reflection_is_sufficient", False)
    iteration = get_attr(state, "reflection_iteration", 0)
    
    # Allow 1 retry (iteration 0 -> retry -> iteration 1 -> stop)
    # Actually if iter=1 (first pass), we want to retry -> iter 2.
    MAX_ITERATIONS = 2 
    
    if is_sufficient or iteration >= MAX_ITERATIONS:
            return "format"
            
    return "enhance"



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

