import logging
import sys
import os
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage

# Ensure app is in path
sys.path.append(os.path.join(os.getcwd(), "app"))

from app.graph.graph import build_graph
from app.graph.state import ResumeEnhancerState
from app.schemas.job_description import JobDescription
from app.schemas.resume import Resume, PersonalInfo
from app.schemas.enhancement import FullEnhancementOutput
from app.schemas.mapping_result import MappingResult

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_graph_reflection_flow():
    print("Testing graph reflection flow...")
    
    # Mock LLM
    mock_llm = MagicMock()
    
    # We need to mock the responses for the sequence of nodes:
    # 1. mapping_node -> returns mapping_result (score=80 to go to enhance path)
    # 2. enhance_node -> returns full_enhancement_output
    # 3. reflection_node (1st pass) -> returns is_sufficient=False
    # 4. enhance_node (2nd pass) -> returns full_enhancement_output
    # 5. reflection_node (2nd pass) -> returns is_sufficient=True
    # 6. format_node
    # 7. report_node
    
    # Since the nodes wrap the LLM calls and we can't easily script the exact sequence of "invoke" calls 
    # on a single mock without complex side_effects, we will mock the *structured_output* method.
    
    # THIS IS TRICKY because different nodes use different schemas.
    # A simple way is to use a side_effect function that checks the schema passed to with_structured_output
    
    # However, build_graph takes 'llm'. Nodes call llm.with_structured_output(Schema).invoke(...)
    
    # Let's try to verify just the ROUTING logic by unit testing route_after_reflection directly
    # instead of running the whole graph which requires heavy mocking.
    
    from app.graph.graph import route_after_reflection
    
    print("\n--- Testing route_after_reflection ---")
    
    # Case 1: Sufficient
    state_sufficient = {"reflection_is_sufficient": True, "reflection_iteration": 1}
    route = route_after_reflection(state_sufficient)
    print(f"State: Sufficient -> Route: {route}")
    assert route == "format"
    
    # Case 2: Not sufficient, low iteration
    state_repeat = {"reflection_is_sufficient": False, "reflection_iteration": 1}
    route = route_after_reflection(state_repeat)
    print(f"State: Not Sufficient, Iter 1 -> Route: {route}")
    assert route == "enhance"
    
    # Case 3: Not sufficient, max iteration (2)
    state_max = {"reflection_is_sufficient": False, "reflection_iteration": 2}
    route = route_after_reflection(state_max)
    print(f"State: Not Sufficient, Iter 2 (Max) -> Route: {route}")
    assert route == "format"

    print("SUCCESS: Graph routing logic verified.")

if __name__ == "__main__":
    test_graph_reflection_flow()
