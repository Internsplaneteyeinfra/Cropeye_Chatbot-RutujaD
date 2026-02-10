#intent_analyzer.py
from app.prompts.intent_prompt import INTENT_PROMPT
from app.utils.json_utils import safe_json
from app.prompts.base_system_prompt import BASE_SYSTEM_PROMPT
from app.config import llm

def intent_analyzer(state: dict) -> dict:
    
    user_message = state.get("user_message", "")
    # Use short_memory from state (loaded in main from Redis)
    history = state.get("short_memory", []) or []

    # Build conversation context
    history_text = ""
    last_intent = None

    for h in history:
        history_text += f"{h['role']}: {h['message']}\n"
        if h.get("intent"):
            last_intent = h["intent"]

    prompt = ( BASE_SYSTEM_PROMPT +"Conversation history:\n" + history_text + "\n" + INTENT_PROMPT ).format(user_message=user_message)
    
    
    try:
        # prompt = (BASE_SYSTEM_PROMPT + INTENT_PROMPT).format(
        #     user_message=state.get("user_message", "")
        # )

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
        # if not intent or not isinstance(intent, str):
        #     intent = "general_explanation"

        # if not isinstance(entities, dict):
        #     entities = {}

        if not intent:
            intent = last_intent  # reuse previous intent

        state["intent"] = intent
        state["entities"] = entities if isinstance(entities, dict) else {}
        # short_memory stays as loaded from main; user/bot messages saved in main after graph

    except Exception as e:
        print(f"INTENT_ANALYZER_ERROR: {str(e)}")
        # state["intent"] = "general_explanation"
        state["intent"] = last_intent  # reuse previous intent
        state["entities"] = {}

    return state