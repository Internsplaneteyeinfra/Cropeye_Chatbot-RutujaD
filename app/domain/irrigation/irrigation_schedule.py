# app/domain/irrigation/irrigation_schedule.py

from app.services.api_service import get_api_service
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional


class IrrigationSchedule:
    """
    Builds 7-day irrigation schedule Home Page(calculation only).
    No advice, no motor logic.
    """

    EFFICIENCY = 0.94
    ACRE_TO_SQM = 4046.86

    def __init__(self, auth_token: Optional[str] = None):
        self.api = get_api_service(auth_token)

    # -----------------------------
    # Helpers
    # -----------------------------

    def calculate_net_et(self, et: float, rainfall: float) -> float:
        net = et - rainfall
        return net if net > 0 else 0

    def calculate_water_required(self, net_et: float, kc: float) -> int:
        """
        Formula:
        Net ET × Kc × 0.94 × 4046.86
        Result: Liters per acre
        """
        if net_et <= 0 or kc <= 0:
            return 0

        liters = net_et * kc * self.EFFICIENCY * self.ACRE_TO_SQM
        return round(liters)

    # -----------------------------
    # Main builder
    # -----------------------------

    async def build(self, plot_id: str, kc: float = 0.3) -> List[Dict[str, Any]]:
        weather_today = await self.api.get_current_weather(plot_id)
        forecast = await self.api.get_weather_forecast(plot_id)
        et_data = await self.api.get_evapotranspiration(plot_id)

        base_et = (
            et_data.get("ET_mean_mm_per_day")
            or et_data.get("et_24hr")
            or et_data.get("et")
            or 0
        )

        today = datetime.now().date()
        schedule: List[Dict[str, Any]] = []

        for day_index in range(7):
            date = today + timedelta(days=day_index)

            if day_index == 0:
                rainfall = weather_today.get("precip_mm", 0)
                et_value = base_et
            else:
                forecast_list = forecast.get("data", []) if forecast else []

                forecast_day = (
                    forecast_list[day_index - 1]
                    if day_index - 1 < len(forecast_list)
                    else {}
                )

                rainfall = float(forecast_day.get("precip_mm", 0))
                et_value = base_et  # backend keeps ET flat; frontend adds variation

            net_et = self.calculate_net_et(et_value, rainfall)
            water_required = self.calculate_water_required(net_et, kc)

            schedule.append({
                "date": date.strftime("%d %b"),
                "is_today": day_index == 0,
                "evapotranspiration": et_value,
                "rainfall": rainfall,
                "net_et": net_et,
                "water_required_liters": water_required,
                "plant_water_uptake": None  # placeholder
            })

        return schedule
