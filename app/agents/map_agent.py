from app.domain.map_intelligence.soil_moisture_map import SoilMoistureMap
from app.domain.map_intelligence.water_uptake_map import WaterUptakeMap
from app.domain.map_intelligence.growth_map import GrowthMap
from app.domain.map_intelligence.pest_map import PestMap

async def map_agent(state: dict) -> dict:
    context = state.get("context", {})
    plot_id = context.get("plot_id")
    auth_token = context.get("auth_token")

    cached = context.get("cached_data", {})

    entities = state.get("entities", {})
    map_type = entities.get("query_type")

    analysis = {"map": {}}

    if map_type == "soil_moisture_map":
        if cached.get("soil_moisture_map"):
            analysis["map"]["soil_moisture"] = cached["soil_moisture_map"]
        else:
            analysis["map"]["soil_moisture"] = await SoilMoistureMap(auth_token).fetch(plot_id)


    elif map_type == "water_uptake_map":
        if cached.get("water_uptake_map"):
            analysis["map"]["water_uptake"] = cached["water_uptake_map"]
        else:
            analysis["map"]["water_uptake"] = await WaterUptakeMap(auth_token).fetch(plot_id)


    elif map_type == "pest_map":
        if cached.get("pest_map"):
            analysis["map"]["pest"] = cached["pest_map"]
        else:
            analysis["map"]["pest"] = await PestMap(auth_token).fetch(plot_id)


    elif map_type == "growth_map":
        if cached.get("growth_map"):
            analysis["map"]["growth"] = cached["growth_map"]
        else:
            analysis["map"]["growth"] = await GrowthMap(auth_token).fetch(plot_id)


    state["analysis"] = analysis
    return state
