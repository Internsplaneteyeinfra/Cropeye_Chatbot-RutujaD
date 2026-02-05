# weather_agent.py

from app.domain.weather.current_weather import CurrentWeather
from app.domain.weather.forecast_7day import WeatherForecast

async def weather_agent(state: dict) -> dict:

    context = state.get("context", {})
    plot_id = context.get("plot_id")
    auth_token = context.get("auth_token")

    current = CurrentWeather(auth_token)
    forecast = WeatherForecast(auth_token)

    analysis = {"weather": {}}

    analysis["weather"]["current_weather"] = await current.fetch(plot_id)
    analysis["weather"]["forecast_7day"] = await forecast.fetch(plot_id)

    state["analysis"] = analysis
    return state
