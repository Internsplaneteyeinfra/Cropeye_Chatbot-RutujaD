from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.agents.language_detector import language_detector
from app.agents.intent_analyzer import intent_analyzer
from app.agents.response_generator import response_generator


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("language_detector", language_detector)
    graph.add_node("intent_analyzer", intent_analyzer)
    graph.add_node("response_generator", response_generator)

    graph.set_entry_point("language_detector")
    graph.add_edge("language_detector", "intent_analyzer")
    graph.add_edge("intent_analyzer", "response_generator")
    graph.add_edge("response_generator", END)

    return graph.compile()