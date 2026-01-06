
from app.prompts.response_prompt import RESPONSE_PROMPT
from app.config import llm

def response_generator(state: dict) -> dict:
    """
    Temporary response generator using LLM.
    This will be replaced later by real agents (weather, soil, etc).
    """

    prompt = RESPONSE_PROMPT.format(
        intent=state.get("intent", ""),
        language=state.get("user_language", "en"),
        user_message=state.get("user_message", "")
    )

    response = llm.invoke(prompt)

    state["final_response"] = response.content.strip()
    return state
