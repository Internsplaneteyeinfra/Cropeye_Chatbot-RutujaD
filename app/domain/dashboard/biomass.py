# app/domain/dashboard/biomass.py
from app.services.api_service import get_api_service

class Biomass:

    def __init__(self, auth_token):
        self.api = get_api_service(auth_token)

    async def fetch(self, plot_id):
        agro = await self.api.get_agro_stats(plot_id)

        if not agro or "error" in agro:
            return {}

        plot = agro.get(plot_id, {})
        biomass = plot.get("biomass", {})
        
        return {
            "mean": biomass.get("mean"),
            "min": biomass.get("min"),
            "max": biomass.get("max")
        }
