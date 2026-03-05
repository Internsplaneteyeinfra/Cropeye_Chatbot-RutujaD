# app/services/report_service.py

"""
Report Service
Combines cached farm data with domain logic to generate comprehensive yield improvement reports.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from app.memory.redis_manager import redis_manager
from app.services.farm_context_service import get_farm_context

# Domain modules
from app.domain.dashboard.yield_projection import YieldProjection
from app.domain.dashboard.biomass import Biomass
from app.domain.dashboard.crop_status import CropStatus
from app.domain.dashboard.indices import FieldIndices
from app.domain.dashboard.stress import StressEvents
from app.domain.dashboard.sugar_content import SugarContent
from app.domain.irrigation.irrigation_status import IrrigationStatus
from app.domain.pest_risk.risk_calculator import generate_risk_assessment


async def get_report_data(plot_id: str, user_id: Optional[int] = None, auth_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches cached farm data, applies domain logic, and combines all relevant metrics
    for yield improvement report generation.
    
    Args:
        plot_id: Plot identifier
        user_id: Optional user ID
        auth_token: Optional authentication token
        
    Returns:
        Dictionary containing all processed farm metrics ready for LLM analysis
    """
    
    # Step 1: Fetch cached farm data from Redis
    cached_data = redis_manager.get_plot(plot_id)
    
    if not cached_data:
        return {"error": "Plot data not found. Please initialize the plot first."}
    
    # Step 2: Get farm context (Kc, crop stage, plantation date, etc.)
    farm_context = await get_farm_context(
        plot_name=plot_id,
        user_id=user_id,
        auth_token=auth_token
    )
    
    if farm_context.get("error"):
        return {"error": farm_context.get("error")}
    
    # Step 3: Process data through domain modules
    report_data = {
        "farm_context": farm_context,
        "timestamp": datetime.now().isoformat(),
    }
    
    # Yield Projection
    yield_projection = YieldProjection()
    yield_data = await yield_projection.fetch(cached_data)
    report_data["yield"] = yield_data
    
    # Biomass
    biomass = Biomass()
    biomass_data = await biomass.fetch(cached_data)
    report_data["biomass"] = biomass_data
    
    # Crop Status
    crop_status = CropStatus()
    crop_status_data = await crop_status.fetch(cached_data)
    report_data["crop_status"] = crop_status_data
    
    # Field Indices
    field_indices = FieldIndices()
    indices_data = await field_indices.fetch(cached_data, period="weekly")
    report_data["indices"] = indices_data
    
    # Stress Events
    stress = StressEvents()
    stress_data = await stress.fetch(cached_data)
    report_data["stress"] = stress_data
    
    # Sugar Content
    sugar_content = SugarContent()
    sugar_data = await sugar_content.fetch(cached_data)
    report_data["sugar_content"] = sugar_data
    
    # Irrigation Status
    irrigation_status = IrrigationStatus(auth_token=auth_token)
    irrigation_data = await irrigation_status.build(plot_id, cached_data)
    report_data["irrigation"] = irrigation_data
    
    # Soil Analysis
    soil_analysis = cached_data.get("soil_analysis", {})
    report_data["soil"] = {
        "N": soil_analysis.get("N"),
        "P": soil_analysis.get("P"),
        "K": soil_analysis.get("K"),
        "pH": soil_analysis.get("pH"),
        "CEC": soil_analysis.get("CEC"),
        "OC": soil_analysis.get("OC"),
        "BD": soil_analysis.get("BD"),
        "Fe": soil_analysis.get("Fe"),
        "SOC": soil_analysis.get("SOC"),
    }
    
    # NPK Requirements
    npk_requirements = cached_data.get("npk_requirements", {})
    report_data["npk_requirements"] = npk_requirements
    
    # Pest Detection and Risk Assessment
    pest_detection = cached_data.get("pest_detection", {})
    weather = cached_data.get("current_weather", {})
    
    if pest_detection and farm_context.get("plantation_date"):
        # Extract pixel_summary from pest_detection (same as pest_agent)
        ps = pest_detection.get("pixel_summary", {}) if isinstance(pest_detection, dict) else {}
        
        pest_detection_data = {
            "fungi_affected_pixel_percentage": float(ps.get("fungi_affected_pixel_percentage")) if ps.get("fungi_affected_pixel_percentage") is not None else 0.0,
            "chewing_affected_pixel_percentage": float(ps.get("chewing_affected_pixel_percentage")) if ps.get("chewing_affected_pixel_percentage") is not None else 0.0,
            "sucking_affected_pixel_percentage": float(ps.get("sucking_affected_pixel_percentage")) if ps.get("sucking_affected_pixel_percentage") is not None else 0.0,
            "SoilBorn_affected_pixel_percentage": float(ps.get("SoilBorn_affected_pixel_percentage")) if ps.get("SoilBorn_affected_pixel_percentage") is not None else 0.0,
        }
        
        current_conditions = {
            "month": datetime.now().strftime("%B"),
            "temperature": weather.get("temperature_c", 0),
            "humidity": weather.get("humidity", 0),
        }
        
        pest_risk = generate_risk_assessment(
            plantation_date=farm_context.get("plantation_date"),
            current_conditions=current_conditions,
            pest_detection_data=pest_detection_data
        )
        report_data["pest_risk"] = pest_risk
    else:
        report_data["pest_risk"] = {}
    
    # Weather Data
    report_data["weather"] = {
        "current": weather,
        "forecast": cached_data.get("weather_forecast", {}),
    }
    
    # Evapotranspiration
    et_data = cached_data.get("et", {})
    report_data["evapotranspiration"] = et_data
    
    # Soil Moisture Timeseries
    soil_moisture_ts = cached_data.get("soil_moisture_timeseries", {})
    report_data["soil_moisture_timeseries"] = soil_moisture_ts
    
    # Agro Stats Summary
    agro = cached_data.get("agro", {})
    report_data["agro_summary"] = {
        "days_to_harvest": agro.get("days_to_harvest"),
        "current_growth_stage": agro.get("current_growth_stage"),
        "plantation_type": agro.get("plantation_type"),
    }
    
    return report_data
