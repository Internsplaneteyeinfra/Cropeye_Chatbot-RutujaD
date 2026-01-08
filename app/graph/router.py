# app/graph/router.py

def router(state: dict) -> str:
    """
    Decide which agent to call next based on intent.
    Returns the NEXT NODE NAME.
    """

    intent = state.get("intent")

    # Route to farm context first (if not already set)
    if "context" not in state or not state.get("context") or not state["context"].get("plot_id"):
        return "farm_context_agent"

    # Route based on intent
    if intent == "weather_forecast":
        return "weather_agent"

    if intent == "soil_status" or intent == "soil_analysis":
        return "soil_analysis_agent"

    if intent == "irrigation_advice":
        return "irrigation_agent"

    if intent == "pest_risk":
        return "pest_agent"

    if intent == "yield_forecast":
        return "yield_agent"

    if intent == "fertilizer_advice":
        return "soil_analysis_agent"  # Uses same agent as soil analysis

    if intent == "crop_health_summary":
        return "crop_health_agent"

    # Default to response generator
    return "response_generator"
