from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph.router import router

from app.agents.language_detector import language_detector
from app.agents.intent_analyzer import intent_analyzer
from app.agents.soil_analysis_agent import soil_analysis_agent
from app.agents.soil_moisture_agent import soil_moisture_agent
from app.agents.weather_agent import weather_agent

from app.agents.response_generator import response_generator

def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("language_detector", language_detector)
    graph.add_node("intent_analyzer", intent_analyzer)

    graph.add_node("soil_analysis_agent", soil_analysis_agent)
    graph.add_node("soil_moisture_agent", soil_moisture_agent)
    graph.add_node("weather_agent", weather_agent)

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
            "response_generator": "response_generator"
        }
    )
    
    graph.add_edge("soil_analysis_agent", "response_generator")
    graph.add_edge("soil_moisture_agent", "response_generator")
    graph.add_edge("weather_agent", "response_generator")
    graph.add_edge("response_generator", END)

    return graph.compile()
