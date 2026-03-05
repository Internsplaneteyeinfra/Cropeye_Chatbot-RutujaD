# app/domain/dashboard/stress.py
from app.services.api_service import get_api_service

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

