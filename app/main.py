from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import shutil
import os
import uuid

from app.database import Base, engine, SessionLocal
from app.models import Document, DocumentChunk
from app.settings import UPLOAD_FOLDER
from app.utils import extract_text, chunk_text
from app.embeddings import create_embedding
from app.pinecone_client import index
from app import schemas

# LangGraph imports
from app.langgraph_flow import langgraph_app
from app.langgraph_state import GraphState


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini AI Document Query System")


# ---------------- DB Dependency ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"message": "RAG application started!"}

# ---------------- Health ----------------
@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------- List Documents ----------------
@app.get("/documents", response_model=list[schemas.DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).order_by(Document.uploaded_at.desc()).all()


# ---------------- Upload Document ----------------
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filename = os.path.basename(file.filename)
    ext = filename.split(".")[-1].lower()

    if ext not in ["pdf", "txt"]:
        raise HTTPException(status_code=400, detail="Only PDF or TXT files allowed")

    save_path = os.path.join(UPLOAD_FOLDER, filename)
    base, extension = os.path.splitext(save_path)
    counter = 1
    while os.path.exists(save_path):
        save_path = f"{base}_{counter}{extension}"
        counter += 1

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if ext == "pdf":
            text = extract_text(save_path)
        else:
            with open(save_path, "r", encoding="utf-8") as f:
                text = f.read()
    except Exception as e:
        os.remove(save_path)
        raise HTTPException(status_code=500, detail=str(e))

    if not text.strip():
        os.remove(save_path)
        raise HTTPException(status_code=400, detail="No extractable text found")

    document = Document(
        filename=os.path.basename(save_path),
        filepath=save_path,
        status="uploaded"
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = chunk_text(text)

    for i, chunk in enumerate(chunks):
        embedding = create_embedding(chunk)
        if not embedding:
            continue

        vector_id = f"{document.id}_{i}_{uuid.uuid4()}"

        index.upsert(
            vectors=[{
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "document_id": document.id,
                    "chunk_index": i
                }
            }],
            namespace=str(document.id)
        )

        db_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=i,
            chunk_text=chunk,
            vector_id=vector_id
        )
        db.add(db_chunk)

    db.commit()

    return {
        "message": "Uploaded and indexed successfully",
        "document_id": document.id,
        "chunks_created": len(chunks)
    }


# ---------------- Ask (LangGraph Driven) ----------------
@app.post("/ask")
def ask_question(query: str):
    state: GraphState = {
        "question": query,
        "needs_retrieval": False,
        "context": [],
        "answer": ""
    }

    final_state = langgraph_app.invoke(state)

    return {
        "query": query,
        "answer": final_state.get("answer", ""),
        "context": final_state.get("context", [])
    }
