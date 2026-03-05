# app/domain/dashboard/biomass.py
from app.services.api_service import get_api_service

class Biomass:

    async def fetch(self, cached):

        agro = cached.get("agro")

        if not agro:
            return {}

        biomass = agro.get("biomass", {})

        return {
            "mean": biomass.get("mean"),
            "min": biomass.get("min"),
            "max": biomass.get("max")
        }