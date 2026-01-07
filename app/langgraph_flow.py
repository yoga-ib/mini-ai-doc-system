from langgraph.graph import StateGraph, END

from app.langgraph_state import GraphState
from app.router_agent import router_agent
from app.retriever_agent import retriever_agent
from app.answer_agent import answer_agent


# Create LangGraph with state
graph = StateGraph(GraphState)

# Add agents as nodes
graph.add_node("router", router_agent)
graph.add_node("retriever", retriever_agent)
graph.add_node("answer", answer_agent)

# Entry point
graph.set_entry_point("router")


# Router decision function
def route_decision(state: GraphState):
    if state.get("needs_retrieval"):
        return "retriever"
    return "answer"


# Conditional routing
graph.add_conditional_edges(
    "router",
    route_decision,
    {
        "retriever": "retriever",
        "answer": "answer",
    }
)

# Normal flow
graph.add_edge("retriever", "answer")
graph.add_edge("answer", END)

# Compile graph
langgraph_app = graph.compile()
