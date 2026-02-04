import logging
from typing import Any, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from graph.state import ResumeEnhancerState
from llm.prompts.reflection import REFLECTION_SYSTEM, build_reflection_prompt_user
from schemas.reflection import ReflectionOutput

logger = logging.getLogger(__name__)

def reflection_node(state: ResumeEnhancerState, llm: BaseChatModel) -> Dict[str, Any]:
    """
    Critique the enhanced resume.
    """
    logger.info("reflection_node: starting")
    
    # Extract inputs
    # If state is a dict (standard in LangGraph invocation), access keys; otherwise attributes
    full_enhancement_output = (
        state.full_enhancement_output 
        if not isinstance(state, dict) 
        else state.get("full_enhancement_output")
    )
    job_description = (
        state.job_description 
        if not isinstance(state, dict) 
        else state.get("job_description")
    )
    
    current_iteration = (
        state.reflection_iteration 
        if not isinstance(state, dict) 
        else state.get("reflection_iteration", 0)
    )

    if not full_enhancement_output:
        logger.error("reflection_node: full_enhancement_output missing")
        raise ValueError("reflection_node requires full_enhancement_output")

    # Serialize inputs for prompt
    enhanced_json = full_enhancement_output.model_dump_json(indent=2)
    # Assuming JD has a text field or similar. 
    # If job_description is a Pydantic model, dump it.
    jd_text = job_description.model_dump_json() if job_description else "No JD provided"

    structured_llm = llm.with_structured_output(ReflectionOutput)
    
    user_prompt = build_reflection_prompt_user(
        job_description=jd_text,
        enhanced_resume_json=enhanced_json
    )
    
    try:
        result = structured_llm.invoke(
            [
                SystemMessage(content=REFLECTION_SYSTEM),
                HumanMessage(content=user_prompt)
            ]
        )
    except Exception as e:
        logger.exception("reflection_node: LLM call failed: %s", e)
        raise

    logger.info(
        "reflection_node: done is_sufficient=%s score=%s iteration=%s", 
        result.is_sufficient, 
        result.score,
        current_iteration
    )

    return {
        "reflection_feedback": result.critique,
        "reflection_iteration": current_iteration + 1,
        "reflection_is_sufficient": result.is_sufficient
    }

