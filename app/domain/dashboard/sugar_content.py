from app.services.api_service import get_api_service


# class SugarContent:

#     def __init__(self, auth_token):
#         self.api = get_api_service(auth_token)

#     async def fetch(self, plot_id: str) -> dict:
#         agro = await self.api.get_agro_stats(plot_id)

#         if not agro or "error" in agro:
#             return {}

#         plot = agro.get(plot_id, {})
#         brix = plot.get("brix_sugar", {}).get("brix", {})

#         return {
#             "mean": brix.get("mean"),
#             "min": brix.get("min"),
#             "max": brix.get("max")
#         }



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