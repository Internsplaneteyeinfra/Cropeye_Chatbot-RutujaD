# app/graph/graph.py
from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph.router import router

from app.agents.unified_agent import unified_agent

from app.agents.soil_analysis_agent import soil_analysis_agent
from app.agents.soil_moisture_agent import soil_moisture_agent
from app.agents.weather_agent import weather_agent
from app.agents.map_agent import map_agent
from app.agents.pest_agent import pest_agent
from app.agents.irrigation_agent import irrigation_agent
from app.agents.fertilizer_agent import fertilizer_agent
from app.agents.dashboard_agent import dashboard_agent

def build_graph():
    graph = StateGraph(GraphState)

    # Unified agent handles both intent detection and response generation
    graph.add_node("unified_agent", unified_agent)

    graph.add_node("soil_analysis_agent", soil_analysis_agent)
    graph.add_node("soil_moisture_agent", soil_moisture_agent)
    graph.add_node("weather_agent", weather_agent)
    graph.add_node("map_agent", map_agent)
    graph.add_node("pest_agent", pest_agent)
    graph.add_node("irrigation_agent", irrigation_agent)
    graph.add_node("fertilizer_agent", fertilizer_agent)
    graph.add_node("dashboard_agent", dashboard_agent)

    # Set entry point to unified agent (intent detection mode)
    graph.set_entry_point("unified_agent")
    
    # Route based on detected intent
    # If final_response is already set (general_explanation case handled in unified_agent), go to END
    # Otherwise, route to domain agents
    def route_after_intent(state: dict) -> str:
        if state.get("final_response"):
            return END
        return router(state)
    
    graph.add_conditional_edges(
        "unified_agent",
        route_after_intent,
        {
            "soil_analysis_agent": "soil_analysis_agent",
            "soil_moisture_agent": "soil_moisture_agent",
            "weather_agent": "weather_agent",
            "map_agent": "map_agent",
            "pest_agent": "pest_agent",
            "irrigation_agent": "irrigation_agent",
            "fertilizer_agent": "fertilizer_agent",
            "dashboard_agent": "dashboard_agent",
            "unified_agent": "unified_agent",  # For general_explanation (shouldn't happen, but safe fallback)
            END: END
        }
    )
    
    # All domain agents route back to unified agent (response generation mode)
    graph.add_edge("soil_analysis_agent", "unified_agent")
    graph.add_edge("soil_moisture_agent", "unified_agent")
    graph.add_edge("weather_agent", "unified_agent")
    graph.add_edge("map_agent", "unified_agent")
    graph.add_edge("pest_agent", "unified_agent")
    graph.add_edge("irrigation_agent", "unified_agent")
    graph.add_edge("fertilizer_agent", "unified_agent")
    graph.add_edge("dashboard_agent", "unified_agent")
    
    # Unified agent (response generation mode) always ends the graph
    graph.add_edge("unified_agent", END)

    return graph.compile()
