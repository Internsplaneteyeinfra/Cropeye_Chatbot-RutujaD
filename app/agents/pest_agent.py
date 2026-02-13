# app/agents/pest_agent.py
# Replicates frontend pestt risk logic. Fetches data from same APIs as frontend when not in context.

from datetime import datetime, timedelta
from typing import Any, Dict

from app.domain.pest_risk.risk_calculator import generate_risk_assessment
from app.services.api_service import get_api_service


REQUIRED_PEST_DETECTION_KEYS = (
    "fungi_affected_pixel_percentage",
    "chewing_affected_pixel_percentage",
    "sucking_affected_pixel_percentage",
    "SoilBorn_affected_pixel_percentage",
)


def _get_pest_detection_defaults() -> Dict[str, float]:
    return {
        "fungi_affected_pixel_percentage": 0,
        "chewing_affected_pixel_percentage": 0,
        "sucking_affected_pixel_percentage": 0,
        "SoilBorn_affected_pixel_percentage": 0,
    }


def _ensure_pest_detection(data: Any) -> Dict[str, float]:
    if not data or not isinstance(data, dict):
        return _get_pest_detection_defaults()
    out = _get_pest_detection_defaults().copy()
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
        temp = float(data.get("temperature", data.get("temperature_c", 0)))
    except (TypeError, ValueError):
        temp = 0
    try:
        humidity = float(data.get("humidity", 0))
    except (TypeError, ValueError):
        humidity = 0
    return {"month": month or "", "temperature": temp, "humidity": humidity}


def _default_plantation_date() -> str:
    return (datetime.utcnow() - timedelta(days=90)).strftime("%Y-%m-%d")


def _default_current_conditions() -> Dict[str, Any]:
    now = datetime.utcnow()
    return {
        "month": now.strftime("%B"),
        "temperature": 28,
        "humidity": 65,
    }


async def _fetch_plantation_date(api: Any, plot_id: str) -> str:
    """Try to get plantation_date from farmer profile (same source as frontend)."""
    try:
        profile = await api.get_farmer_profile()

        if not profile or "error" in profile:
            print("⚠ API error — using default plantation date")
            return _default_plantation_date()

        plots = profile.get("plots") or profile.get("data", {}).get("plots") or []
        for plot in plots:
            pid = (
                plot.get("fastapi_plot_id")
                or plot.get("plot_name")
                or (f"{plot.get('gat_number', '')}_{plot.get('plot_number', '')}")
            )
            if str(pid) == str(plot_id):
                farms = plot.get("farms") or []
                if farms:
                    fd = farms[0]
                    pd = fd.get("plantation_date") or fd.get("plantation_Date")
                    if pd and isinstance(pd, str) and pd.strip():
                        print("✅ Plantation date from API:", pd)
                        return pd.strip()
                break
    except Exception:
        pass
    return _default_plantation_date()


async def _fetch_current_conditions(api: Any, plot_id: str) -> Dict[str, Any]:
    """Fetch weather from same API as frontend (current-weather by plot_id)."""
    now = datetime.utcnow()
    default = {"month": now.strftime("%B"), "temperature": 28, "humidity": 65}
    try:
        data = await api.get_current_weather(plot_id)
        if not data or "error" in data:
            return default
        temp = data.get("temperature_c", data.get("temperature", 28))
        humidity = data.get("humidity", 65)
        try:
            temp = float(temp)
        except (TypeError, ValueError):
            temp = 28
        try:
            humidity = float(humidity)
        except (TypeError, ValueError):
            humidity = 65
        return {"month": now.strftime("%B"), "temperature": temp, "humidity": humidity}
    except Exception:
        return default


async def _fetch_pest_detection_data(api: Any, plot_id: str) -> Dict[str, float]:
    """Fetch pest detection from same API as frontend (pixel_summary percentages)."""
    default = _get_pest_detection_defaults()
    try:
        data = await api.get_pest_detection(plot_id)
        if not data or "error" in data:
            return default
        ps = data.get("pixel_summary") or {}
        return {
            "fungi_affected_pixel_percentage": float(ps.get("fungi_affected_pixel_percentage") or 0),
            "chewing_affected_pixel_percentage": float(ps.get("chewing_affected_pixel_percentage") or 0),
            "sucking_affected_pixel_percentage": float(ps.get("sucking_affected_pixel_percentage") or 0),
            "SoilBorn_affected_pixel_percentage": float(ps.get("SoilBorn_affected_pixel_percentage") or 0),
        }
    except Exception:
        return default


async def pest_agent(state: dict) -> dict:
    """
    Runs the same risk calculation as frontend pestt (Pests, Diseases, Weeds).
    Fetches plantation_date, weather, and pest_detection from same backend APIs as frontend
    when not provided in context. Risk calculation uses no other external APIs.
    """
    context = state.get("context") or {}
    entities = state.get("entities") or {}
    plot_id = context.get("plot_id") or entities.get("plot_id")
    if not plot_id:
        return {
            "analysis": {
                "agent": "pest_risk",
                "plot_id": None,
                "error": "Missing frontend risk calculation inputs",
            }
        }

    auth_token = context.get("auth_token")
    api = get_api_service(auth_token)

    # Use context/entities if provided; otherwise fetch from APIs (same as frontend)
    plantation_date = context.get("plantation_date") or entities.get("plantation_date")
    if not plantation_date or not isinstance(plantation_date, str) or not plantation_date.strip():
        plantation_date = await _fetch_plantation_date(api, plot_id)

    current_conditions = _ensure_current_conditions(
        context.get("current_conditions") or entities.get("current_conditions")
    )
    if not current_conditions.get("month"):
        current_conditions = await _fetch_current_conditions(api, plot_id)

    pest_detection_data = context.get("pest_detection_data") or entities.get("pest_detection_data")
    if not pest_detection_data or not isinstance(pest_detection_data, dict):
        pest_detection_data = await _fetch_pest_detection_data(api, plot_id)
    else:
        pest_detection_data = _ensure_pest_detection(pest_detection_data)

    result = generate_risk_assessment(
        plantation_date=plantation_date.strip(),
        current_conditions=current_conditions,
        pest_detection_data=pest_detection_data,
    )

    analysis = {
        "agent": "pest_risk",
        "plot_id": plot_id,
        "risk_assessment": result,
        "high_risk_weeds": result.get("weeds", {}).get("high", []),
        "moderate_risk_weeds": result.get("weeds", {}).get("moderate", []),
        "low_risk_weeds": result.get("weeds", {}).get("low", []),
    }
    return {"analysis": analysis}
