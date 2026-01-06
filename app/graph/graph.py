from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.agents.language_detector import language_detector
from app.agents.intent_analyzer import intent_analyzer


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("language_detector", language_detector)
    graph.add_node("intent_analyzer", intent_analyzer)

    graph.set_entry_point("language_detector")
    graph.add_edge("language_detector", "intent_analyzer")
    graph.add_edge("intent_analyzer", END)

    return graph.compile()