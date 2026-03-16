# app/domain/dashboard/yield_projection.py

class YieldProjection:

    async def fetch(self, cached):

        agro = cached.get("agro")
        if not agro:
            return {}

        yield_data = agro.get("brix_sugar", {}).get("sugar_yield", {})

        return {
            "mean": yield_data.get("mean"),
            "min": yield_data.get("min"),
            "max": yield_data.get("max")
        }