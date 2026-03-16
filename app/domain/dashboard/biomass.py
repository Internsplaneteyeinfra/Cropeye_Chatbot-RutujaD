# app/domain/dashboard/biomass.py

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