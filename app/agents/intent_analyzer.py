#intent_analyzer.py
from app.prompts.intent_prompt import INTENT_PROMPT
from app.utils.json_utils import safe_json
from app.prompts.base_system_prompt import BASE_SYSTEM_PROMPT
from app.config import llm

def intent_analyzer(state: dict) -> dict:
    try:
        prompt = (BASE_SYSTEM_PROMPT + INTENT_PROMPT).format(
            user_message=state.get("user_message", "")
        )

        response = llm.invoke(prompt)
        
        # Handle different response formats
        content = ""
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'text'):
            content = response.text
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)
            
        print("RAW LLM RESPONSE:", content)

        result = safe_json(content)
        
        intent = result.get("intent")
        entities = result.get("entities")

        # HARD GUARANTEE: intent must exist
        if not intent or not isinstance(intent, str):
            intent = "general_explanation"

        if not isinstance(entities, dict):
            entities = {}

        state["intent"] = intent
        state["entities"] = entities
        
    except Exception as e:
        print(f"INTENT_ANALYZER_ERROR: {str(e)}")
        state["intent"] = "general_explanation"
        state["entities"] = {}

    return state