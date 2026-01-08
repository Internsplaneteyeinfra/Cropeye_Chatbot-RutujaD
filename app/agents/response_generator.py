from app.prompts.response_prompt import RESPONSE_PROMPT
from app.config import llm
import json


def response_generator(state: dict) -> dict:
    """
    Response Generator Agent
    Formats and translates responses to user's language
    """
    
    intent = state.get("intent", "")
    language = state.get("user_language", "en")
    user_message = state.get("user_message", "")
    analysis = state.get("analysis", {})
    context = state.get("context", {})
    
    # Format analysis data for prompt
    analysis_str = "No analysis data available"
    if analysis:
        try:
            # Convert analysis to readable string
            if isinstance(analysis, dict):
                analysis_str = json.dumps(analysis, indent=2, ensure_ascii=False)
            else:
                analysis_str = str(analysis)
        except Exception:
            analysis_str = str(analysis)
    
    # Format context for prompt
    context_str = "No context available"
    if context:
        try:
            context_str = json.dumps(context, indent=2, ensure_ascii=False)
        except Exception:
            context_str = str(context)
    
    prompt = RESPONSE_PROMPT.format(
        intent=intent,
        language=language,
        analysis=analysis_str,
        context=context_str,
        user_message=user_message
    )

    response = llm.invoke(prompt)

    state["final_response"] = response.content.strip()
    return state
