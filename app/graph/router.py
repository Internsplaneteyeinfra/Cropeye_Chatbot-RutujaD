# app/graph/router.py

def route(state):
    intent = state["intent"]

    if intent == "weather_forecast":
        return "weather_agent"

    if intent == "soil_moisture":
        return "soil_agent"

    if intent == "crop_health_summary":
        return "crop_health_agent"

    return "explanation_agent"
