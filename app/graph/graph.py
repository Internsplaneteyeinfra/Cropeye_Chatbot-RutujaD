from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph.router import router

from app.agents.language_detector import language_detector
from app.agents.intent_analyzer import intent_analyzer

from app.agents.soil_analysis_agent import soil_analysis_agent
from app.agents.soil_moisture_agent import soil_moisture_agent
from app.agents.weather_agent import weather_agent
from app.agents.map_agent import map_agent
from app.agents.pest_agent import pest_agent
from app.agents.irrigation_agent import irrigation_agent
from app.agents.fertilizer_agent import fertilizer_agent

from app.agents.response_generator import response_generator

def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("language_detector", language_detector)
    graph.add_node("intent_analyzer", intent_analyzer)

    graph.add_node("soil_analysis_agent", soil_analysis_agent)
    graph.add_node("soil_moisture_agent", soil_moisture_agent)
    graph.add_node("weather_agent", weather_agent)
    graph.add_node("map_agent", map_agent)
    graph.add_node("pest_agent", pest_agent)
    graph.add_node("irrigation_agent", irrigation_agent)
    graph.add_node("fertilizer_agent", fertilizer_agent)
    graph.add_node("response_generator", response_generator)


    # Set entry point
    graph.set_entry_point("language_detector")

    graph.add_edge("language_detector", "intent_analyzer")
    graph.add_conditional_edges(
        "intent_analyzer",
        router,
        {
            "soil_analysis_agent": "soil_analysis_agent",
            "soil_moisture_agent": "soil_moisture_agent",
            "weather_agent": "weather_agent",
            "map_agent": "map_agent",
            "pest_agent": "pest_agent",
            "irrigation_agent": "irrigation_agent",
            "fertilizer_agent": "fertilizer_agent",
            "response_generator": "response_generator"
        }
    )
    
    graph.add_edge("soil_analysis_agent", "response_generator")
    graph.add_edge("soil_moisture_agent", "response_generator")
    graph.add_edge("weather_agent", "response_generator")
    graph.add_edge("map_agent", "response_generator")
    graph.add_edge("pest_agent", "response_generator")
    graph.add_edge("irrigation_agent", "response_generator")
    graph.add_edge("fertilizer_agent", "response_generator")
    graph.add_edge("response_generator", END)

    return graph.compile()
