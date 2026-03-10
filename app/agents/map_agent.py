from app.domain.map_intelligence.soil_moisture_map import SoilMoistureMap
from app.domain.map_intelligence.water_uptake_map import WaterUptakeMap
from app.domain.map_intelligence.growth_map import GrowthMap
from app.domain.map_intelligence.pest_map import PestMap

async def map_agent(state: dict) -> dict:
    context = state.get("context", {})
    cached = context.get("cached_data", {})
    entities = state.get("entities", {})
    map_type = entities.get("query_type")
    analysis = {"map": {}}

    if map_type == "soil_moisture_map":
        soil_map = SoilMoistureMap()
        analysis["map"]["soil_moisture"] = await soil_map.fetch(cached)

    elif map_type == "water_uptake_map":
        water_map = WaterUptakeMap()
        analysis["map"]["water_uptake"] = await water_map.fetch(cached)

    elif map_type == "pest_map":
        pest_map = PestMap()
        analysis["map"]["pest"] = await pest_map.fetch(cached)

    elif map_type == "growth_map":
        growth_map = GrowthMap()
        analysis["map"]["growth"] = await growth_map.fetch(cached)

    state["analysis"] = analysis
    return state