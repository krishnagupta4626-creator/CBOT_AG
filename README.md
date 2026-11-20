# 🌸 EmoPal - Multimodal Emotional Support Chatbot (RAG + Guardrails)

EmoPal is an emotionally intelligent, empathetic multimodal companion powered by **Google Gemini**, built with **Streamlit** (UI frontend), **FastAPI** (orchestration API), **MySQL** (persistence), and a curated **RAG (Retrieval-Augmented Generation)** knowledge pipeline for psychological first-aid and grounding exercises.

---

## 🌟 Key Features

1. **Multimodal Inputs & Outputs**:
   - **Text**: Empathetic conversation, active listening, cognitive reframing.
   - **Image**: Visual emotion acknowledgment for user-uploaded sketches, photos, or journal entries.
   - **Audio / Voice Notes**: Voice venting with spoken empathetic audio response playback (TTS via `gTTS`).
   - **Documents**: Ingests PDF or text journal notes for personalized grounding.
2. **Defensive Guardrails & Safety Overrides**:
   - **Zero-Tolerance Crisis Interceptor**: Instantly detects indicators of self-harm or suicide and overrides with regional 24/7 crisis hotlines (988, 111, Tele-MANAS, findahelpline.com) and grounding exercises.
   - **PII Scrubbing**: Strips phone numbers, emails, credit cards, and SSNs.
   - **Prompt Injection Defense**: Deflects jailbreak and system-override attempts.
   - **Non-Clinical Boundaries**: Maintains clear non-diagnostic boundaries while providing emotional validation.
3. **Evidence-Based RAG Knowledge Pipeline**:
   - Grounded in vetted psychoeducational resources:
     - *5-4-3-2-1 Sensory Grounding*
     - *Box Breathing & Physiological Sigh*
     - *R.A.I.N. Mindfulness & Thought vs. Fact Reframing*
4. **Relational Database Architecture**:
   - MySQL schema storing `chat_sessions`, `chat_messages` (with modality tags), `guardrail_logs`, and `knowledge_documents`.
   - Built-in graceful SQLite fallback mode to ensure the service runs immediately in local environments while MySQL credentials are being configured.

---

## 🏗️ Project Architecture

```
CBOT_AG/
│
├── backend/
│   ├── config.py              # Environment configuration & directory paths
│   ├── database.py            # MySQL engine & schema initializer
│   ├── models.py              # SQLAlchemy ORM models
│   ├── prompts.py             # EmoPal Master System Prompt & RAG formatting
│   ├── guardrails.py          # Crisis detection, PII scrubber, & safety filter
│   ├── rag_engine.py          # Document chunking, embeddings, & vector retrieval
│   ├── gemini_service.py      # Google Gemini multimodal client
│   ├── tts_service.py         # Text-to-speech engine
│   └── main.py                # FastAPI REST endpoints
│
├── frontend/
│   ├── app.py                 # Streamlit interactive chat UI
│   └── styles.css             # Calming emotional support styling
│
├── knowledge_base/            # Vetted grounding & coping literature
│   ├── anxiety_grounding.txt
│   ├── breathing_exercises.txt
│   └── mindfulness_coping.txt
│
├── tests/
│   ├── test_guardrails.py     # Unit tests for crisis & safety filters
│   ├── test_rag.py            # Tests for RAG chunking & retrieval
│   └── test_api.py            # End-to-end FastAPI integration tests
│
├── run_all.py                 # One-click launcher for Backend + Frontend
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
└── .env                       # Local secrets configuration
```

---

## 🚀 Getting Started

### 1. Configure Environment (`.env`)
Copy `.env.example` to `.env` and fill in your keys:
```bash
# Google Gemini API Key (from Google AI Studio)
GEMINI_API_KEY=your_actual_gemini_api_key

# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=emopal_db
```
*(Note: If your local MySQL service is not yet running or password is blank, EmoPal automatically falls back to an offline local SQLite database `emopal_fallback.db` without crashing!)*

### 2. Run All Services with One Command
```bash
python run_all.py
```
This launches:
- **FastAPI Backend**: `http://127.0.0.1:8000` (API Docs: `http://127.0.0.1:8000/docs`)
- **Streamlit Frontend**: `http://localhost:8501`

### 3. Or Run Individually

**Terminal 1 (Backend):**
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Frontend):**
```bash
streamlit run frontend/app.py
```

---

## 🧪 Running Verification Tests

Run the test suite to verify Guardrails, RAG, and API functionality:
```bash
python tests/test_guardrails.py
python tests/test_rag.py
python tests/test_api.py
```
All tests verify zero-tolerance crisis triggers, PII scrubbing, RAG document retrieval, and audio response pipelines.
