# app/domain/dashboard/stress.py
from app.services.api_service import get_api_service

# class StressEvents:

#     def __init__(self, auth_token):
#         self.api = get_api_service(auth_token)

#     async def fetch(self, plot_id):
#         data = await self.api.get_stress_events(plot_id)

#         if not data or "error" in data:
#             return {}
        
        
#         return {
#             "stress_events": data.get("total_events")
#         }

class StressEvents:

    async def fetch(self, cached):

        data = cached.get("stress")

        if not data:
            return {}

        return {
            "stress_events": data.get("total_events"),
            "index_type": data.get("index_type"),
            "threshold": data.get("threshold_used")
        }