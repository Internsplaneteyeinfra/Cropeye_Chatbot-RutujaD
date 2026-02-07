# response_generator.py
from app.config import llm
import json
from app.prompts.base_system_prompt import BASE_SYSTEM_PROMPT   #globle
from app.prompts.response_prompt import RESPONSE_PROMPT         #globle

from app.prompts.weather_prompt import WEATHER_AGENT_PROMPT
from app.prompts.soil_moisture_prompt import SOIL_MOISTURE_AGENT_PROMPT
from app.prompts.irrigation_prompt import IRRIGATION_AGENT_PROMPT
from app.prompts.map_prompt import MAP_AGENT_PROMPT


def _select_domain_prompt(intent: str) -> str:
    """
    Select domain-specific interpretation prompt based on intent.
    This controls WHAT the model should interpret.
    """

    if intent in {"weather_forecast"}:
        return WEATHER_AGENT_PROMPT

    if intent in {"soil_status", "soil_moisture_current", "soil_moisture_trend"}:
        return SOIL_MOISTURE_AGENT_PROMPT

    if intent in {"map_view"}:
        return MAP_AGENT_PROMPT

    if intent in {"irrigation_schedule", "irrigation_advice"}:
        return IRRIGATION_AGENT_PROMPT

    # if intent in {"soil_analysis", "fertilizer_advice"}:
    #     return SOIL_ANALYSIS_AGENT_PROMPT

 
    return ""

def response_generator(state: dict) -> dict:
    
    intent = state.get("intent", "")
    language = state.get("user_language", "en")
    user_message = state.get("user_message", "")
    analysis = state.get("analysis", {})
    context = state.get("context", {})
    
    
    analysis_str = "No analysis data available"
    if analysis:
        try:
            if isinstance(analysis, dict):
                analysis_str = json.dumps(analysis, indent=2, ensure_ascii=False)
            else:
                analysis_str = str(analysis)
        except Exception:
            analysis_str = str(analysis)
    

    context_str = "No context available"
    if context:
        try:
            context_str = json.dumps(context, indent=2, ensure_ascii=False)
        except Exception:
            context_str = str(context)
    
    domain_prompt = _select_domain_prompt(intent)

    prompt = (BASE_SYSTEM_PROMPT + domain_prompt + RESPONSE_PROMPT).format(
        intent=intent,
        language=language,
        analysis=analysis_str,
        context=context_str,
        user_message=user_message
    )

    response = llm.invoke(prompt)

    state["final_response"] = response.content.strip()
    return state
