# agents/soil_moiture_agent.py 

from app.domain.soil_moisture.soil_moisture_trend import IrrigationSoilMoisture
from datetime import datetime
# from app.prompts.soil_moisture_prompt import SOIL_MOISTURE_AGENT_PROMPT


async def soil_moisture_agent(state: dict) -> dict:
    context = state.get("context", {})
    plot_id = context.get("plot_id")
    auth_token = context.get("auth_token")

    # 🔑 STEP 1: context-level cache
    if "soil_moisture_analysis" not in context:
        irrigation = IrrigationSoilMoisture(auth_token)
        context["soil_moisture_analysis"] = await irrigation.build(plot_id)
        context["soil_moisture_cached_at"] = datetime.now().isoformat()

    # 🔑 STEP 2: reuse cached analysis
    state["analysis"] = {
        "soil_moisture": context["soil_moisture_analysis"]
    }

    # state["prompt"] = SOIL_MOISTURE_AGENT_PROMPT

    return state