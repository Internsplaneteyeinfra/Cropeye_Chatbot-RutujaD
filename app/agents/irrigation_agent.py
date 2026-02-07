# agents/irrigation_agent.py

from app.domain.irrigation.irrigation_status import IrrigationStatus
from app.domain.irrigation.irrigation_schedule import IrrigationSchedule

async def irrigation_agent(state: dict) -> dict:
    context = state.get("context", {})
    plot_id = context.get("plot_id")
    auth_token = context.get("auth_token")

    entities = state.get("entities", {})
    query_type = entities.get("query_type")

    # status = IrrigationStatus(auth_token)
    # schedule = IrrigationSchedule(auth_token)

    analysis = {"irrigation": {}}

    if query_type == "7_day_schedule":
        schedule = IrrigationSchedule(auth_token)
        analysis["irrigation"]["schedule_7_day"] = await schedule.build(plot_id)

    else:
        status = IrrigationStatus(auth_token)
        analysis["irrigation"]["status"] = await status.build(plot_id)

    state["analysis"] = analysis
    return state
