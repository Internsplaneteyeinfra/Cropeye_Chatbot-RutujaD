"""
Farm Context Service
Extracts and manages farm context (plot, crop, plantation date, etc.)
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.services.api_service import get_api_service


def calculate_crop_stage(plantation_date: str, current_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate crop stage based on plantation date
    Returns: stage name, days since plantation, Kc value
    """
    if current_date is None:
        current_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        plant_dt = datetime.strptime(plantation_date, "%Y-%m-%d")
        curr_dt = datetime.strptime(current_date, "%Y-%m-%d")
        days = (curr_dt - plant_dt).days
        
        if days < 0:
            days = 0
        
        # Sugarcane growth stages
        if days <= 30:
            stage = "Germination"
            kc = 0.3
        elif days <= 90:
            stage = "Tillering"
            kc = 0.7
        elif days <= 150:
            stage = "Grand Growth"
            kc = 1.1
        elif days <= 300:
            stage = "Maturity"
            kc = 0.85
        else:
            stage = "Harvest Ready"
            kc = 0.8
        
        return {
            "stage": stage,
            "days_since_plantation": days,
            "kc": kc
        }
    except ValueError:
        return {
            "stage": "Unknown",
            "days_since_plantation": 0,
            "kc": 0.7
        }


async def get_farm_context(
    plot_name: Optional[str] = None,
    user_id: Optional[int] = None,
    auth_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get farm context for a plot
    Returns: plot_id, crop_type, plantation_date, area, irrigation_type, crop_stage, etc.
    """
    api_service = get_api_service(auth_token)
    
    # Get farmer profile
    profile_data = await api_service.get_farmer_profile(user_id)
    
    if "error" in profile_data:
        return {
            "error": profile_data["error"],
            "plot_id": plot_name,
            "crop_type": "Sugarcane",  # Default
            "plantation_date": None,
            "area_acres": None
        }
    
    # Extract plots from profile
    plots = profile_data.get("plots", [])
    
    if not plots:
        return {
            "error": "No plots found for this farmer",
            "plot_id": plot_name,
            "crop_type": "Sugarcane",
            "plantation_date": None,
            "area_acres": None
        }
    
    # Find the requested plot or use first plot
    selected_plot = None
    
    if plot_name:
        # Try to find plot by name
        for plot in plots:
            plot_id = (
                plot.get("fastapi_plot_id") or
                plot.get("plot_name") or
                f"{plot.get('gat_number', '')}_{plot.get('plot_number', '')}"
            )
            if plot_id == plot_name or str(plot_id) == str(plot_name):
                selected_plot = plot
                break
    
    # If not found, use first plot
    if not selected_plot:
        selected_plot = plots[0]
    
    # Extract farm data
    farms = selected_plot.get("farms", [])
    farm = farms[0] if farms else {}
    
    # Get crop type
    crop_type = "Sugarcane"  # Default
    if farm.get("crop_type"):
        if isinstance(farm["crop_type"], dict):
            crop_type = farm["crop_type"].get("crop_type", "Sugarcane")
        else:
            crop_type = str(farm["crop_type"])
    
    # Get plantation date
    plantation_date = None
    if farm.get("plantation_date"):
        plantation_date = farm["plantation_date"]
    elif farm.get("plantation_Date"):
        plantation_date = farm["plantation_Date"]
    
    # Get area
    area_acres = None
    if farm.get("area_size_numeric"):
        area_acres = float(farm["area_size_numeric"])
    elif farm.get("area_size"):
        try:
            area_acres = float(farm["area_size"])
        except (ValueError, TypeError):
            pass
    
    # Get irrigation type
    irrigation_type = "drip"  # Default
    if farm.get("irrigation_type_name"):
        irrigation_type = farm["irrigation_type_name"]
    elif farm.get("irrigation_Type"):
        irrigation_type = farm["irrigation_Type"]
    
    # Get plot ID
    plot_id = (
        selected_plot.get("fastapi_plot_id") or
        selected_plot.get("plot_name") or
        f"{selected_plot.get('gat_number', '')}_{selected_plot.get('plot_number', '')}"
    )
    
    # Calculate crop stage
    crop_stage_info = {}
    if plantation_date:
        crop_stage_info = calculate_crop_stage(plantation_date)
    
    return {
        "plot_id": str(plot_id),
        "plot_name": str(plot_id),
        "crop_type": crop_type,
        "plantation_date": plantation_date,
        "area_acres": area_acres,
        "irrigation_type": irrigation_type.lower(),
        "crop_stage": crop_stage_info.get("stage", "Unknown"),
        "days_since_plantation": crop_stage_info.get("days_since_plantation", 0),
        "kc": crop_stage_info.get("kc", 0.7),
        "error": None
    }
