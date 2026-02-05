# soil_moiture_agent.py 

from app.domain.soil_moisture.soil_moisture_map import SatelliteSoilMoisture
from app.domain.soil_moisture.soil_moisture_trend import IrrigationSoilMoisture


async def soil_moisture_agent(state: dict) -> dict:
    context = state.get("context", {})
    plot_id = context.get("plot_id")
    auth_token = context.get("auth_token")

    entities = state.get("entities", {})
    moisture_type = entities.get("query_type")

    satellite = SatelliteSoilMoisture(auth_token)
    irrigation = IrrigationSoilMoisture(auth_token)

    analysis = {"soil_moisture": {}}
    
    if moisture_type == "soil_moisture_map":
        analysis["soil_moisture"]["satellite"] = await satellite.fetch(plot_id)

    elif moisture_type == ("soil_moisture_trend"):
        analysis["soil_moisture"]["irrigation"] = await irrigation.build(plot_id)


    state["analysis"] = analysis
    return state
