from typing import Any, Dict, List, Optional, Tuple

from app.services.api_service import get_api_service
from app.domain.fertilizer.schedule import (
    generate_7_day_schedule,
    calculate_months_since_plantation,
    PLANTATION_TYPE_MONTHS,
)


def _get_plot_farm_from_profile(profile: Dict[str, Any], plot_id: str) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Resolve plot and first farm from farmer profile (same structure as pest_agent).
    Handles profile.plots or profile.data.plots; matches by fastapi_plot_id, plot_name, or gat_number_plot_number.
    Returns (plot, farm) or (None, None).
    """
    if not profile or "error" in profile:
        return None, None
    plots: List[Dict] = profile.get("plots") or profile.get("data", {}).get("plots") or []
    for plot in plots:
        pid = (
            plot.get("fastapi_plot_id")
            or plot.get("plot_name")
            or (f"{plot.get('gat_number', '')}_{plot.get('plot_number', '')}")
        )
        if str(pid) != str(plot_id):
            continue
        farms = plot.get("farms") or []
        if not farms:
            return plot, None
        return plot, farms[0]
    return None, None


async def fertilizer_agent(state: dict) -> dict:
    """
    Fertilizer Agent
    - Fetches NPK requirements
    - Generates 7-day fertilizer schedule
    - Respects 'No Fertilizer Required' logic
    """

    context = state.get("context", {})
    plot_id = context.get("plot_id")
    auth_token = context.get("auth_token")

    if not plot_id:
        state["analysis"] = {
            "fertilizer": {
                "error": "plot_id missing"
            }
        }
        return state

    api = get_api_service(auth_token)

    # -------------------------------------------------
    # 1️⃣ Fetch farmer profile (same pattern as pest_agent)
    # -------------------------------------------------
    profile = await api.get_farmer_profile()
    plot, farm = _get_plot_farm_from_profile(profile, plot_id)

    if not plot:
        if "error" in profile:
            state["analysis"] = {"fertilizer": profile}
        else:
            state["analysis"] = {"fertilizer": {"error": "Plot or farm data not found"}}
        return state

    if not farm:
        state["analysis"] = {
            "fertilizer": {"error": "No farm data found for this plot"}
        }
        return state

    plantation_date = farm.get("plantation_date") or farm.get("plantation_Date")
    crop_type = farm.get("crop_type") or {}

    plantation_type = crop_type.get("plantation_type") or crop_type.get("plantation_type_display")
    planting_method = crop_type.get("planting_method") or crop_type.get("planting_method_display")

    if not all([plantation_date, plantation_type, planting_method]):
        state["analysis"] = {
            "fertilizer": {
                "error": "Incomplete farm data (plantation_date / plantation_type / planting_method)"
            }
        }
        return state

    # -------------------------------------------------
    # 2️⃣ Check if fertilizer is still required
    # -------------------------------------------------
    months_completed = calculate_months_since_plantation(plantation_date)

    normalized_type = plantation_type.lower().replace("-", "").replace(" ", "")
    required_months = next(
        (
            v for k, v in PLANTATION_TYPE_MONTHS.items()
            if k.replace("-", "").replace(" ", "") == normalized_type
        ),
        None
    )

    if required_months and months_completed >= required_months:
        state["analysis"] = {
            "fertilizer": {
                "no_fertilizer_required": True,
                "months_completed": months_completed,
                "required_months": required_months
            }
        }
        return state

    # -------------------------------------------------
    # 3️⃣ Generate fertilizer schedule (CORE LOGIC)
    # -------------------------------------------------
    try:
        schedule = generate_7_day_schedule(
            plantation_date=plantation_date,
            planting_method=planting_method
        )
    except Exception as e:
        state["analysis"] = {
            "fertilizer": {
                "error": f"Failed to generate fertilizer schedule: {str(e)}"
            }
        }
        return state

    npk = await api.get_npk_requirements(plot_id)
    npk_data = {}
    if "error" not in npk:
        npk_data = {
            "plantanalysis_n": npk.get("plantanalysis_n"),
            "plantanalysis_p": npk.get("plantanalysis_p"),
            "plantanalysis_k": npk.get("plantanalysis_k"),
        }
    else:
        npk_data = {"error": npk["error"]}

    state["analysis"] = {
        "fertilizer": {
            "no_fertilizer_required": False,
            "npk": npk_data,
            "schedule": schedule,
        }
    }

    return state
