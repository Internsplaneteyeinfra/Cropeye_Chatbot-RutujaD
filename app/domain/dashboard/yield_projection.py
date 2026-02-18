# app/domain/dashboard/yield_projection.py
from app.services.api_service import get_api_service

class YieldProjection:

    def __init__(self, token):
        self.api = get_api_service(token)

    async def fetch(self, plot_id):
        agro = await self.api.get_agro_stats(plot_id)

        if not agro or "error" in agro:
            return {}

        plot = agro.get(plot_id, {})
        yield_data = plot.get("brix_sugar", {}).get("sugar_yield", {})
        
        return {
            "mean": yield_data.get("mean"),
            "min": yield_data.get("min"),
            "max": yield_data.get("max")
        }

