# app/graph/router.py

SOIL_ANALYSIS_INTENTS = {
    "soil_analysis"
}
SOIL_MOISTURE_INTENTS = {
     "soil_moisture", 
}
WEATHER_INTENTS = {
    "current_weather",
    "weather_forecast",
}
IRRIGATION_INTENTS = {
    "irrigation_advice",
    "irrigation_schedule",
}
MAP_INTENTS = {
     "growth_map",
     "soil_moisture_map",
     "water_uptake_map",
     "pest_map",
}
PEST_INTENTS = {
    "pest_risk",
}
FIELD_HEALTH_INTENTS = {
    "field_score",
    "crop_health_analysis",
}
FERTILIZER_INTENTS = {
    "fertilizer_schedule",
    "fertilizer_advice",
}
DASHBOARD_INTENTS = {
    "dashboard_summary",
    "crop_status_check",
    "yield_info",
    "sugar_content_check",
    "stress_check",
    "biomass_check",
    "indices_check" ,
    "recovery_rate_check"
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

    if intent in FIELD_HEALTH_INTENTS:
        return "field_health_agent"

    if intent in FERTILIZER_INTENTS:
        return "fertilizer_agent"

    if intent in DASHBOARD_INTENTS:
        return "dashboard_agent"

    return "unified_agent"


# Just reminder: later i'll create a combined soil_agent for soil moisture AND soil analysis 