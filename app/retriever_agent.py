from sqlalchemy.orm import Session
from app.langgraph_state import GraphState
from app.embeddings import create_embedding
from app.pinecone_client import index
from app.models import DocumentChunk, Document
from app.database import SessionLocal


def retriever_agent(state: GraphState) -> GraphState:
    query = state["question"]

    query_embedding = create_embedding(query)
    if not query_embedding:
        state["context"] = []
        return state

    db: Session = SessionLocal()

    try:
        # 🔹 Get latest uploaded document
        latest_doc = db.query(Document).order_by(Document.uploaded_at.desc()).first()

        if not latest_doc:
            state["context"] = []
            return state

        # 🔹 IMPORTANT FIX: namespace = document_id
        search_result = index.query(
            vector=query_embedding,
            top_k=5,
            namespace=str(latest_doc.id),   # ✅ THIS IS THE KEY FIX
            include_metadata=True
        )

        matches = search_result.get("matches", [])
        chunks = []

        for match in matches:
            vector_id = match["id"]
            chunk = db.query(DocumentChunk).filter(
                DocumentChunk.vector_id == vector_id
            ).first()

            if chunk:
                chunks.append(chunk.chunk_text)

        state["context"] = chunks
        return state

    finally:
        db.close()
