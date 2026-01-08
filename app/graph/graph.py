from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.agents.language_detector import language_detector
from app.agents.intent_analyzer import intent_analyzer
from app.agents.response_generator import response_generator
from app.agents.farm_context_agent import farm_context_agent
from app.agents.soil_analysis_agent import soil_analysis_agent
from app.graph.router import router

def build_graph():
    graph = StateGraph(GraphState)

    # Add all nodes
    graph.add_node("language_detector", language_detector)
    graph.add_node("intent_analyzer", intent_analyzer)
    graph.add_node("farm_context_agent", farm_context_agent)
    graph.add_node("soil_analysis_agent", soil_analysis_agent)
    graph.add_node("response_generator", response_generator)

    # Set entry point
    graph.set_entry_point("language_detector")
    
    # Add edges
    graph.add_edge("language_detector", "intent_analyzer")
    
    # Route from intent analyzer
    graph.add_conditional_edges(
        "intent_analyzer",
        router,
        {
            "farm_context_agent": "farm_context_agent",
            "soil_analysis_agent": "soil_analysis_agent",
            "response_generator": "response_generator"
        }
    )
    
    # After farm context, route again based on intent
    graph.add_conditional_edges(
        "farm_context_agent",
        router,
        {
            "soil_analysis_agent": "soil_analysis_agent",
            "irrigation_agent": "response_generator",  # Placeholder - will be implemented later
            "pest_agent": "response_generator",  # Placeholder
            "yield_agent": "response_generator",  # Placeholder
            "crop_health_agent": "response_generator",  # Placeholder
            "weather_agent": "response_generator",  # Placeholder
            "response_generator": "response_generator"
        }
    )
    
    # After soil analysis, go to response generator
    graph.add_edge("soil_analysis_agent", "response_generator")
    
    # Final response
    graph.add_edge("response_generator", END)

    return graph.compile()
