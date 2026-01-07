from pydantic import BaseModel
from datetime import datetime

class DocumentOut(BaseModel):
    id: int
    filename: str
    filepath: str
    uploaded_at: datetime
    status: str

    class Config:
        from_attributes = True   # Pydantic v2 version of orm_mode