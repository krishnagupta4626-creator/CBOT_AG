from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String(64), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    emotional_state_summary = Column(String(255), nullable=True)

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    guardrail_logs = relationship("GuardrailLog", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    sender = Column(Enum("user", "assistant", "system", name="sender_enum"), nullable=False)
    content_text = Column(Text, nullable=True)
    modality = Column(Enum("text", "image", "audio", "document", name="modality_enum"), default="text")
    media_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


class GuardrailLog(Base):
    __tablename__ = "guardrail_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False, index=True)
    trigger_type = Column(String(64), nullable=False)  # 'crisis_self_harm', 'pii_leak', 'toxic_content', 'prompt_injection'
    detected_phrase = Column(Text, nullable=True)
    action_taken = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="guardrail_logs")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    doc_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, default="general_mental_health")
    chunk_index = Column(Integer, nullable=False, default=0)
    chunk_text = Column(Text, nullable=False)
    embedding_json = Column(Text, nullable=True)  # JSON-serialized list of floats
    created_at = Column(DateTime, default=datetime.utcnow)
