#app/domain/fertilizer/schedule.py

# import json
# from datetime import datetime, timedelta
# from pathlib import Path

# BUD_PATH = Path(__file__).parent / "bud.json"

# with open(BUD_PATH, "r", encoding="utf-8") as f:
#     BUD_DATA = json.load(f)

# PLANTATION_TYPE_MONTHS = {
#     "suru": 10,
#     "adsali": 14,
#     "preseasonal": 12,
#     "ratoon": 9,
# }

# def normalize(value: str) -> str:
#     return (
#         value.lower()
#         .strip()
#         .replace("_", "-")
#         .replace(" ", "-")
#     )

# # def calculate_days_since_plantation(plantation_date: str) -> int:
# #     plantation = datetime.fromisoformat(plantation_date)
# #     today = datetime.now()
# #     return max((today - plantation).days, 0)


# def calculate_days_since_plantation(plantation_date: str) -> int:

#     if not plantation_date or not isinstance(plantation_date, str):
#         raise ValueError("Invalid plantation_date")

#     try:
#         plantation = datetime.fromisoformat(
#             plantation_date.replace("Z", "+00:00")
#         )
#     except Exception:
#         raise ValueError("plantation_date must be ISO format YYYY-MM-DD")

#     today = datetime.now(plantation.tzinfo)
#     return max((today - plantation).days, 0)


# def calculate_months_since_plantation(plantation_date: str) -> int:
#     plantation = datetime.fromisoformat(plantation_date)
#     today = datetime.now()

#     months = (today.year - plantation.year) * 12 + (today.month - plantation.month)
#     if today.day < plantation.day:
#         months -= 1

#     return max(months, 0)

# # def get_stage_for_day(days: int, stages: list) -> dict:
# #     for stage in stages:
# #         start, end = stage["days"].replace("–", "-").split("-")
# #         if int(start) <= days <= int(end):
# #             return stage
# #     return stages[-1]

# def get_stage_for_day(days: int, stages: list) -> dict:
#     for stage in stages:
#         start, end = stage["days"].replace("–", "-").split("-")
#         if int(start) <= days <= int(end):
#             return stage

#     raise ValueError(f"No fertilizer stage defined for day {days}")


# def generate_7_day_schedule(plantation_date: str, planting_method: str):
#     method = normalize(planting_method)

#     schedule = next(
#         (
#             s for s in BUD_DATA["fertilizer_schedule"]
#             if normalize(s["method"]) == method
#         ),
#         None
#     )

#     if not schedule:
#         raise ValueError(f"No fertilizer schedule for planting method: {planting_method}")

#     days_since = calculate_days_since_plantation(plantation_date)
#     today = datetime.now()

#     result = []

#     for i in range(7):
#         target_day = days_since + i
#         target_date = today + timedelta(days=i)
#         stage = get_stage_for_day(target_day, schedule["stages"])

#         result.append({
#             "date": target_date.strftime("%d/%m/%Y"),
#             "stage": stage["stage"],
#             "days": target_day,
#             "N_kg_acre": stage["N_kg_acre"],
#             "P_kg_acre": stage["P_kg_acre"],
#             "K_kg_acre": stage["K_kg_acre"],
#             "fertilizers": stage["fertilizers"],
#             "organic_inputs": stage["organic_inputs"],
#         })

#     return result


import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any

# =====================================================
# LOAD BUD DATA
# =====================================================

BUD_PATH = Path(__file__).parent / "bud.json"

with open(BUD_PATH, "r", encoding="utf-8") as f:
    BUD_DATA = json.load(f)

# =====================================================
# CONSTANTS
# =====================================================

PLANTATION_TYPE_MONTHS = {
    "suru": 10,
    "adsali": 14,
    "preseasonal": 12,
    "ratoon": 9,
}

# =====================================================
# SHARED VALIDATION HELPERS
# =====================================================

def _require_string(value: Any, name: str) -> str:
    if not value or not isinstance(value, str):
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _parse_iso_date(date_str: str) -> datetime:
    date_str = _require_string(date_str, "plantation_date")

    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        raise ValueError("plantation_date must be ISO format YYYY-MM-DD")


def _normalize(value: str) -> str:
    return value.lower().strip().replace("_", "-").replace(" ", "-")


# =====================================================
# DATE CALCULATIONS
# =====================================================

def calculate_days_since_plantation(plantation_date: str) -> int:
    plantation = _parse_iso_date(plantation_date)
    today = datetime.now(plantation.tzinfo)
    return max((today - plantation).days, 0)


def calculate_months_since_plantation(plantation_date: str) -> int:
    plantation = _parse_iso_date(plantation_date)
    today = datetime.now(plantation.tzinfo)

    months = (today.year - plantation.year) * 12 + (today.month - plantation.month)

    if today.day < plantation.day:
        months -= 1

    return max(months, 0)


# =====================================================
# STAGE RESOLUTION
# =====================================================

def _get_stage_for_day(days: int, stages: list) -> Dict:
    for stage in stages:
        start, end = stage["days"].replace("–", "-").split("-")

        if int(start) <= days <= int(end):
            return stage

    raise ValueError(f"No fertilizer stage defined for day {days}")


def _get_schedule_by_method(method: str) -> Dict:
    method = _normalize(_require_string(method, "planting_method"))

    schedule = next(
        (
            s for s in BUD_DATA["fertilizer_schedule"]
            if _normalize(s["method"]) == method
        ),
        None
    )

    if not schedule:
        raise ValueError(f"No fertilizer schedule for planting method: {method}")

    return schedule


# =====================================================
# MAIN SCHEDULE GENERATOR
# =====================================================

def generate_7_day_schedule(
    plantation_date: str,
    planting_method: str
) -> list:

    # Resolve schedule definition
    schedule_def = _get_schedule_by_method(planting_method)

    # Calculate days since plantation
    days_since = calculate_days_since_plantation(plantation_date)

    today = datetime.now()
    result = []

    for i in range(7):

        target_day = days_since + i
        target_date = today + timedelta(days=i)

        stage = _get_stage_for_day(
            target_day,
            schedule_def["stages"]
        )

        result.append({
            "date": target_date.strftime("%d/%m/%Y"),
            "stage": stage["stage"],
            "days": target_day,
            "N_kg_acre": stage["N_kg_acre"],
            "P_kg_acre": stage["P_kg_acre"],
            "K_kg_acre": stage["K_kg_acre"],
            "fertilizers": stage["fertilizers"],
            "organic_inputs": stage["organic_inputs"],
        })

    return result
