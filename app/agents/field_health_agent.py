# app/agents/field_health_agent.py

from datetime import datetime
from typing import Any, Dict

from app.domain.pest_risk.risk_calculator import generate_risk_assessment
from app.services.api_service import get_api_service


REQUIRED_PEST_DETECTION_KEYS = (
    "fungi_affected_pixel_percentage",
    "chewing_affected_pixel_percentage",
    "sucking_affected_pixel_percentage",
    "SoilBorn_affected_pixel_percentage",
)


def _empty_pest_detection() -> Dict[str, float]:
    return {k: None for k in REQUIRED_PEST_DETECTION_KEYS}


def _ensure_pest_detection(data: Any) -> Dict[str, float]:
    if not data or not isinstance(data, dict):
        return _empty_pest_detection()

    out = _empty_pest_detection()
    for k in REQUIRED_PEST_DETECTION_KEYS:
        if k in data and data[k] is not None:
            try:
                out[k] = float(data[k])
            except (TypeError, ValueError):
                pass
    return out


def _ensure_current_conditions(data: Any) -> Dict[str, Any]:
    if not data or not isinstance(data, dict):
        return {}

    month = data.get("month")

    try:
        temp = float(data.get("temperature", data.get("temperature_c")))
    except (TypeError, ValueError):
        temp = None

    try:
        humidity = float(data.get("humidity"))
    except (TypeError, ValueError):
        humidity = None

    return {
        "month": month,
        "temperature": temp,
        "humidity": humidity,
    }

async def field_health_agent(state: dict) -> dict:

    context = state.get("context") or {}
    entities = state.get("entities") or {}
    cached = context.get("cached_data") or {}
    intent = state.get("intent")

    plot_id = context.get("plot_id") or entities.get("plot_id")

    if not plot_id:
        return {
            "analysis": {
                "agent": "field_health",
                "error": "Plot ID missing"
            }
        }

    if intent == "field_score":
        field_analysis = cached.get("field_analysis")
        
        if not field_analysis:
            api_service = get_api_service()
            current_date = datetime.now().strftime("%Y-%m-%d")
            field_analysis = await api_service.get_field_analysis(
                plot_name=plot_id,
                end_date=current_date,
                days_back=7
            )
 
        if "error" in field_analysis or not field_analysis:
            return {
                "analysis": {
                    "agent": "field_health",
                    "intent": "field_score",
                    "plot_id": plot_id,
                    "error": field_analysis.get("error", "Field analysis data not available")
                }
            }
 
        state["analysis"] = {
            "agent": "field_health",
            "intent": "field_score",
            "plot_id": plot_id,
            "field_score": {
                "plotName": field_analysis.get("plot_name", plot_id),
                "overallHealth": field_analysis.get("overall_health", 0),
                "healthStatus": field_analysis.get("health_status", "Unknown"),
                "statistics": {
                    "mean": field_analysis.get("statistics", {}).get("mean", 0)
                }
            }
        }

        return state

    if intent == "crop_health_analysis":

        plantation_date = context.get("plantation_date")

        weather = cached.get("current_weather", {})

        current_conditions = {
            "month": datetime.utcnow().strftime("%B"),
            "temperature": weather.get("temperature_c"),
            "humidity": weather.get("humidity")
        }

        pest = cached.get("pest_detection", {})
        ps = pest.get("pixel_summary", {})

        pest_detection_data = {
            "fungi_affected_pixel_percentage": ps.get("fungi_affected_pixel_percentage"),
            "chewing_affected_pixel_percentage": ps.get("chewing_affected_pixel_percentage"),
            "sucking_affected_pixel_percentage": ps.get("sucking_affected_pixel_percentage"),
            "SoilBorn_affected_pixel_percentage": ps.get("SoilBorn_affected_pixel_percentage"),
        }

        result = generate_risk_assessment(
            plantation_date=plantation_date,
            current_conditions=current_conditions,
            pest_detection_data=pest_detection_data
        )

        result.pop("current_conditions", None)

        state["analysis"] = {
            "agent": "field_health",
            "intent": "crop_health_analysis",
            "plot_id": plot_id,
            "risk_assessment": result
        }

        return state