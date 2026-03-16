# app/domain/irrigation/irrigation_status.py

from typing import Optional, Dict, Any
from app.memory.redis_manager import redis_manager
from app.domain.irrigation.irrigation_schedule import IrrigationSchedule


class IrrigationStatus:
    """
    Builds current irrigation status cards:
    - Rainfall
    - Temperature
    - Humidity
    - Evapotranspiration (ET)
    - Soil Moisture (latest field value)
    - Plant Water Uptake (calculated using exact frontend logic)
    """

    async def build(self, plot_id: str, cached: dict, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
     
        weather = cached.get("current_weather", {})
        et_data = cached.get("et", {})
        soil_stack = cached.get("soil_moisture_timeseries", {})

        soil_moisture_value = None
        stack = soil_stack.get("soil_moisture_stack") if isinstance(soil_stack, dict) else None
        if isinstance(stack, list) and stack:
            soil_moisture_value = stack[-1].get("soil_moisture")

        et_value = None
        if isinstance(et_data, dict):
            et_value = et_data.get("ET_mean_mm_per_day")

        rainfall = weather.get("precip_mm")
        temperature = weather.get("temperature_c")
        humidity = weather.get("humidity")

        plant_water_uptake_liters_per_hour = None
        plant_water_uptake_efficiency = None

        try:
            irrigation_schedule_data = cached.get("irrigation_schedule")
            
            if not irrigation_schedule_data and context:
                schedule = IrrigationSchedule()
                lat = context.get("lat")
                lon = context.get("lon")
                if lat and lon:
                    irrigation_schedule_data = await schedule.build(plot_id, lat, lon, cached, context)
            
            water_required_liters = 0
            if isinstance(irrigation_schedule_data, list):
                today_data = next((day for day in irrigation_schedule_data if day.get("is_today")), None)
                if today_data:
                    water_required_liters = today_data.get("water_required_liters", 0)
            
            plants_in_field = 0
            profile_data = redis_manager.get("public_plots")
            if profile_data:
                plots = profile_data.get("results", [])
                for plot in plots:
                    pid = plot.get("fastapi_plot_id")
                    if str(pid) == str(plot_id):
                        farms = plot.get("farms", [])
                        if farms and len(farms) > 0:
                            plants_in_field = farms[0].get("plants_in_field", 0)
                            break
            
            if plants_in_field > 0:
                plant_water_uptake_liters_per_hour = (water_required_liters / plants_in_field) / 24
            else:
                plant_water_uptake_liters_per_hour = 0.0
            
            water_uptake_map = cached.get("water_uptake_map", {})
            pixel_summary = water_uptake_map.get("pixel_summary", {})
            
            if pixel_summary:
                adequate = pixel_summary.get("adequat_pixel_percentage", 0) or 0
                excellent = pixel_summary.get("excellent_pixel_percentage", 0) or 0
                
                plant_water_uptake_efficiency = round(adequate + excellent)
            else:
                plant_water_uptake_efficiency = 0
                
        except Exception as e:
            print(f"[IrrigationStatus] Error calculating plant water uptake: {e}")
            plant_water_uptake_liters_per_hour = None
            plant_water_uptake_efficiency = None

        return {
            "rainfall_mm": rainfall,
            "temperature_c": temperature,
            "humidity_percent": humidity,
            "evapotranspiration_mm_per_day": et_value,
            "soil_moisture_percent": soil_moisture_value,
            "plant_water_uptake_liters_per_hour": plant_water_uptake_liters_per_hour,
            "plant_water_uptake_efficiency_percent": plant_water_uptake_efficiency,
            "plant_water_uptake_mm": plant_water_uptake_liters_per_hour
        }