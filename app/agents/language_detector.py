
from app.prompts.language_prompt import LANGUAGE_DETECTION_PROMPT
from app.config import llm
from app.utils.json_utils import safe_json


def language_detector(state: dict) -> dict:
    user_message = state.get("user_message", "")

    prompt = LANGUAGE_DETECTION_PROMPT.format(
        user_message=user_message
    )

    response = llm.invoke(prompt)

    result = safe_json(response.content)

    # HARD GUARANTEE: always set a language
    language = result.get("language")

    if not language or not isinstance(language, str):
        language = "en"

    state["user_language"] = language.lower()
    return state
