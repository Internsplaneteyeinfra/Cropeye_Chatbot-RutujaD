#state.py
from typing import TypedDict, Optional, Dict, Any, List

class GraphState(TypedDict):
    user_message: str
    user_language: Optional[str]
    intent: Optional[str]
    entities: Dict[str, Any]
    context: Optional[Dict[str, Any]]  
    analysis: Optional[Dict[str, Any]]  # Agent analysis results
    user_id: Optional[int]  
    auth_token: Optional[str]  
    final_response: Optional[str]
    short_memory: Optional[List[Dict[str, Any]]] 
