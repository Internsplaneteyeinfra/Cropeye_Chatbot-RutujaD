from typing import Any, Optional
from app.services.api_service import get_api_service

# Optimal ranges (same as dashboard logic)
SOIL_OPTIMAL_RANGES = {
    "nitrogen": {"min": 50, "max": 150, "unit": "Kg/acre"},
    "phosphorus": {"min": 25, "max": 75, "unit": "Kg/acre"},
    "potassium": {"min": 20, "max": 100, "unit": "Kg/acre"},
    "pH": {"min": 6.2, "max": 7.5, "unit": ""},
    "cec": {"min": 15, "max": 40, "unit": "C mol/Kg"},
    "organic_carbon": {"min": 2, "max": 15, "unit": "T/acre"},
    "bulk_density": {"min": 0.50, "max": 1.60, "unit": "Kg/m³"},
    "fe": {"min": 4.5, "max": 10, "unit": "ppm"},
    "soc": {"min": 1.5, "max": 3.5, "unit": "%"}
}

def get_parameter_status(value: float, param: str) -> str:
    if value is None or param not in SOIL_OPTIMAL_RANGES:
        return "Unknown"
    r = SOIL_OPTIMAL_RANGES[param]
    if value < r["min"]:
        return "Low"
    elif value > r["max"]:
        return "Very High"
    else:
        return "Optimal"

async def soil_analysis_agent(state: dict) -> dict:
    """
    Handles:
    - Single parameter soil query
    - Full soil analysis report
    """

    context = state.get("context") or {}
    entities = state.get("entities") or {}

    plot_id = context.get("plot_id") or entities.get("plot_id") or "369_12"
    date = entities.get("date")

    auth_token = state.get("auth_token")
    api_service = get_api_service(auth_token)

    # ---- CALL APIs ----
    analyze_data = await api_service.get_soil_analysis(
        plot_name=plot_id,
        date=date
    )

    required_n_data = await api_service.get_npk_requirements(
        plot_name=plot_id,
        end_date=date
    )

    # ---- LOG FOR CROSS CHECK ----
    print("\n=== SOIL ANALYSIS DEBUG ===")
    print("Plot:", plot_id)
    print("Analyze API:", analyze_data)
    print("Required-N API:", required_n_data)
    print("==========================\n")

    if "error" in analyze_data:
        state["analysis"] = analyze_data
        return state

    # ---- EXTRACT STATISTICS ----
    stats = (
        analyze_data.get("features", [{}])[0]
        .get("properties", {})
        .get("statistics", {})
    )

    # ---- FINAL VALUES (DASHBOARD LOGIC) ----
    soil_report = {
        "nitrogen": {
            "value": required_n_data.get("soilN"),
            "unit": "Kg/acre",
            "status": get_parameter_status(required_n_data.get("soilN"), "nitrogen")
        },
        "phosphorus": {
            "value": required_n_data.get("soilP"),
            "unit": "Kg/acre",
            "status": get_parameter_status(required_n_data.get("soilP"), "phosphorus")
        },
        "potassium": {
            "value": required_n_data.get("soilK"),
            "unit": "Kg/acre",
            "status": get_parameter_status(required_n_data.get("soilK"), "potassium")
        },
        "pH": {
            "value": stats.get("phh2o"),
            "unit": "",
            "status": get_parameter_status(stats.get("phh2o"), "pH")
        },
        "cec": {
            "value": stats.get("cation_exchange_capacity"),
            "unit": "C mol/Kg",
            "status": get_parameter_status(stats.get("cation_exchange_capacity"), "cec")
        },
        "organic_carbon": {
            "value": stats.get("organic_carbon_stock"),
            "unit": "T/acre",
            "status": get_parameter_status(stats.get("organic_carbon_stock"), "organic_carbon")
        },
        "bulk_density": {
            "value": stats.get("bulk_density"),
            "unit": "Kg/m³",
            "status": get_parameter_status(stats.get("bulk_density"), "bulk_density")
        },
        "fe": {
            "value": stats.get("fe_ppm_estimated"),
            "unit": "ppm",
            "status": get_parameter_status(stats.get("fe_ppm_estimated"), "fe")
        },
        "soc": {
            "value": stats.get("soil_organic_carbon"),
            "unit": "%",
            "status": get_parameter_status(stats.get("soil_organic_carbon"), "soc")
        }
    }

    state["analysis"] = {
        "agent": "soil_analysis",
        "plot_id": plot_id,
        "report_type": "full_soil_analysis",
        "parameters": soil_report
    }

    return state
