from typing import Dict

from app.services.api_service import get_api_service
from app.services.farm_context_service import get_farm_context
from app.domain.fertilizer.schedule import (
    generate_7_day_schedule,
    calculate_months_since_plantation,
    PLANTATION_TYPE_MONTHS,
)


async def fertilizer_agent(state: dict) -> dict:

    context = state.get("context", {})
    plot_id = context.get("plot_id")
    auth_token = context.get("auth_token")

    if not plot_id:
        state["analysis"] = {"fertilizer": {"error": "plot_id missing"}}
        return state

    # =====================================================
    # FARM CONTEXT (single source of truth)
    # =====================================================
    farm = await get_farm_context(
        plot_name=plot_id,
        auth_token=auth_token
    )

    if farm.get("error"):
        state["analysis"] = {"fertilizer": farm}
        return state

    plantation_date = farm.get("plantation_date")
    plantation_type = farm.get("plantation_type")
    planting_method = farm.get("planting_method")

    # ❗ STRICT VALIDATION (NO DEFAULTS)
    if not plantation_date:
        state["analysis"] = {"fertilizer": {"error": "plantation_date missing"}}
        return state

    if not plantation_type:
        state["analysis"] = {"fertilizer": {"error": "plantation_type missing"}}
        return state

    if not planting_method:
        state["analysis"] = {"fertilizer": {"error": "planting_method missing"}}
        return state

    # =====================================================
    # CHECK IF FERTILIZER STILL REQUIRED
    # =====================================================
    months_completed = calculate_months_since_plantation(plantation_date)

    normalized_type = plantation_type.lower().replace("-", "").replace(" ", "")
    required_months = next(
        (
            v for k, v in PLANTATION_TYPE_MONTHS.items()
            if k.replace("-", "").replace(" ", "") == normalized_type
        ),
        None
    )

    if required_months is None:
        state["analysis"] = {
            "fertilizer": {"error": f"Unknown plantation_type: {plantation_type}"}
        }
        return state

    if months_completed >= required_months:
        state["analysis"] = {
            "fertilizer": {
                "no_fertilizer_required": True,
                "months_completed": months_completed,
                "required_months": required_months
            }
        }
        return state

    # =====================================================
    # GENERATE SCHEDULE
    # =====================================================
    try:
        schedule = generate_7_day_schedule(
            plantation_date=plantation_date,
            planting_method=planting_method
        )
    except Exception as e:
        state["analysis"] = {
            "fertilizer": {"error": f"Schedule generation failed: {str(e)}"}
        }
        return state

    # =====================================================
    # NPK REQUIREMENTS
    # =====================================================
    api = get_api_service(auth_token)
    npk = await api.get_npk_requirements(plot_id)

    npk_data: Dict = (
        {
            "plantanalysis_n": npk.get("plantanalysis_n"),
            "plantanalysis_p": npk.get("plantanalysis_p"),
            "plantanalysis_k": npk.get("plantanalysis_k"),
        }
        if "error" not in npk
        else {"error": npk["error"]}
    )

    # =====================================================
    # FINAL OUTPUT
    # =====================================================
    state["analysis"] = {
        "fertilizer": {
            "no_fertilizer_required": False,
            "npk": npk_data,
            "schedule": schedule,
        }
    }

    return state
