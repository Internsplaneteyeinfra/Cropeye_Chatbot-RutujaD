from app.domain.map_intelligence.soil_moisture_map import SoilMoistureMap
from app.domain.map_intelligence.water_uptake_map import WaterUptakeMap
from app.domain.map_intelligence.growth_map import GrowthMap
from app.domain.map_intelligence.pest_map import PestMap

async def map_agent(state: dict) -> dict:
    context = state.get("context", {})
    cached = context.get("cached_data", {})
    entities = state.get("entities", {})
    map_type = entities.get("query_type")
    plot_id = context.get("plot_id")

    analysis = {"map": {}}

    def get_cached(key):
        data = cached.get(key)
        if not data or data.get("status") == "failed":
            return {
                "message": "This data is currently unavailable for this plot."
            }
        return data

    if map_type == "soil_moisture_map":
        soil_map = SoilMoistureMap()
        compressed = await soil_map.fetch(plot_id)
        analysis["map"]["soil_moisture"] = compressed

    elif map_type == "water_uptake_map":
        water_map = WaterUptakeMap()
        compressed = await water_map.fetch(plot_id)
        analysis["map"]["water_uptake"] = compressed

    elif map_type == "pest_map":
        pest_map = PestMap()
        compressed = await pest_map.fetch(plot_id)
        analysis["map"]["pest"] = compressed

    elif map_type == "growth_map":
        growth_map = GrowthMap()
        compressed = await growth_map.fetch(plot_id)
        analysis["map"]["growth"] = compressed

    state["analysis"] = analysis
    return state