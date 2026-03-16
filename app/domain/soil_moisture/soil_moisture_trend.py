# # irrigation page soil_moisture_trend.py

from typing import Optional, List, Dict

class IrrigationSoilMoisture:
    """
    Handles:
    - Daily soil moisture (irrigation page)
    - Soil moisture card (latest value)
    - Weekly soil moisture trend
    """

    OPTIMAL_MIN = 60
    OPTIMAL_MAX = 80

    def __init__(self, auth_token: Optional[str] = None):
        self.auth_token = auth_token

    async def fetch(self, plot_id: str, cached: dict) -> dict:
        """
        Fetch soil moisture timeseries from CACHE instead of API
        """
        return cached.get("soil_moisture_timeseries")

    def extract_current(self, stack: list) -> float | None:
        if not stack:
            return None
        return stack[-1]["soil_moisture"]

    def compute_level(self, value: float | None) -> str:
        if value is None:
            return "unknown"
        if value < 40:
            return "low"
        elif 40 <= value < 80:
            return "good"
        elif 80 <= value <= 100:
            return "high"
        else:
            return "unknown"

    def weekly_trend(self, stack: List[dict]) -> List[Dict[str, float]]:
        return [
            {
                "day": d["day"],
                "soil_moisture": d["soil_moisture"]
            }
            for d in stack[-7:]
        ]

    async def build(self, plot_id: str, cached: dict) -> dict:
        data = await self.fetch(plot_id, cached)

        # API error
        if isinstance(data, dict) and "error" in data:
            return {
                "error": data["error"],
                "current": None,
                "weekly_trend": []
            }

        # SAME LOGIC (UNCHANGED)
        if isinstance(data, dict):
            stack = data.get("soil_moisture_stack", [])
        elif isinstance(data, list):
            stack = data
        else:
            stack = []

        if not stack:
            return {
                "error": "No soil moisture data available",
                "current": None,
                "weekly_trend": []
            }

        current_value = self.extract_current(stack)

        return {
            "source": "field_sensor",
            "current": {
                "value": current_value,
                "level": self.compute_level(current_value),
                "optimal_range": f"{self.OPTIMAL_MIN}–{self.OPTIMAL_MAX}%"
            },
            "weekly_trend": self.weekly_trend(stack)
        }