#state.py
from typing import TypedDict, Optional, Dict, Any, List

class GraphState(TypedDict):
    user_message: str
    user_language: Optional[str]
    intent: Optional[str]
    entities: Dict[str, Any]
    context: Optional[Dict[str, Any]]  # Farm context (plot, crop, etc.)
    analysis: Optional[Dict[str, Any]]  # Agent analysis results
    user_id: Optional[int]  # User ID from auth
    auth_token: Optional[str]  # Auth token for API calls
    final_response: Optional[str]
