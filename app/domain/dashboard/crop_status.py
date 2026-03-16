#app domain/dashboard/crop_status.py

class CropStatus:

    async def fetch(self, cached):

        harvest = cached.get("harvest", {})
        agro = cached.get("agro", {})

        summary = harvest.get("harvest_summary", {})

        return {
            "status": summary.get("harvest_status"),
            "days_to_harvest": agro.get("days_to_harvest"),
            "growth_stage": agro.get("current_growth_stage"),
            "plantation_type": agro.get("plantation_type")
        }