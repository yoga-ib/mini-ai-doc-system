from app.langgraph_state import GraphState

def answer_agent(state: GraphState) -> GraphState:
    context = state.get("context", [])

    if not context:
        state["answer"] = "No relevant information found in the document."
        return state

    # Simple answer generation (Day-3 scope)
    combined_context = " ".join(context)
    state["answer"] = combined_context

    return state