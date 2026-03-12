
class SugarContent:

    async def fetch(self, cached):

        agro = cached.get("agro")
        if not agro:
            return {}

        brix = agro.get("brix_sugar", {}).get("brix", {})

        return {
            "mean": brix.get("mean"),
            "min": brix.get("min"),
            "max": brix.get("max")

        }