import json
import math
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Literal, Tuple

from app.services.api_service import get_api_service
from app.services.farm_context_service import get_farm_context

# =====================================================
# LOAD bud.json (same KC source as frontend)
# =====================================================

# BUD_PATH = Path(__file__).parent / "bud.json"

# if BUD_PATH.exists():
#     BUD_DATA = json.loads(BUD_PATH.read_text(encoding="utf-8"))
# else:
#     print("[IRRIGATION WARNING] bud.json not found. Using fallback KC values.")
#     BUD_DATA = {}


# =====================================================
# HELPERS
# =====================================================

def _parse_rainfall_value(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(" mm", "").replace(",", ".")
    try:
        return float(s) if s else 0.0
    except:
        return 0.0


# def _get_plot_farm_from_profile(profile: Any, plot_id: str):
#     if not profile or isinstance(profile, dict) and "error" in profile:
#         return None, None

#     plots = profile if isinstance(profile, list) else profile.get("plots") or profile.get("data", {}).get("plots") or []

#     for p in plots:
#         pid = p.get("fastapi_plot_id") or f"{p.get('gat_number','')}_{p.get('plot_number','')}"
#         if str(pid) == str(plot_id):
#             farms = p.get("farms") or []
#             return p, (farms[0] if farms else None)

#     return None, None


# =====================================================
# FRONTEND IDENTICAL KC LOGIC
# =====================================================

# def _get_crop_stage(days: int) -> str:
#     if days > 210:
#         return "Maturity & Ripening"
#     elif days > 90:
#         return "Grand Growth"
#     elif days > 30:
#         return "Tillering"
#     return "Germination"


# def _kc_from_stage(stage: str) -> float:
#     kc_value = 0.3

#     for method in BUD_DATA.get("fertilizer_schedule", []):
#         for st in method.get("stages", []):
#             if st.get("stage") == stage:
#                 try:
#                     kc_value = float(st.get("kc", kc_value))
#                 except:
#                     pass

#     return kc_value


# def _derive_kc_from_plantation_date(plantation_date: str) -> float:
#     try:
#         plant_dt = datetime.fromisoformat(str(plantation_date).replace("Z", "+00:00"))
#         now = datetime.now(plant_dt.tzinfo or timezone.utc)
#         days = max(0, (now - plant_dt).days)
#     except:
#         return 0.37

#     stage = _get_crop_stage(days)
#     print("Plantation date =", plantation_date)
#     print("Days from plantation =", days)
#     print("Derived stage =", stage)
#     print("KC from bud.json =", _kc_from_stage(stage))

#     return _kc_from_stage(stage)


# =====================================================
# MAIN CLASS
# =====================================================

class IrrigationSchedule:

    EFFICIENCY = 0.94
    # ACRE_TO_SQM = 4046.86

    def __init__(self, auth_token=None):
        self.api = get_api_service(auth_token)
        self.auth_token = auth_token

    # -----------------------------
    # ET range
    # -----------------------------
    @staticmethod
    def get_et_range(et: float) -> Literal["Low", "Medium", "High"]:
        if et <= 3.0:
            return "Low"
        if et <= 5.5:
            return "Medium"
        return "High"

    # -----------------------------
    # Net ET
    # -----------------------------
    def calculate_net_et(self, et, rainfall):
        return max(0, et - rainfall)


    # -----------------------------
    # Water calculation (plot area based)
    # -----------------------------
    def calculate_water_required(self, net_et, kc):
        if net_et <= 0 or kc <= 0:
            return 0

        # area_sqm = area_hectares * 10000
        # liters = net_et * kc * self.EFFICIENCY
        liters = net_et * kc * 0.94 * 4046.86

        return round(liters)

    # -----------------------------
    # Deterministic ET prediction
    # -----------------------------
    @staticmethod
    def generate_adjusted_et(base_et, plot_id):

        effective_base = base_et if base_et > 0 else 2.5

        seed = sum(ord(c) for c in plot_id) + datetime.now().day
        random_seed = seed

        def rnd():
            nonlocal random_seed
            random_seed = (random_seed * 9301 + 49297) % 233280
            return random_seed / 233280

        candidate_days = [0,1,2,3,4,5]
        num_medium = 2 + int(rnd()*2)
        medium_days = []

        for _ in range(num_medium):
            idx = int(rnd()*len(candidate_days))
            medium_days.append(candidate_days.pop(idx))

        predictions = []

        for i in range(6):

            is_medium = i in medium_days

            if effective_base <= 3:
                val = (3.2 + rnd()*1.8) if is_medium else (2.0 + rnd()*0.9)
            elif effective_base <= 5.5:
                val = (3.5 + rnd()*1.5) if is_medium else (2.3 + rnd()*0.7)
            else:
                val = (5.5 + rnd()) if is_medium else (3.0 + rnd()*0.8)

            val = max(val*(0.95 + rnd()*0.10), 1.5)
            predictions.append(round(val,1))

        return predictions

    # -----------------------------
    # Flood time
    # -----------------------------
    @staticmethod
    def format_time(hours):
        if not hours or hours <= 0:
            return "0 hrs 0 mins"
        h = int(hours)
        m = round((hours-h)*60)
        return f"{h} hrs {m} mins"

    def calculate_flood_time(self, water, hp, pipe_in, distance=None):
        if not water or not hp or not pipe_in:
            return None

        diameter_m = pipe_in * 0.0254
        area = math.pi * (diameter_m/2)**2
        velocity = max(0.75, min(2.5, hp*0.45))

        if distance:
            velocity *= max(0.5, 1 - (distance/100)*0.05)

        flow_lph = area * velocity * 3600 * 1000
        if flow_lph <= 0:
            return None

        return self.format_time(water/flow_lph)


    # =====================================================
    # BUILD SCHEDULE
    # =====================================================

    async def build(self, plot_id: str):

        # ✅ SINGLE SOURCE OF TRUTH FOR KC
        farm_context = await get_farm_context(
            plot_name=plot_id,
            auth_token=self.auth_token
        )

        # if kc is missing, raise error
        if farm_context.get("error"):
            print("[FARM CONTEXT ERROR] =", farm_context["error"])

        kc = farm_context.get("kc")

        if kc is None:
            print("[FARM CONTEXT ERROR] KC value missing from farm context")

        print("\n[FARM CONTEXT]")
        print("KC =", kc)
        print("Stage =", farm_context.get("crop_stage"))
        print("Plantation =", farm_context.get("plantation_date"))

        # ------------------------------------------------

        weather_today = await self.api.get_current_weather(plot_id)
        forecast = await self.api.get_weather_forecast(plot_id)
        et_data = await self.api.get_evapotranspiration(plot_id)

        print("\n========== ET API DEBUG ==========")
        print("Plot ID =", plot_id)
        print("Raw ET response =", et_data)
        print("Type =", type(et_data))
        print("==================================")

        print("\n[IRRIGATION DEBUG]")
        # print("Area hectares =", area_hectares)

        base_et = (
            et_data.get("et_24hr")
            or et_data.get("ET_mean_mm_per_day")
            or et_data.get("et")            
        )        
        if not base_et or base_et <= 0:
            print("Evapotranspiration data not available")


        print("Base ET =", base_et)

        today_rain = _parse_rainfall_value(weather_today.get("precip_mm"))
        forecast_list = forecast.get("data", []) if forecast else []
        next_6_et = self.generate_adjusted_et(base_et, plot_id)

        today = datetime.now().date()
        schedule = []

        for i in range(7):

            date = today + timedelta(days=i)

            if i == 0:
                et = base_et
                rain = today_rain
            else:
                et = next_6_et[i-1]
                fc = forecast_list[i-1] if i-1 < len(forecast_list) else {}
                rain = _parse_rainfall_value(fc.get("precip_mm"))

            net = self.calculate_net_et(et, rain)
            water = self.calculate_water_required(net, kc)

            print("Water required =", water)

            schedule.append({
                "date": date.strftime("%d %b"),
                "is_today": i == 0,
                "et_value": round(et,1),
                "et_range": self.get_et_range(et),
                "rainfall_mm": round(rain,1),
                "net_et": round(net,2),
                "water_required_liters": water,
                "flood_time": "N/A"
            })

        return schedule