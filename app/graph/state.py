#state.py
from typing import TypedDict, Optional, Dict, Any, List
from langchain_core.messages import BaseMessage  


class GraphState(TypedDict):

    messages: List[BaseMessage]
    user_language: Optional[str]
    intent: Optional[str]
    entities: Dict[str, Any]
    context: Optional[Dict[str, Any]]  
    analysis: Optional[Dict[str, Any]]
    conversation_state: Optional[Dict[str, Any]]  
    user_id: Optional[int]  
    final_response: Optional[str]
