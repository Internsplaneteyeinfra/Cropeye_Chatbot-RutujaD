# language_detector.py
from app.prompts.language_prompt import LANGUAGE_DETECTION_PROMPT
from app.config import llm
from app.utils.json_utils import safe_json


def language_detector(state: dict) -> dict:
    user_message = state.get("user_message", "")

    try:
        prompt = LANGUAGE_DETECTION_PROMPT.format(
            user_message=user_message
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

        result = safe_json(content)

        # HARD GUARANTEE: always set a language
        language = result.get("language")

        if not language or not isinstance(language, str):
            language = "en"

        state["user_language"] = language.lower()
    except Exception as e:
        print(f"LANGUAGE_DETECTOR_ERROR: {str(e)}")
        state["user_language"] = "en"
    
    return state
