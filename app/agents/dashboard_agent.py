import asyncio
from app.domain.dashboard.crop_status import CropStatus
from app.domain.dashboard.biomass import Biomass
from app.domain.dashboard.yield_projection import YieldProjection
from app.domain.dashboard.stress import StressEvents
from app.domain.dashboard.sugar_content import SugarContent

# from app.domain.dashboard.indices import FieldIndices


async def dashboard_agent(state: dict):

    context = state.get("context", {})
    plot_id = context.get("plot_id")
    auth_token = context.get("auth_token")


    entities = state.get("entities", {})
    dashboard_type = entities.get("query_type")

    analysis = {"dashboard": {}}

    if dashboard_type == "crop_status_check":
        analysis["dashboard"]["crop"] = await CropStatus(auth_token).fetch(plot_id)

    elif dashboard_type == "biomass_check":
        analysis["dashboard"]["biomass"] = await Biomass(auth_token).fetch(plot_id)

    elif dashboard_type == "yield_info":
        analysis["dashboard"]["yield"] = await YieldProjection(auth_token).fetch(plot_id)

    elif dashboard_type == "stress_check":
        analysis["dashboard"]["stress"] = await StressEvents(auth_token).fetch(plot_id)

    elif dashboard_type == "sugar_content_check":
        analysis["dashboard"]["sugar_content"] = await SugarContent(auth_token).fetch(plot_id)

    # elif dashboard_type == "recovery_rate":
    #     analysis["dashboard"]["recovery_rate"] = await RecoveryRate(auth_token).fetch(plot_id)

    # elif dashboard_type == "field_indices":
    #     analysis["dashboard"]["field_indices"] = await FieldIndices(auth_token).fetch(plot_id)
    

    state["analysis"] = analysis
    return state