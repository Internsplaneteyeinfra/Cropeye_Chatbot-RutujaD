# app/domain/irrigation/irrigation_status.py

from app.services.api_service import get_api_service
from typing import Optional, Dict, Any


# class IrrigationStatus:
#     """
#     Builds current irrigation status cards:
#     - Rainfall
#     - Temperature
#     - Humidity
#     - Evapotranspiration (ET)
#     - Soil Moisture (latest field value)
#     - Plant Water Uptake (calculated placeholder)
#     """

#     def __init__(self, auth_token: Optional[str] = None):
#         self.api = get_api_service(auth_token)

#     async def build(self, plot_id: str) -> Dict[str, Any]:
#         # -----------------------------
#         # Fetch required data
#         # -----------------------------

#         weather = await self.api.get_current_weather(plot_id)
#         et_data = await self.api.get_evapotranspiration(plot_id)
#         soil_stack = await self.api.get_soil_moisture_timeseries(plot_id)

#         # -----------------------------
#         # Soil moisture (latest value)
#         # -----------------------------

#         soil_moisture_value = None
#         if isinstance(soil_stack, list) and soil_stack:
#             soil_moisture_value = soil_stack[-1].get("soil_moisture")

#         # -----------------------------
#         # ET value
#         # -----------------------------

#         et_value = None
#         if isinstance(et_data, dict):
#             et_value = et_data.get("ET_mean_mm_per_day")

#         # -----------------------------
#         # Weather values
#         # -----------------------------

#         rainfall = weather.get("rainfall") if isinstance(weather, dict) else None
#         temperature = weather.get("temperature") if isinstance(weather, dict) else None
#         humidity = weather.get("humidity") if isinstance(weather, dict) else None

#         # -----------------------------
#         # Plant Water Uptake (PLACEHOLDER)
#         # -----------------------------
#         # ⚠️ Formula will be plugged later
#         plant_water_uptake = None

#         # -----------------------------
#         # Final structured response
#         # -----------------------------

#         return {
#             "rainfall_mm": rainfall,
#             "temperature_c": temperature,
#             "humidity_percent": humidity,
#             "evapotranspiration_mm_per_day": et_value,
#             "soil_moisture_percent": soil_moisture_value,
#             "plant_water_uptake_mm": plant_water_uptake
#         }


from typing import Optional, Dict, Any


class IrrigationStatus:
    """
    Builds current irrigation status cards:
    - Rainfall
    - Temperature
    - Humidity
    - Evapotranspiration (ET)
    - Soil Moisture (latest field value)
    - Plant Water Uptake (calculated placeholder)
    """

    def __init__(self, auth_token: Optional[str] = None):
        self.auth_token = auth_token

    async def build(self, plot_id: str, cached: dict) -> Dict[str, Any]:
        # -----------------------------
        # Fetch from CACHE instead of API
        # -----------------------------

        weather = cached.get("current_weather", {})
        et_data = cached.get("et", {})
        soil_stack = cached.get("soil_moisture_timeseries", {})

        # -----------------------------
        # Soil moisture (latest value)
        # -----------------------------

        soil_moisture_value = None
        stack = soil_stack.get("soil_moisture_stack") if isinstance(soil_stack, dict) else None
        if isinstance(stack, list) and stack:
            soil_moisture_value = stack[-1].get("soil_moisture")

        # -----------------------------
        # ET value
        # -----------------------------

        et_value = None
        if isinstance(et_data, dict):
            et_value = et_data.get("ET_mean_mm_per_day")

        # -----------------------------
        # Weather values
        # -----------------------------

        rainfall = weather.get("precip_mm")
        temperature = weather.get("temperature_c")
        humidity = weather.get("humidity")

        # -----------------------------
        # Plant Water Uptake (PLACEHOLDER)
        # -----------------------------

        plant_water_uptake = None

        # -----------------------------
        # Final structured response
        # -----------------------------

        return {
            "rainfall_mm": rainfall,
            "temperature_c": temperature,
            "humidity_percent": humidity,
            "evapotranspiration_mm_per_day": et_value,
            "soil_moisture_percent": soil_moisture_value,
            "plant_water_uptake_mm": plant_water_uptake
        }