# app/graph/router.py

SOIL_ANALYSIS_INTENTS = {
    "soil_analysis",
    "fertilizer_advice"
}
SOIL_MOISTURE_INTENTS = {
     "soil_moisture", 
}

WEATHER_INTENTS = {
    "weather_forecast",
}


def router(state: dict) -> str:
    """
    Decide next agent based on intent only.
    Chatbot-first routing (no forced context).
    """

    intent = state.get("intent", "")

    if intent in SOIL_ANALYSIS_INTENTS:
        return "soil_analysis_agent"

    if intent in SOIL_MOISTURE_INTENTS:
        return "soil_moisture_agent"

    if intent in WEATHER_INTENTS:
        return "weather_agent"

    return "response_generator"


# Just reminder: later i'll create a combined soil_agent for soil moisture, soil analysis 