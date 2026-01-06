#state.py
from typing import TypedDict, Optional, Dict, Any, List

class GraphState(TypedDict):
    user_message: str
    user_language: Optional[str]
    intent: Optional[str]
    entities: Dict[str, Any]
    analysis: Dict[str, Any]
    final_response: Optional[str]
