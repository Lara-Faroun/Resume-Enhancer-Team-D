import logging
import sys
import os
from unittest.mock import MagicMock

# Ensure app is in path
sys.path.append(os.path.join(os.getcwd(), "app"))

from app.graph.nodes.reflection import reflection_node
from app.graph.state import ResumeEnhancerState
from app.schemas.enhancement import FullEnhancementOutput
from app.schemas.job_description import JobDescription
from app.schemas.reflection import ReflectionOutput

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_reflection_node_logic():
    print("Testing reflection_node logic...")
    
    # Mock LLM
    mock_llm = MagicMock()
    
    # Scene 1: Needs Improvement
    mock_llm.with_structured_output.return_value.invoke.return_value = ReflectionOutput(
        is_sufficient=False,
        critique="Too generic.",
        score=5
    )
    
    state = {
        "full_enhancement_output": FullEnhancementOutput(),
        "job_description": JobDescription(
            job_title="Software Engineer",
            responsibilities=["Code"],
            requirements=["Python"],
            required_skills=["Python"],
            preferred_skills=["Java"]
        ),
        "reflection_iteration": 0
    }
    # Note: Using dict for state as LangGraph usually passes dict to nodes
    
    result = reflection_node(state, mock_llm)
    
    print(f"Result 1 (Iter 0 -> Needs Improvement): {result}")
    assert result["reflection_iteration"] == 1
    assert result["reflection_is_sufficient"] is False
    assert result["reflection_feedback"] == "Too generic."

    # Scene 2: Sufficient
    mock_llm.with_structured_output.return_value.invoke.return_value = ReflectionOutput(
        is_sufficient=True,
        critique="Looks good.",
        score=9
    )
    
    state["reflection_iteration"] = 1
    result = reflection_node(state, mock_llm)
    
    print(f"Result 2 (Iter 1 -> Sufficient): {result}")
    assert result["reflection_iteration"] == 2
    assert result["reflection_is_sufficient"] is True

    print("SUCCESS: reflection_node logic verified.")

if __name__ == "__main__":
    try:
        test_reflection_node_logic()
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()
