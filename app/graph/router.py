# app/graph/router.py

SOIL_ANALYSIS_INTENTS = {
    "soil_analysis"
}
SOIL_MOISTURE_INTENTS = {
     "soil_moisture", 
}
WEATHER_INTENTS = {
    "weather_forecast",
}
IRRIGATION_INTENTS = {
    "irrigation_advice",
    "irrigation_schedule",
}
MAP_INTENTS = {
     "map_view",
}
PEST_INTENTS = {
    "pest_risk",
}
FERTILIZER_INTENTS = {
    "fertilizer_advice",
}
DASHBOARD_INTENTS = {
    "dashboard_summary",
    "crop_status_check",
    "yield_info",
    "sugar_content_check",
    "stress_check",
    "biomass_check"
}

def router(state: dict) -> str:
    """
    Decide next agent based on intent only.
    Chatbot-first routing (no forced context).
    """

    intent = state.get("intent", "")
    print("🧭 ROUTER intent =", intent)

    if intent in MAP_INTENTS:
        return "map_agent"
        
    if intent in SOIL_ANALYSIS_INTENTS:
        return "soil_analysis_agent"

    if intent in SOIL_MOISTURE_INTENTS:
        return "soil_moisture_agent"

    if intent in WEATHER_INTENTS:
        return "weather_agent"

    if intent in IRRIGATION_INTENTS:
        return "irrigation_agent"

    if intent in PEST_INTENTS:
        return "pest_agent"

    if intent in FERTILIZER_INTENTS:
        return "fertilizer_agent"

    if intent in DASHBOARD_INTENTS:
        return "dashboard_agent"

    return "response_generator"


# Just reminder: later i'll create a combined soil_agent for soil moisture AND soil analysis 