# # agents/irrigation_agent.py

# from app.domain.irrigation.irrigation_status import IrrigationStatus
# from app.domain.irrigation.irrigation_schedule import IrrigationSchedule


# async def irrigation_agent(state: dict) -> dict:
#     context = state.get("context", {})

#     plot_id = context.get("plot_id")
#     auth_token = context.get("auth_token")
#     lat = context.get("lat")
#     lon = context.get("lon")

#     entities = state.get("entities", {})
#     query_type = entities.get("query_type")

#     analysis = {"irrigation": {}}

#     if query_type == "7_day_schedule" and plot_id:
#         schedule = IrrigationSchedule(auth_token)

#         # backend auto derives KC + motor + pipe from profile
#         analysis["irrigation"]["schedule_7_day"] = await schedule.build(plot_id, lat, lon)

#     else:
#         status = IrrigationStatus(auth_token)
#         analysis["irrigation"]["status"] = await status.build(plot_id, lat, lon)

#     state["analysis"] = analysis
#     return state


from app.domain.irrigation.irrigation_status import IrrigationStatus
from app.domain.irrigation.irrigation_schedule import IrrigationSchedule


async def irrigation_agent(state: dict) -> dict:

    context = state.get("context", {})
    cached = context.get("cached_data", {})

    plot_id = context.get("plot_id")
    auth_token = context.get("auth_token")
    lat = context.get("lat")
    lon = context.get("lon")

    entities = state.get("entities", {})
    query_type = entities.get("query_type")

    analysis = {"irrigation": {}}

    def get_cached(key):
        data = cached.get(key)
        if not data or data.get("status") == "failed":
            return None
        return data

    if query_type == "7_day_schedule" and plot_id:
        schedule = IrrigationSchedule(auth_token)
        analysis["irrigation"]["schedule_7_day"] = await schedule.build( plot_id, lat, lon, cached)

    else:
        status = IrrigationStatus(auth_token)
        analysis["irrigation"]["status"] = await status.build( plot_id, lat, lon, cached)

    state["analysis"] = analysis
    return state