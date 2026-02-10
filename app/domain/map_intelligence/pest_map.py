# domain/map_intelligence/pest_map.py
"""
Pest Map Analysis for CROPEYE.
Fetches pest detection data from API and converts percentages to severity levels.
All values and severity levels MUST match frontend logic (pestt folder).
"""

from typing import Dict, Any, Optional
from app.services.api_service import get_api_service

# Severity levels as defined in frontend (pestt) - do not change.
SEVERITY_LEVELS = ("Very Low", "Low", "Medium", "High", "Very High")

# Frontend-aligned thresholds: percentage (0-100) -> value (0-4) -> severity
# Matches frontend logic from pestt folder
def _percentage_to_value(percentage: float) -> int:
    """
    Convert percentage (0-100) to numeric value (0-4).
    Matches frontend logic: 0%->0, 1-10%->1, 11-25%->2, 26-50%->3, 50%+->4
    """
    pct = max(0.0, min(100.0, float(percentage)))
    
    if pct == 0:
        return 0
    elif pct <= 10:
        return 1
    elif pct <= 25:
        return 2
    elif pct <= 50:
        return 3
    else:
        return 4


def _value_to_severity(value: int) -> str:
    """
    Convert numeric value (0-4) to severity level.
    Matches frontend logic from pestt folder.
    """
    if value <= 0:
        return "Very Low"
    if value == 1:
        return "Low"
    if value == 2:
        return "Medium"
    if value == 3:
        return "High"
    return "Very High"


def _build_pest_category(percentage: float) -> Dict[str, Any]:
    """
    Build pest category object from percentage.
    Converts percentage to value (0-4) and severity level.
    """
    value = _percentage_to_value(percentage)
    return {
        "value": value,
        "level": _value_to_severity(value),
    }


class PestMap:
    """
    Fetches pest detection data from API and converts percentages to severity levels.
    
    Frontend files reference: 
    - frontend/cropeye07/src/components/pestt/meter/riskAssessmentService.ts
    - frontend/cropeye07/src/components/Map.tsx
    """

    def __init__(self, auth_token: Optional[str] = None):
        self.api = get_api_service(auth_token)

    async def fetch(self, plot_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch pest detection data from API and compute pest analysis.
        
        """
        # Fetch pest detection data from API
        data = await self.api.get_pest_detection(plot_id)
        
        if not data or "error" in data:
            return {
                "error": "Failed to fetch pest detection data",
            }
        
        # Extract percentages from pixel_summary (matching frontend logic)
        pixel_summary = data.get("pixel_summary", {})
        
        chewing_percentage = pixel_summary.get("chewing_affected_pixel_percentage", 0) or 0
        sucking_percentage = pixel_summary.get("sucking_affected_pixel_percentage", 0) or 0
        fungi_percentage = pixel_summary.get("fungi_affected_pixel_percentage", 0) or 0
        soil_borne_percentage = pixel_summary.get("SoilBorn_affected_pixel_percentage", 0) or 0
        
        # Convert percentages to values and severity levels using frontend logic
        return {
            "intent": "pest_map",
            "plot_id": plot_id or "",
            "pest_analysis": {
                "chewing": _build_pest_category(chewing_percentage),
                "sucking": _build_pest_category(sucking_percentage),
                "fungi": _build_pest_category(fungi_percentage),
                "soil_borne": _build_pest_category(soil_borne_percentage),
            },
            "map_ready": True,
        }
