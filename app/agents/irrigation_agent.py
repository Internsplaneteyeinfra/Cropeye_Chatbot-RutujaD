# # # agents/irrigation_agent.py

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
            schedule = IrrigationSchedule()   # ✅ no token
            result = await schedule.build(plot_id, lat, lon, cached)

            analysis["irrigation"]["schedule_7_day"] = result

    # ---------- STATUS ----------
    else:
        status = IrrigationStatus()   # ✅ no token
        result = await status.build(plot_id, cached)

        analysis["irrigation"]["status"] = result

    state["analysis"] = analysis
    return state