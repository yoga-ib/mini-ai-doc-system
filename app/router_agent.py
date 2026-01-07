from app.langgraph_state import GraphState


def router_agent(state: GraphState) -> GraphState:
    question = state["question"].lower()

    keywords = [
        "document",
        "file",
        "policy",
        "content",
        "mentioned",
        "objective",
        "describe",
        "explain"
    ]

    needs_retrieval = any(word in question for word in keywords)

    state["needs_retrieval"] = needs_retrieval
    return state
