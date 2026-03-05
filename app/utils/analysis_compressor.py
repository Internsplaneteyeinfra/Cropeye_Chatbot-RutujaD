def compress_analysis(intent, analysis):

    if not analysis:
        return None

    # ---------------- PEST ----------------
    if intent == "pest_risk":

        high = [w["name"] for w in analysis.get("high_risk_weeds", [])]
        moderate = [w["name"] for w in analysis.get("moderate_risk_weeds", [])]

        return {
            "high_risk_weeds": high,
            "moderate_risk_weeds": moderate
        }

    # ---------------- WEATHER ----------------
    if intent == "weather_forecast":

        weather = analysis.get("current_weather", {})

        return {
            "temperature": weather.get("temperature"),
            "humidity": weather.get("humidity"),
            "rain": weather.get("precip_mm")
        }

    # ---------------- SOIL MOISTURE ----------------
    if intent == "soil_moisture":

        return {
            "soil_moisture": analysis.get("current_soil_moisture")
        }

    # default
    return analysis