from app.domain.map_intelligence.soil_moisture_map import SoilMoistureMap
from app.domain.map_intelligence.water_uptake_map import WaterUptakeMap
from app.domain.map_intelligence.growth_map import GrowthMap
from app.domain.map_intelligence.pest_map import PestMap

async def map_agent(state: dict) -> dict:
    context = state.get("context", {})
    plot_id = context.get("plot_id")
    auth_token = context.get("auth_token")

    entities = state.get("entities", {})
    map_type = entities.get("query_type")

    analysis = {"map": {}}

    if map_type == "soil_moisture_map":
        analysis["map"]["soil_moisture"] = await SoilMoistureMap(auth_token).fetch(plot_id)

    elif map_type == "water_uptake_map":
        analysis["map"]["water_uptake"] = await WaterUptakeMap(auth_token).fetch(plot_id)

    elif map_type == "pest_map":
        analysis["map"]["pest"] = await PestMap(auth_token).fetch(plot_id, context)

    elif map_type == "growth_map":
        analysis["map"]["growth"] = await GrowthMap(auth_token).fetch(plot_id)

    state["analysis"] = analysis
    return state
