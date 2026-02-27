import asyncio
from app.domain.dashboard.crop_status import CropStatus
from app.domain.dashboard.biomass import Biomass
from app.domain.dashboard.yield_projection import YieldProjection
from app.domain.dashboard.stress import StressEvents
from app.domain.dashboard.sugar_content import SugarContent

from app.domain.dashboard.indices import FieldIndices
# from app.domain.dashboard.recovery_rate import RecoveryRate

from app.utils.cache_helper import get_cached_or_fail

async def dashboard_agent(state: dict):

    context = state.get("context", {})
    cached = context.get("cached_data", {})
    entities = state.get("entities", {})

    dashboard_type = entities.get("query_type")
    analysis = {"dashboard": {}}

    if dashboard_type == "crop_status_check":
        analysis["dashboard"]["crop"] = await CropStatus().fetch(cached)

    elif dashboard_type == "biomass_check":
        analysis["dashboard"]["biomass"] = await Biomass().fetch(cached)

    elif dashboard_type == "yield_info":
        analysis["dashboard"]["yield"] = await YieldProjection().fetch(cached)  

    elif dashboard_type == "stress_check":
        analysis["dashboard"]["stress"] = await StressEvents().fetch(cached)

    elif dashboard_type == "sugar_content_check":
        analysis["dashboard"]["sugar_content"] = await SugarContent().fetch(cached)

    elif dashboard_type == "indices_check":
        period = entities.get("time_period", "weekly")
        analysis["dashboard"]["indices"] = await FieldIndices().fetch(cached, period)

    state["analysis"] = analysis
    return state
