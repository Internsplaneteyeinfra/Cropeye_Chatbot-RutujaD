def filter_analysis_by_intent(intent: str, analysis: dict):
    """
    Return only analysis data relevant to the detected intent.
    This prevents sending unnecessary data to the LLM.
    """

    if not analysis or not isinstance(analysis, dict):
        return {}

    intent_map = {

        "soil_analysis": [
            "soil_analysis",
            "npk_requirements"
        ],

        "pest_risk": [
            "pest_detection",
            "pest_map"
        ],

        "weather_forecast": [
            "current_weather",
            "weather_forecast"
        ],

        "soil_moisture": [
            "soil_moisture_timeseries",
            "soil_moisture_map"
        ],

        "irrigation_advice": [
            "soil_moisture_timeseries",
            "et"
        ],

        "irrigation_schedule": [
            "soil_moisture_timeseries",
            "et",
            "weather_forecast"
        ],

        "fertilizer_advice": [
            "soil_analysis",
            "npk_requirements"
        ],

        "map_view": [
            "growth_map",
            "soil_moisture_map",
            "water_uptake_map",
            "pest_map"
        ],

        "dashboard_summary": [
            "agro",
            "harvest",
            "stress",
            "indices"
        ]
    }

    keys = intent_map.get(intent, [])

    filtered = {}

    for key in keys:
        if key in analysis:
            filtered[key] = analysis[key]

    return filtered