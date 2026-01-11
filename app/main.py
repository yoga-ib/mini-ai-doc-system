from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import shutil
import os
import uuid
import tempfile
import os
import shutil
import ast
from dotenv import load_dotenv 

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

# Cloud Database imports 
from supabase import create_client, Client

# LLm imports
from transformers import pipeline
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer

load_dotenv() 

embed_model = SentenceTransformer("all-MiniLM-L6-v2")  # lightweight and fast

llm = pipeline("text2text-generation", model="google/flan-t5-large", max_length=512)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mini AI Document Query System")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase : Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def parse_embedding(embedding_str):
    """
    Convert string embedding from Supabase to numpy array
    """
    # Safely parse the string list into Python list
    embedding_list = ast.literal_eval(embedding_str)
    # Convert to numpy float array
    return np.array(embedding_list, dtype=np.float32)

def embed_query(text: str):
    return embed_model.encode(text)

def get_top_k_chunks(query_embedding, k=5):

    data = supabase.table("documents_vectors").select("*").execute()
    chunks = data.data

    similarities = []
    query_vec = np.array(query_embedding, dtype=np.float32)

    for chunk in chunks:
        # Parse embedding string into numeric array
        vector = parse_embedding(chunk["embedding"])

        # Cosine similarity
        sim = np.dot(query_vec, vector) / (np.linalg.norm(query_vec) * np.linalg.norm(vector))
        similarities.append((sim, chunk))

    similarities.sort(reverse=True, key=lambda x: x[0])
    return [c for _, c in similarities[:k]]



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
    safe_filename = filename.replace(" ", "_")
    ext = safe_filename.split(".")[-1].lower()

    if ext not in ["pdf", "txt"]:
        raise HTTPException(400, "Only PDF or TXT files allowed")

    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        shutil.copyfileobj(file.file, tmp)
        temp_path = tmp.name

    try:
        if ext == "pdf":
            text = extract_text(temp_path)
        else:
            with open(temp_path, "r", encoding="utf-8") as f:
                text = f.read()
    except Exception as e:
        os.remove(temp_path)
        raise HTTPException(500, f"Text extraction failed: {e}")

    if not text.strip():
        os.remove(temp_path)
        raise HTTPException(400, "No extractable text found")

    # Upload to Supabase Storage (correct way)
    with open(temp_path, "rb") as f:
        supabase.storage.from_("documents").upload(
            safe_filename,
            f,
            {"content-type": file.content_type}
        )

    file_url = supabase.storage.from_("documents").get_public_url(safe_filename)

    # Save document metadata
    document = Document(
        filename=safe_filename,
        filepath=file_url,
        status="uploaded"
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    chunks = chunk_text(text)
    created_chunks = 0

    for i, chunk in enumerate(chunks):
        embedding = create_embedding(chunk)
        if not embedding:
            continue

        # Supabase vector table
        supabase.table("documents_vectors").insert({
            "id": str(uuid.uuid4()),
            "document_id": document.id,
            "chunk_index": i,
            "content": chunk,
            "embedding": embedding
        }).execute()

        # Local DB chunk table
        db_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=i,
            chunk_text=chunk
        )
        db.add(db_chunk)
        created_chunks += 1

    db.commit()
    os.remove(temp_path)

    return {
        "message": "Uploaded and indexed successfully",
        "document_id": document.id,
        "chunks_created": created_chunks,
        "file_url": file_url
    }


class QueryRequest(BaseModel):
    query: str

@app.post("/ask")
def ask_question(request: QueryRequest):
    query = request.query

    query_embedding = embed_model.encode(query).astype(np.float32)


    top_chunks = get_top_k_chunks(query_embedding, k=5)
    context_text = "\n\n".join([c["content"] for c in top_chunks])

    prompt = f"Answer the question based on the context below:\n\nContext:\n{context_text}\n\nQuestion: {query}\nAnswer:"

    answer = llm(prompt)[0]["generated_text"]

    return {
        "query": query,
        "answer": answer,
        "context": [c["content"] for c in top_chunks]
    }
