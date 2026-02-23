# weather_agent.py

from app.domain.weather.current_weather import CurrentWeather
from app.domain.weather.forecast_7day import WeatherForecast


# async def weather_agent(state: dict) -> dict:

#     context = state.get("context", {})

#     plot_id = context.get("plot_id")
#     auth_token = context.get("auth_token")
#     lat = context.get("lat")
#     lon = context.get("lon")

#     current = CurrentWeather(auth_token)
#     forecast = WeatherForecast(auth_token)

#     analysis = {"weather": {}}

#     analysis["weather"]["current_weather"] = await current.fetch(plot_id, lat, lon)
#     analysis["weather"]["forecast_7day"] = await forecast.fetch(plot_id, lat, lon)

#     state["analysis"] = analysis

#     return state


# weather_agent.py

async def weather_agent(state: dict) -> dict:

    context = state.get("context", {})
    cached = context.get("cached_data", {})

    analysis = {"weather": {}}

    def get_cached(key):
        data = cached.get(key)
        if not data or data.get("status") == "failed":
            return {
                "message": "This data is currently unavailable for this plot."
            }
        return data

    analysis["weather"]["current_weather"] = get_cached("current_weather")
    analysis["weather"]["weather_forecast"] = get_cached("weather_forecast")

    state["analysis"] = analysis

    return state