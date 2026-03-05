

# weather_agent.py
from app.domain.weather.current_weather import CurrentWeather
from app.domain.weather.forecast_7day import WeatherForecast

async def weather_agent(state: dict) -> dict:

    context = state.get("context", {})
    cached = context.get("cached_data", {})
    intent = state.get("intent")
    analysis = {"weather": {}}

    def get_cached(key):
        data = cached.get(key)
        if not data or data.get("status") == "failed":
            return {
                "message": "This data is currently unavailable for this plot."
            }
        return data

    if intent == "weather_forecast":
        analysis["weather"]["weather_forecast"] = get_cached("weather_forecast")

    elif intent == "current_weather":
        analysis["weather"]["current_weather"] = get_cached("current_weather")

    
    # analysis["weather"]["current_weather"] = get_cached("current_weather")
    # analysis["weather"]["weather_forecast"] = get_cached("weather_forecast")

    state["analysis"] = analysis

    return state