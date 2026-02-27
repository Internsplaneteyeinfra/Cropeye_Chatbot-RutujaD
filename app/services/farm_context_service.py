# app/services/farm_context_service.py

"""
Farm Context Service
Extracts and manages farm context (plot, crop, plantation date, etc.)
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from app.services.api_service import get_api_service
import json
from pathlib import Path

BUD_PATH = Path("app/domain/irrigation/bud.json")

if BUD_PATH.exists():
    BUD_DATA = json.loads(BUD_PATH.read_text(encoding="utf-8"))
else:
    raise ValueError("bud.json not found — KC calculation cannot run")

def get_stage(days):
    if days > 210:
        return "Maturity & Ripening"
    elif days > 90:
        return "Grand Growth"
    elif days > 30:
        return "Tillering"
    return "Germination"

def get_kc(stage):
    for method in BUD_DATA.get("fertilizer_schedule", []):
        for st in method.get("stages", []):
            if st["stage"] == stage:
                return float(st["kc"])
    raise ValueError(f"KC not found in bud.json for stage {stage}")


def calculate_crop_stage(plantation_date: str, current_date=None):

    if not current_date:
        current_date = datetime.now().strftime("%Y-%m-%d")

    plant_dt = datetime.strptime(plantation_date, "%Y-%m-%d")
    curr_dt = datetime.strptime(current_date, "%Y-%m-%d")

    days = max(0, (curr_dt - plant_dt).days)
    stage = get_stage(days)
    kc = get_kc(stage)

    return {
        "stage": stage,
        "days_since_plantation": days,
        "kc": kc
    }


def _derive_kc_from_plantation_date(plantation_date: str) -> float:

    plant_dt = datetime.fromisoformat(
        str(plantation_date).replace("Z", "+00:00")
    )

    now = datetime.now(plant_dt.tzinfo or timezone.utc)

    days = max(0, (now - plant_dt).days)

    stage = _get_crop_stage(days)

    kc = _kc_from_stage(stage)

    print("\n===== KC CALCULATION (FRONTEND MATCH) =====")
    print("Plantation date:", plantation_date)
    print("Days:", days)
    print("Stage:", stage)
    print("KC:", kc)

    return kc, stage, days

async def get_farm_context(
    plot_name: Optional[str] = None,
    user_id: Optional[int] = None,
    auth_token: Optional[str] = None
) -> Dict[str, Any]:

    if not plot_name:
        return {"error": "Plot name is required"}

    # ---------- CACHE FARM CONTEXT PER PLOT TO AVOID RE-PARSING ----------
    from app.memory.redis_manager import redis_manager
    cache_key = f"farm_context:{plot_name}"
    cached_context = redis_manager.get(cache_key)
    
    if cached_context and not cached_context.get("error"):
        return cached_context

    api_service = get_api_service(auth_token)
    profile_data = await api_service.get_public_plots()

    if "error" in profile_data:
        return {"error": profile_data["error"]}

    plots = profile_data.get("results", [])

    selected_plot = None

    for plot in plots:
        pid = plot.get("fastapi_plot_id")

        if str(pid) == str(plot_name):
            selected_plot = plot
            break

    if not selected_plot:
        return {"error": f"Plot {plot_name} not found"}

    farms = selected_plot.get("farms", [])

    if not farms:
        return {"error": "No farm data found for this plot"}

    farm = farms[0]
    plantation_date = farm.get("plantation_date")
    plantation_type = farm.get("plantation_type")
    planting_method = farm.get("planting_method")

    # ---------- DISABLE VERBOSE LOGGING FOR PERFORMANCE ----------
    # print("PLANTATION DATE =", plantation_date)
    # print("PLANTATION TYPE =", plantation_type)
    # print("PLANTATION METHOD =", planting_method)

    if not plantation_date:
        return {"error": "Plantation date missing"}

    crop_stage_info = calculate_crop_stage(plantation_date)

    # print("KC_CALCULATED =", crop_stage_info["kc"])

    location = selected_plot.get("location", {}).get("coordinates", [])

    lon = location[0] if len(location) >= 2 else None
    lat = location[1] if len(location) >= 2 else None

    farm_context = {
        "plot_id": plot_name,
        "plantation_date": plantation_date,
        "crop_stage": crop_stage_info["stage"],
        "days_since_plantation": crop_stage_info["days_since_plantation"],
        "plantation_type": plantation_type,
        "planting_method": planting_method,
        "kc": crop_stage_info["kc"],
        "lat": lat,
        "lon": lon,
        "error": None
    }
    
    # ---------- CACHE FARM CONTEXT FOR 24 HOURS ----------
    redis_manager.set(cache_key, farm_context, ttl=86400)
    
    return farm_context