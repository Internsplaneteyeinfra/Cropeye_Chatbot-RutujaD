#intent_analyzer.py
from app.prompts.intent_prompt import INTENT_PROMPT
from app.utils.json_utils import safe_json
from app.config import llm

def intent_analyzer(state: dict) -> dict:
    prompt = INTENT_PROMPT.format(
        user_message=state["user_message"]
    )

    response = llm.invoke(prompt)
    print("RAW OLLAMA RESPONSE:", response.content)

    result = safe_json(response.content)
    
    intent = result.get("intent")
    entities = result.get("entities")

    # HARD GUARANTEE: intent must exist
    if not intent or not isinstance(intent, str):
        intent = "general_explanation"

    if not isinstance(entities, dict):
        entities = {}

    state["intent"] = intent
    state["entities"] = entities

    return state