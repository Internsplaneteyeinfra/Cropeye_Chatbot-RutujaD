from langchain_google_genai import ChatGoogleGenerativeAI
from app.prompts.language_prompt import LANGUAGE_DETECTION_PROMPT
from app.config import GEMINI_MODEL, GOOGLE_API_KEY
from app.utils.json_utils import safe_json

llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0
)

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
        # very rare fallback – choose English as safe default
        language = "en"

    state["user_language"] = language.lower()
    return state
