from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="uploaded")

    # One-to-many: Document → Chunks
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    # One-to-many: Document → Vectors
    vectors = relationship(
        "DocumentVector",
        back_populates="document",
        cascade="all, delete-orphan"
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer)
    chunk_text = Column(Text)
    vector_id = Column(String, ForeignKey("documents_vectors.id", ondelete="SET NULL"), unique=True)

    document = relationship("Document", back_populates="chunks")
    vector = relationship("DocumentVector", back_populates="chunk", uselist=False)


class DocumentVector(Base):
    __tablename__ = "documents_vectors"

    id = Column(String, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer)
    content = Column(Text)
    embedding = Column(Text)

    document = relationship("Document", back_populates="vectors")
    chunk = relationship("DocumentChunk", back_populates="vector", uselist=False)