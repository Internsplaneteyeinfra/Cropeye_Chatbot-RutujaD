from app.services.api_service import get_api_service

class CropStatus:

    def __init__(self, auth_token):
        self.api = get_api_service(auth_token)

    async def fetch(self, plot_id):

        harvest = await self.api.get_harvest_status(plot_id)
        agro = await self.api.get_agro_stats(plot_id)

        summary = harvest.get("harvest_summary", {})

        return {
            "status": summary.get("harvest_status"),
            "days_to_harvest": agro.get("days_to_harvest"),
            "growth_stage": agro.get("current_growth_stage"),
            "plantation_type": agro.get("plantation_type")
        }
