from typing import TypedDict, List


class GraphState(TypedDict):
    question: str
    needs_retrieval: bool
    context: List[str]
    answer: str
