import json
import re

def safe_json(text: str) -> dict:
    """
    Safely parse JSON from LLM responses.
    Handles:
    - Pure JSON
    - JSON wrapped in markdown ```json
    - Extra text before/after JSON
    """
    # if not text or not isinstance(text, str):
    #     return {}

    # # First attempt: direct JSON
    # try:
    #     return json.loads(text)
    # except Exception:
    #     pass

    # # Second attempt: extract JSON block
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    return {}
