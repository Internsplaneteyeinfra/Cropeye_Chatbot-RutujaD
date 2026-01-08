"""
Farm Context Agent
Retrieves and manages farm context (plot, crop, plantation date, etc.)
"""

from typing import Dict, Any
from app.services.farm_context_service import get_farm_context


async def farm_context_agent(state: dict) -> dict:
    """
    Farm Context Agent
    Gets farmer's plot information and maintains context
    """
    # Extract entities and context
    entities = state.get("entities", {})
    plot_id = entities.get("plot_id")
    
    # Get user_id from state if available (from auth token)
    user_id = state.get("user_id")
    auth_token = state.get("auth_token")
    
    # Get farm context
    context = await get_farm_context(
        plot_name=plot_id,
        user_id=user_id,
        auth_token=auth_token
    )
    
    # Store context in state
    if "context" not in state:
        state["context"] = {}
    
    state["context"].update(context)
    
    return state
