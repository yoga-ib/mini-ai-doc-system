# embeddings.py
from sentence_transformers import SentenceTransformer

# Load model once globally
model = SentenceTransformer('all-MiniLM-L6-v2')

def create_embedding(text: str):
    """
    Generate embeddings for the given text using local sentence-transformers model.
    Returns a list of floats.
    """
    try:
        if not text.strip():
            return None
        # Convert numpy array to list
        return model.encode(text).tolist()
    except Exception as e:
        print("EMBEDDING ERROR:", e)
        return None
