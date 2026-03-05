# # app/agents/pest_agent.py

from datetime import datetime
from typing import Any, Dict

from app.domain.pest_risk.risk_calculator import generate_risk_assessment


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


async def pest_agent(state: dict) -> dict:
    """
    Same logic as original.
    Only change:
    DATA SOURCE → cache instead of API
    """

    context = state.get("context") or {}
    entities = state.get("entities") or {}
    cached = context.get("cached_data") or {}

    plot_id = context.get("plot_id") or entities.get("plot_id")

    if not plot_id:
        return {
            "analysis": {
                "agent": "pest_risk",
                "plot_id": None,
                "error": "Missing frontend risk calculation inputs",
            }
        }

    # plantation date
    plantation_date = context.get("plantation_date") or entities.get("plantation_date")

    if not plantation_date or not isinstance(plantation_date, str) or not plantation_date.strip():
        profile = cached.get("farmer_profile") or {}

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
                        plantation_date = pd.strip()
                break

    # weather
    current_conditions = _ensure_current_conditions(
        context.get("current_conditions") or entities.get("current_conditions")
    )

    if not current_conditions.get("month"):

        weather = cached.get("current_weather")

        if weather and isinstance(weather, dict):

            try:
                temp = float(weather.get("temperature_c", weather.get("temperature")))
            except (TypeError, ValueError):
                temp = None

            try:
                humidity = float(weather.get("humidity"))
            except (TypeError, ValueError):
                humidity = None

            current_conditions = {
                "month": datetime.utcnow().strftime("%B"),
                "temperature": temp,
                "humidity": humidity,
            }

    # pest detection
    pest_detection_data = context.get("pest_detection_data") or entities.get("pest_detection_data")

    if not pest_detection_data or not isinstance(pest_detection_data, dict):

        pest_cached = cached.get("pest_detection")

        if pest_cached and isinstance(pest_cached, dict):

            ps = pest_cached.get("pixel_summary") or {}

            pest_detection_data = {
                "fungi_affected_pixel_percentage":
                    float(ps.get("fungi_affected_pixel_percentage"))
                    if ps.get("fungi_affected_pixel_percentage") is not None else None,

                "chewing_affected_pixel_percentage":
                    float(ps.get("chewing_affected_pixel_percentage"))
                    if ps.get("chewing_affected_pixel_percentage") is not None else None,

                "sucking_affected_pixel_percentage":
                    float(ps.get("sucking_affected_pixel_percentage"))
                    if ps.get("sucking_affected_pixel_percentage") is not None else None,

                "SoilBorn_affected_pixel_percentage":
                    float(ps.get("SoilBorn_affected_pixel_percentage"))
                    if ps.get("SoilBorn_affected_pixel_percentage") is not None else None,
            }

        else:
            pest_detection_data = _empty_pest_detection()

    else:
        pest_detection_data = _ensure_pest_detection(pest_detection_data)

    result = generate_risk_assessment(
        plantation_date=plantation_date,
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

    state["analysis"] = analysis
    return state