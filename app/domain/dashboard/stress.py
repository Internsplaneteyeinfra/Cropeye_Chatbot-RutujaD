# app/domain/dashboard/stress.py

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

