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
    
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass

    return {}
