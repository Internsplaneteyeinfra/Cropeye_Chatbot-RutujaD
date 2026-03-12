# # # # agents/irrigation_agent.py

# from app.domain.irrigation.irrigation_status import IrrigationStatus
# from app.domain.irrigation.irrigation_schedule import IrrigationSchedule
# async def irrigation_agent(state: dict) -> dict:

#     context = state.get("context", {})
#     cached = context.get("cached_data", {})

#     plot_id = context.get("plot_id")
#     lat = context.get("lat")
#     lon = context.get("lon")

#     intent = state.get("intent")

#     analysis = {"irrigation": {}}

#     # ---------- SCHEDULE ----------
#     if intent == "irrigation_schedule":

#         cached_schedule = cached.get("irrigation_schedule")

#         if cached_schedule:
#             analysis["irrigation"]["schedule_7_day"] = cached_schedule

#         else:
#             schedule = IrrigationSchedule()  
#             result = await schedule.build(plot_id, lat, lon, cached, context)

#             analysis["irrigation"]["schedule_7_day"] = result

#     # ---------- STATUS ----------
#     else:
#         # status = IrrigationStatus()  
#         # result = await status.build(plot_id, cached)

#         # analysis["irrigation"]["status"] = result
#         status = IrrigationStatus()
#     result = await status.build(plot_id, cached)

#     parameter = state.get("entities", {}).get("parameter")

#     # If user asked specific parameter
#     if parameter:

#         mapping = {
#             "rainfall": "rainfall_mm",
#             "temperature": "temperature_c",
#             "humidity": "humidity_percent",
#             "ET": "evapotranspiration_mm_per_day",
#             "soil_moisture": "soil_moisture_percent",
#             "plant_water_uptake": "plant_water_uptake_mm"
#         }

#         key = mapping.get(parameter)

#         if key and key in result:
#             analysis["irrigation"]["status"] = {
#                 key: result[key]
#             }
#         else:
#             analysis["irrigation"]["status"] = result

#     # If user asked general irrigation
#     else:
#         analysis["irrigation"]["status"] = result

#     state["analysis"] = analysis
#     return state


from app.domain.irrigation.irrigation_status import IrrigationStatus
from app.domain.irrigation.irrigation_schedule import IrrigationSchedule


async def irrigation_agent(state: dict) -> dict:

    context = state.get("context", {})
    cached = context.get("cached_data", {})

    plot_id = context.get("plot_id")
    lat = context.get("lat")
    lon = context.get("lon")

    intent = state.get("intent")

    analysis = {"irrigation": {}}

    # ---------- SCHEDULE ----------
    if intent == "irrigation_schedule":

        cached_schedule = cached.get("irrigation_schedule")

        if cached_schedule:
            analysis["irrigation"]["schedule_7_day"] = cached_schedule

        else:
            schedule = IrrigationSchedule()
            result = await schedule.build(plot_id, lat, lon, cached, context)

            analysis["irrigation"]["schedule_7_day"] = result

    # ---------- STATUS ----------
    else:

        status = IrrigationStatus()
        result = await status.build(plot_id, cached)

        parameter = state.get("entities", {}).get("parameter")

        if parameter:

            mapping = {
                "rainfall": "rainfall_mm",
                "temperature": "temperature_c",
                "humidity": "humidity_percent",
                "ET": "evapotranspiration_mm_per_day",
                "soil_moisture": "soil_moisture_percent",
                "plant_water_uptake": "plant_water_uptake_mm"
            }

            key = mapping.get(parameter)

            if key and key in result:
                analysis["irrigation"]["status"] = {
                    key: result[key]
                }
            else:
                analysis["irrigation"]["status"] = result

        else:
            analysis["irrigation"]["status"] = result

    state["analysis"] = analysis
    return state