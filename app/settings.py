import os

DATABASE_URL = os.environ.get("DATABASE_URL")

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


HF_EMBED_MODEL = r"all-MiniLM-L6-v2"

PINECONE_API_KEY = "pcsk_5YueeH_74nrFRY1FKSgN7KvoswoXHAUEU5qtcTDuuFfqYb5tbiMeTNC2fEmtCvvsCQibfK"

PINECONE_HOST = "https://mini-ai-index-1dh48uz.svc.aped-4627-b74a.pinecone.io"
PINECONE_INDEX_NAME = "mini-ai-index"


#Yoga-ib1126
