# irrigation page soil_moisture_trend.py

from app.services.api_service import get_api_service
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
        self.api = get_api_service(auth_token)

    async def fetch(self, plot_id: str) -> dict:
        """
        Fetch soil moisture timeseries from FIELD service
        """
        return await self.api.get_soil_moisture_timeseries(plot_id)

    def extract_current(self, stack: list) -> float | None:
        """
        Latest available soil moisture (usually yesterday)
        """
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
        """
        Last 7 days trend for chart
        """
        return [
            {
                "day": d["day"],
                "soil_moisture": d["soil_moisture"]
            }
            for d in stack[-7:]
        ]

    async def build(self, plot_id: str) -> dict:
        data = await self.fetch(plot_id)

        # API error
        if isinstance(data, dict) and "error" in data:
            return {
                "error": data["error"],
                "current": None,
                "weekly_trend": []
            }

        # ✅ HANDLE BOTH RESPONSE SHAPES
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
                "optimal_range": f"{self.OPTIMAL_MIN}–{self.OPTIMAL_MAX}%",
            },
            "weekly_trend": self.weekly_trend(stack)
        }
