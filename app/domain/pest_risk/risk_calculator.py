# app/domain/pest_risk/risk_calculator.py
# Replicates frontend pestt logic exactly. No external API. No formula changes.

from typing import Any, Dict, List, Optional

# --- Data: same as frontend pestsData (fields used for risk only) ---
PESTS_DATA: List[Dict[str, Any]] = [
    {"name": "Early shoot borer", "months": ["April", "May", "June", "July"], "stage": {"minDays": 0, "maxDays": 120}, "category": "chewing"},
    {"name": "Top shoot borer", "months": ["January", "February", "March", "April"], "stage": {"minDays": 46, "maxDays": 210}, "category": "chewing"},
    {"name": "Root borer", "months": ["April", "May", "June", "July", "August", "September", "October"], "stage": {"minDays": 0, "maxDays": 45}, "category": "chewing"},
    {"name": "Internode borer", "months": ["October", "November", "December"], "stage": {"minDays": 121, "maxDays": 365}, "category": "chewing"},
    {"name": "White grub", "months": ["May", "June", "July", "August", "September"], "stage": {"minDays": 46, "maxDays": 365}, "category": "soil_borne"},
    {"name": "Termites", "months": ["September", "October", "November", "December", "January", "February", "March", "April", "May"], "stage": {"minDays": 0, "maxDays": 365}, "category": "soil_borne"},
    {"name": "Whitefly", "months": ["May", "June", "July", "August", "September", "October"], "stage": {"minDays": 121, "maxDays": 210}, "category": "sucking"},
    {"name": "Sugarcane woolly aphids", "months": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], "stage": {"minDays": 121, "maxDays": 365}, "category": "sucking"},
    {"name": "Sugarcane pyrilla", "months": ["February", "March"], "stage": {"minDays": 121, "maxDays": 365}, "category": "sucking"},
    {"name": "Mealy bug", "months": ["February", "March", "September", "October", "November", "December"], "stage": {"minDays": 121, "maxDays": 365}, "category": "sucking"},
    {"name": "Sugarcane scale insect", "months": ["March", "April", "May", "June", "July", "August", "September", "October"], "stage": {"minDays": 46, "maxDays": 365}, "category": "sucking"},
]

# --- Data: same as frontend diseasesData (only Red Rot and Rust use fungi %) ---
DISEASES_DATA: List[Dict[str, Any]] = [
    {"name": "Red Rot", "months": ["July", "August", "September", "October", "November"], "stage": {"minDays": 121, "maxDays": 365}},
    {"name": "Rust", "months": ["August", "September", "October", "November", "December"], "stage": {"minDays": 46, "maxDays": 365}},
    {"name": "Smut", "months": ["February", "March", "April", "May", "June"], "stage": {"minDays": 0, "maxDays": 120}},
    {"name": "Grassy Shoot", "months": ["February", "March", "April", "May"], "stage": {"minDays": 90, "maxDays": 120}},
    {"name": "Wilt", "months": ["July", "August", "September", "October"], "stage": {"minDays": 121, "maxDays": 365}},
    {"name": "Ratoon Stunting Disease (RSD)", "months": ["February", "March", "April", "May", "June", "July", "August", "September", "October", "November"], "stage": {"minDays": 0, "maxDays": 365}},
    {"name": "Leaf Scald", "months": ["March", "April", "May", "June", "July", "August"], "stage": {"minDays": 90, "maxDays": 300}},
    {"name": "Downy Mildew", "months": ["June", "July", "August"], "stage": {"minDays": 121, "maxDays": 210}},
]

# --- Data: same as frontend Weeds.ts (full records for high-risk weeds display) ---
WEEDS_DATA: List[Dict[str, Any]] = [
    {"name": "Hariali (Cynodon dactylon)", "months": ["February", "March", "April", "May"], "when": "Perennial, flushes in warm months", "where": "Irrigated fields, bunds, canals", "why": "Aggressive competitor, spreads via stolons & rhizomes, hard to control", "image": "/Image/hariyali.jpg", "chemical": ["Fenoxaprop-p-ethyl 9.3% EC - 400 ml/acre in 150–200 l water"]},
    {"name": "Congress Grass (Parthenium hysterophorus)", "months": ["February", "March", "April", "May"], "when": "Germinates with first rains", "where": "Roadsides, waste lands, also in cane fields", "why": "Allelopathic, fast spreading, causes worker allergies", "image": "/Image/congress grass.jpg", "chemical": ["2,4-D Sodium Salt 80% WP - 500–750 gm/acre in 150–200 l water"]},
    {"name": "Rajgira (Amaranthus spp.)", "months": ["June", "July", "August", "September"], "when": "Emerges in rainy season", "where": "Fertile, irrigated cane fields", "why": "Fast-growing broadleaf, competes for light & nutrients", "image": "/Image/Amaranthus spp.jpg", "chemical": ["Atrazine 50% WP - 500 gm/acre in 150–200 l water"]},
    {"name": "Bathua (Chenopodium album)", "months": ["October", "November", "December", "January"], "when": "Germinates in winter (low temp)", "where": "Northern India, fertile irrigated lands", "why": "Competes during early cane growth, reduces tillering", "image": "/Image/bathua.jpg", "chemical": ["2,4-D Sodium Salt 80% WP - 600–700 gm/acre in 150–200 l water"]},
]

# --- Sugarcane stages: same as frontend riskAssessmentService SUGARCANE_STAGES ---
SUGARCANE_STAGES = [
    {"name": "Germination & Early Growth", "minDays": 0, "maxDays": 45},
    {"name": "Tillering & Early Stem Elongation", "minDays": 46, "maxDays": 120},
    {"name": "Grand Growth Phase", "minDays": 121, "maxDays": 210},
    {"name": "Ripening & Maturity", "minDays": 211, "maxDays": 365},
]


def _normalize_month(month: Optional[str]) -> str:
    return (month or "").strip().lower()


def calculate_days_since_plantation(plantation_date: str) -> int:
    """Same as frontend calculateDaysSincePlantation."""
    from datetime import datetime
    try:
        # Support YYYY-MM-DD
        parts = plantation_date.strip().split("-")
        if len(parts) == 3:
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            plantation = datetime(y, m, d)
        else:
            plantation = datetime.strptime(plantation_date.strip(), "%Y-%m-%d")
    except Exception:
        return 0
    today = datetime.utcnow()
    delta = today - plantation
    return max(0, delta.days)


def calculate_sugarcane_stage(plantation_date: str) -> str:
    """Same as frontend calculateSugarcaneStage."""
    days = calculate_days_since_plantation(plantation_date)
    for stage in SUGARCANE_STAGES:
        if stage["minDays"] <= days <= stage["maxDays"]:
            return stage["name"]
    return "Ripening & Maturity"


def _assess_pest_risk(
    pest: Dict[str, Any],
    days_since_plantation: int,
    current_month: str,
    pest_detection_data: Dict[str, float],
) -> Optional[str]:
    """
    Same as frontend assessPestRisk.
    Returns 'High' or None. Frontend only uses High; Moderate/Low are never set.
    """
    category = pest.get("category")
    if not category:
        return None

    api_percentage = 0.0
    if category == "chewing":
        api_percentage = pest_detection_data.get("chewing_affected_pixel_percentage") or 0
    elif category == "sucking":
        api_percentage = pest_detection_data.get("sucking_affected_pixel_percentage") or 0
    elif category == "soil_borne":
        api_percentage = pest_detection_data.get("SoilBorn_affected_pixel_percentage") or 0

    if api_percentage == 0:
        return None

    stage_match = True
    if pest.get("stage"):
        s = pest["stage"]
        stage_match = s["minDays"] <= days_since_plantation <= s["maxDays"]

    current_month_norm = _normalize_month(current_month)
    pest_months_norm = [_normalize_month(m) for m in pest.get("months") or []]
    month_match = current_month_norm in pest_months_norm

    if api_percentage > 0 and stage_match and month_match:
        return "High"
    return None


def _assess_disease_risk(
    disease: Dict[str, Any],
    days_since_plantation: int,
    current_month: str,
    pest_detection_data: Dict[str, float],
) -> Optional[str]:
    """
    Same as frontend assessDiseaseRisk.
    Only Red Rot and Rust are fungal; only they use fungi_affected_pixel_percentage.
    Returns 'High' or None.
    """
    fungi_percentage = pest_detection_data.get("fungi_affected_pixel_percentage") or 0
    is_fungal = disease.get("name") in ("Red Rot", "Rust")
    if fungi_percentage == 0 or not is_fungal:
        return None

    stage_match = True
    if disease.get("stage"):
        s = disease["stage"]
        stage_match = s["minDays"] <= days_since_plantation <= s["maxDays"]

    current_month_norm = _normalize_month(current_month)
    disease_months_norm = [_normalize_month(m) for m in disease.get("months") or []]
    month_match = current_month_norm in disease_months_norm

    if fungi_percentage > 0 and stage_match and month_match:
        return "High"
    return None


def _matches_current_month_weed(weed: Dict[str, Any], current_month_lower: str) -> bool:
    """Same as frontend matchesCurrentMonth (weedRiskUtils)."""
    months = weed.get("months") or []
    if not months:
        return False
    return any(_normalize_month(m) == current_month_lower for m in months)


def categorize_weeds_by_season(
    weeds: Optional[List[Dict[str, Any]]] = None,
    current_month_lower: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Same as frontend categorizeWeedsBySeason (weedRiskUtils).
    Returns { "high": [...], "moderate": [...], "low": [...] } with full weed objects.
    """
    from datetime import datetime
    weeds = weeds if weeds is not None else WEEDS_DATA
    if current_month_lower is None:
        # Same as frontend: toLocaleString('en-US', { month: 'long' }).toLowerCase()
        current_month_lower = datetime.utcnow().strftime("%B").lower()

    seasonal = [w for w in weeds if _matches_current_month_weed(w, current_month_lower)]

    if seasonal:
        remaining = [w for w in weeds if w not in seasonal]
        moderate = remaining[: min(1, len(remaining))]
        low = remaining[len(moderate) :]
        return {"high": seasonal, "moderate": moderate, "low": low}

    return {
        "high": weeds[: min(2, len(weeds))],
        "moderate": weeds[2 : min(3, len(weeds))],
        "low": weeds[3:],
    }


def generate_risk_assessment(
    plantation_date: str,
    current_conditions: Dict[str, Any],
    pest_detection_data: Dict[str, float],
    current_month_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    current_conditions: { "month": str, "temperature": number, "humidity": number }
    pest_detection_data: {
      fungi_affected_pixel_percentage, chewing_affected_pixel_percentage,
      sucking_affected_pixel_percentage, SoilBorn_affected_pixel_percentage
    }
    """
    days_since_plantation = calculate_days_since_plantation(plantation_date)
    current_stage = calculate_sugarcane_stage(plantation_date)
    month = (current_month_override or current_conditions.get("month") or "").strip()
    if not month and not current_month_override:
        from datetime import datetime
        month = datetime.utcnow().strftime("%B")

    result: Dict[str, Any] = {
        "stage": current_stage,
        "current_conditions": {
            "month": month,
            "temperature": f"{current_conditions.get('temperature', 0)}°C",
            "humidity": f"{current_conditions.get('humidity', 0)}%",
        },
        "pests": {"High": [], "Moderate": [], "Low": []},
        "diseases": {"High": [], "Moderate": [], "Low": []},
        "weeds": {"high": [], "moderate": [], "low": []},
    }

    active_categories = []
    if (pest_detection_data.get("chewing_affected_pixel_percentage") or 0) > 0:
        active_categories.append("chewing")
    if (pest_detection_data.get("sucking_affected_pixel_percentage") or 0) > 0:
        active_categories.append("sucking")
    if (pest_detection_data.get("SoilBorn_affected_pixel_percentage") or 0) > 0:
        active_categories.append("soil_borne")

    for pest in PESTS_DATA:
        if not pest.get("category") or pest["category"] not in active_categories:
            continue
        level = _assess_pest_risk(pest, days_since_plantation, month, pest_detection_data)
        if level == "High":
            result["pests"]["High"].append(pest["name"])

    has_fungi = (pest_detection_data.get("fungi_affected_pixel_percentage") or 0) > 0
    if has_fungi:
        for disease in DISEASES_DATA:
            level = _assess_disease_risk(disease, days_since_plantation, month, pest_detection_data)
            if level == "High":
                result["diseases"]["High"].append(disease["name"])

    current_month_lower = _normalize_month(month)
    weed_buckets = categorize_weeds_by_season(WEEDS_DATA, current_month_lower)
    result["weeds"] = weed_buckets

    return result
