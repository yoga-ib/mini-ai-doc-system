from pinecone import Pinecone
from app.settings import PINECONE_API_KEY, PINECONE_HOST, PINECONE_INDEX_NAME

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(host=PINECONE_HOST)

def upsert_vector(vector_id: str, embedding: list, metadata: dict):
    index.upsert(
        vectors=[
            {
                "id": vector_id,
                "values": embedding,
                "metadata": metadata
            }
        ]
    )
