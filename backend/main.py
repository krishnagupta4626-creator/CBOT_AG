import os
import uuid
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pypdf import PdfReader

from backend.config import settings
from backend.database import init_db, get_db, DB_ENGINE_TYPE
from backend.models import ChatSession, ChatMessage
from backend.guardrails import GuardrailEngine
from backend.rag_engine import RAGEngine
from backend.gemini_service import GeminiService
from backend.tts_service import TTSService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("emopal.api")

app = FastAPI(
    title="EmoPal - Multimodal Emotional Support API",
    description="FastAPI backend for EmoPal Multimodal RAG Chatbot with Guardrails & MySQL persistence.",
    version="1.0.0"
)

# CORS middleware for Streamlit integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount audio cache directory
app.mount("/audio", StaticFiles(directory=str(settings.AUDIO_DIR)), name="audio")

# Initialize services
gemini_service = GeminiService()
rag_engine = RAGEngine(gemini_client=gemini_service.client)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing database schema...")
    init_db()
    # Ingest default knowledge documents
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        rag_engine.ingest_directory(db)
    finally:
        db.close()
    logger.info("EmoPal Backend startup complete.")

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "EmoPal Multimodal API",
        "database_type": DB_ENGINE_TYPE,
        "gemini_active": gemini_service.client is not None,
        "model": settings.GEMINI_MODEL
    }

@app.post("/api/session")
def create_session(db: Session = Depends(get_db)):
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    session = ChatSession(session_id=session_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return {"session_id": session.session_id, "created_at": session.created_at}

@app.get("/api/history/{session_id}")
def get_history(session_id: str, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return [
        {
            "sender": m.sender,
            "content_text": m.content_text,
            "modality": m.modality,
            "media_url": m.media_url,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]

@app.post("/api/chat")
async def chat_multimodal(
    session_id: str = Form(...),
    prompt: Optional[str] = Form(""),
    generate_audio: Optional[bool] = Form(True),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    document: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Multimodal Chat Endpoint:
    Processes user text, image, audio, or document inputs through Guardrails, RAG, and Gemini.
    """
    # 1. Ensure session exists
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        session = ChatSession(session_id=session_id)
        db.add(session)
        db.commit()

    # 2. Extract Document Content if uploaded
    document_text = None
    if document:
        try:
            doc_bytes = await document.read()
            if document.filename.lower().endswith(".pdf"):
                # Extract text using PyPDF
                import io
                pdf_reader = PdfReader(io.BytesIO(doc_bytes))
                extracted_pages = [page.extract_text() for page in pdf_reader.pages if page.extract_text()]
                document_text = "\n".join(extracted_pages)[:4000]
            else:
                document_text = doc_bytes.decode("utf-8", errors="ignore")[:4000]
        except Exception as e:
            logger.error(f"Error reading document upload: {e}")

    # Read Image and Audio bytes
    image_bytes = await image.read() if image else None
    image_mime = image.content_type if image else "image/png"

    audio_bytes = await audio.read() if audio else None
    audio_mime = audio.content_type if audio else "audio/wav"

    # Determine input modality
    modality = "text"
    if image_bytes:
        modality = "image"
    elif audio_bytes:
        modality = "audio"
    elif document_text:
        modality = "document"

    # 3. Guardrail Pre-Inference Checks
    combined_input_text = f"{prompt or ''} {document_text or ''}".strip()
    guardrail_result = GuardrailEngine.process_input(combined_input_text, session_id, db=db)

    # Save user message to database
    user_msg = ChatMessage(
        session_id=session_id,
        sender="user",
        content_text=prompt or "(Multimodal attachment shared)",
        modality=modality
    )
    db.add(user_msg)
    db.commit()

    # 4. Handle Guardrail Interception (Crisis or Injection)
    if guardrail_result["status"] in ["crisis", "injection"]:
        reply_text = guardrail_result["response"]
        
        # Save assistant emergency response
        assistant_msg = ChatMessage(
            session_id=session_id,
            sender="assistant",
            content_text=reply_text,
            modality="text"
        )
        db.add(assistant_msg)
        db.commit()

        # Generate Audio
        audio_filename = TTSService.text_to_speech(reply_text, session_id) if generate_audio else None
        audio_url = f"/audio/{audio_filename}" if audio_filename else None

        return {
            "response_text": reply_text,
            "audio_url": audio_url,
            "rag_sources": [],
            "guardrail_status": guardrail_result["status"]
        }

    # 5. RAG Retrieval for relevant grounding techniques
    retrieved_chunks = rag_engine.retrieve(db, combined_input_text or "anxiety and grounding", top_k=2)

    # 6. Fetch conversation history for contextual flow
    history_records = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.desc()).limit(6).all()
    history = [{"sender": m.sender, "content_text": m.content_text} for m in reversed(history_records)]

    # 7. Generate Response from Gemini
    clean_prompt = guardrail_result["clean_text"]
    response_text = gemini_service.generate_response(
        prompt=clean_prompt,
        rag_chunks=retrieved_chunks,
        image_bytes=image_bytes,
        image_mime=image_mime,
        audio_bytes=audio_bytes,
        audio_mime=audio_mime,
        document_text=document_text,
        history=history
    )

    # 8. Save Assistant response to database
    assistant_msg = ChatMessage(
        session_id=session_id,
        sender="assistant",
        content_text=response_text,
        modality="text"
    )
    db.add(assistant_msg)
    db.commit()

    # 9. Generate Text-To-Speech audio
    audio_filename = TTSService.text_to_speech(response_text, session_id) if generate_audio else None
    audio_url = f"/audio/{audio_filename}" if audio_filename else None

    return {
        "response_text": response_text,
        "audio_url": audio_url,
        "rag_sources": retrieved_chunks,
        "guardrail_status": "pass"
    }

@app.get("/audio/{filename}")
def get_audio_file(filename: str):
    file_path = settings.AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg")
