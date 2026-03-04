

# # weather_agent.py
# from app.domain.weather.current_weather import CurrentWeather
# from app.domain.weather.forecast_7day import WeatherForecast

# async def weather_agent(state: dict) -> dict:

#     context = state.get("context", {})
#     cached = context.get("cached_data", {})

#     analysis = {"weather": {}}

#     def get_cached(key):
#         data = cached.get(key)
#         if not data or data.get("status") == "failed":
#             return {
#                 "message": "This data is currently unavailable for this plot."
#             }
#         return data

#     analysis["weather"]["current_weather"] = get_cached("current_weather")
#     analysis["weather"]["weather_forecast"] = get_cached("weather_forecast")

#     state["analysis"] = analysis

#     return state

# async def weather_agent(state: dict) -> dict:

#     analysis_payload = state.get("analysis", {})
#     filtered_data = analysis_payload.get("data", {})

#     result = {"weather": {}}

#     def get_data(key):
#         data = filtered_data.get(key)

#         if not data:
#             return {
#                 "message": "Weather data not available"
#             }

#         return data

#     result["weather"]["current_weather"] = get_data("current_weather")
#     result["weather"]["weather_forecast"] = get_data("weather_forecast")

#     state["analysis"] = result

#     print("WEATHER FILTERED DATA:", filtered_data)

#     return state


async def weather_agent(state: dict) -> dict:

    analysis_payload = state.get("analysis", {})
    filtered_data = analysis_payload.get("data", {})
    entities = state.get("entities", {})

    query_type = entities.get("query_type")

    result = {"weather": {}}

    def get_data(key):
        data = filtered_data.get(key)
        if not data:
            return {"message": "Weather data not available"}
        return data

    if query_type == "current":
        result["weather"]["current_weather"] = get_data("current_weather")

    elif query_type == "forecast":
        result["weather"]["weather_forecast"] = get_data("weather_forecast")

    else:
        # fallback
        result["weather"]["current_weather"] = get_data("current_weather")

    state["analysis"] = result

    return state