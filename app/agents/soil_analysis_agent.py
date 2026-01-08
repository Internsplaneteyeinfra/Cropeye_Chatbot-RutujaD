"""
Soil Analysis Agent
Handles all soil-related queries (N, P, K, pH, CEC, OC, BD, Fe, SOC)
"""

from typing import Dict, Any, Optional
from app.services.api_service import get_api_service


# Optimal ranges for soil parameters (from frontend logic)
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

# Parameter name mappings
PARAMETER_MAPPING = {
    "n": "nitrogen",
    "nitrogen": "nitrogen",
    "p": "phosphorus",
    "phosphorus": "phosphorus",
    "k": "potassium",
    "potassium": "potassium",
    "ph": "pH",
    "pH": "pH",
    "cec": "cec",
    "cation exchange capacity": "cec",
    "oc": "organic_carbon",
    "organic carbon": "organic_carbon",
    "bd": "bulk_density",
    "bulk density": "bulk_density",
    "fe": "fe",
    "iron": "fe",
    "soc": "soc",
    "soil organic carbon": "soc"
}


def get_parameter_status(value: float, param_name: str) -> str:
    """
    Determine status: Very Low, Low, Medium, Optimal, Very High
    """
    if param_name not in SOIL_OPTIMAL_RANGES:
        return "Unknown"
    
    optimal = SOIL_OPTIMAL_RANGES[param_name]
    min_val = optimal["min"]
    max_val = optimal["max"]
    range_size = max_val - min_val
    
    if value < min_val - (range_size * 0.5):
        return "Very Low"
    elif value < min_val:
        return "Low"
    elif value <= max_val:
        return "Optimal"
    elif value <= max_val + (range_size * 0.5):
        return "High"
    else:
        return "Very High"


def format_parameter_value(value: Any, param_name: str) -> Optional[float]:
    """
    Format and extract parameter value from API response
    """
    if value is None:
        return None
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


async def soil_analysis_agent(state: dict) -> dict:
    """
    Soil Analysis Agent
    Handles soil-related queries
    """
    # Get context
    context = state.get("context", {})
    plot_id = context.get("plot_id")
    
    if not plot_id:
        state["analysis"] = {
            "error": "Plot ID not found. Please specify a plot.",
            "agent": "soil_analysis"
        }
        return state
    
    # Get entities
    entities = state.get("entities", {})
    parameter = entities.get("parameter")
    date = entities.get("date")
    
    # Get API service
    auth_token = state.get("auth_token")
    api_service = get_api_service(auth_token)
    
    # Fetch soil analysis
    soil_data = await api_service.get_soil_analysis(
        plot_name=plot_id,
        date=date
    )
    
    if "error" in soil_data:
        state["analysis"] = {
            "error": soil_data["error"],
            "agent": "soil_analysis"
        }
        return state
    
    # Extract statistics from response
    # Response format: {features: [{properties: {statistics: {...}}}]}
    statistics = {}
    
    if "features" in soil_data and len(soil_data["features"]) > 0:
        statistics = soil_data["features"][0].get("properties", {}).get("statistics", {})
    elif "statistics" in soil_data:
        statistics = soil_data["statistics"]
    elif isinstance(soil_data, dict):
        statistics = soil_data
    
    # If parameter is specified, return only that parameter
    if parameter:
        param_lower = parameter.lower()
        param_key = PARAMETER_MAPPING.get(param_lower)
        
        if not param_key:
            state["analysis"] = {
                "error": f"Unknown parameter: {parameter}",
                "agent": "soil_analysis"
            }
            return state
        
        # Get value from statistics
        value = None
        
        # Try different possible keys
        possible_keys = [
            param_key,
            param_key.replace("_", ""),
            param_key.upper(),
            param_key.lower()
        ]
        
        for key in possible_keys:
            if key in statistics:
                value = statistics[key]
                break
        
        # Special handling for some parameters
        if param_key == "nitrogen" and value is None:
            value = statistics.get("total_nitrogen")
        if param_key == "organic_carbon" and value is None:
            value = statistics.get("organic_carbon_stock")
        if param_key == "fe" and value is None:
            value = statistics.get("fe_ppm_estimated")
        
        if value is None:
            state["analysis"] = {
                "error": f"Parameter {parameter} not found in soil data",
                "agent": "soil_analysis"
            }
            return state
        
        formatted_value = format_parameter_value(value, param_key)
        if formatted_value is None:
            state["analysis"] = {
                "error": f"Invalid value for parameter {parameter}",
                "agent": "soil_analysis"
            }
            return state
        
        optimal = SOIL_OPTIMAL_RANGES.get(param_key, {})
        status = get_parameter_status(formatted_value, param_key)
        
        state["analysis"] = {
            "agent": "soil_analysis",
            "parameter": param_key,
            "value": formatted_value,
            "unit": optimal.get("unit", ""),
            "optimal_range": {
                "min": optimal.get("min"),
                "max": optimal.get("max")
            },
            "status": status,
            "plot_id": plot_id
        }
    else:
        # Return all parameters
        all_params = {}
        
        for param_key, optimal in SOIL_OPTIMAL_RANGES.items():
            value = None
            
            # Try different possible keys
            possible_keys = [
                param_key,
                param_key.replace("_", ""),
                param_key.upper(),
                param_key.lower()
            ]
            
            for key in possible_keys:
                if key in statistics:
                    value = statistics[key]
                    break
            
            # Special handling
            if param_key == "nitrogen" and value is None:
                value = statistics.get("total_nitrogen")
            if param_key == "organic_carbon" and value is None:
                value = statistics.get("organic_carbon_stock")
            if param_key == "fe" and value is None:
                value = statistics.get("fe_ppm_estimated")
            
            if value is not None:
                formatted_value = format_parameter_value(value, param_key)
                if formatted_value is not None:
                    all_params[param_key] = {
                        "value": formatted_value,
                        "unit": optimal.get("unit", ""),
                        "optimal_range": {
                            "min": optimal.get("min"),
                            "max": optimal.get("max")
                        },
                        "status": get_parameter_status(formatted_value, param_key)
                    }
        
        state["analysis"] = {
            "agent": "soil_analysis",
            "parameters": all_params,
            "plot_id": plot_id
        }
    
    return state
