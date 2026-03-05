# app/utils/cache_filter.py

from app.graph.router import (
    SOIL_ANALYSIS_INTENTS,
    SOIL_MOISTURE_INTENTS,
    WEATHER_INTENTS,
    IRRIGATION_INTENTS,
    MAP_INTENTS,
    PEST_INTENTS,
    FERTILIZER_INTENTS,
    DASHBOARD_INTENTS
)


def filter_cache_by_intent(intent: str, cached_data: dict) -> dict:
    """
    Return only relevant cached data based on detected intent.
    This reduces prompt size and LLM token usage.
    """

    if not cached_data:
        return {}

    # Soil Analysis
    if intent in SOIL_ANALYSIS_INTENTS:
        return {
            "soil_analysis": cached_data.get("soil_analysis")
        }

    # Soil Moisture
    if intent in SOIL_MOISTURE_INTENTS:
        return {
            "soil_moisture": cached_data.get("soil_moisture")
        }

    # Weather
    if intent in WEATHER_INTENTS:
        return {
            "weather": cached_data.get("weather")
        }

    # Irrigation
    if intent in IRRIGATION_INTENTS:
        return {
            "irrigation": cached_data.get("irrigation"),
            "soil_moisture": cached_data.get("soil_moisture"),
            "weather": cached_data.get("weather")
        }

    # Pest
    if intent in PEST_INTENTS:
        return {
            "pest": cached_data.get("pest"),
            "weather": cached_data.get("weather")
        }

    # Fertilizer
    if intent in FERTILIZER_INTENTS:
        return {
            "fertilizer": cached_data.get("fertilizer"),
            "soil_analysis": cached_data.get("soil_analysis")
        }

    # Dashboard
    if intent in DASHBOARD_INTENTS:
        return {
            "dashboard": cached_data.get("dashboard")
        }

    # Map
    if intent in MAP_INTENTS:
        return {
            "map": cached_data.get("map")
        }

    # fallback
    return {}