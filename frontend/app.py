import streamlit as st
import requests
import uuid
from pathlib import Path

# Streamlit Page Config
st.set_page_config(
    page_title="EmoPal - Multimodal Emotional Companion",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Endpoint
API_URL = "http://127.0.0.1:8000"

# Custom CSS for comforting emotional support theme
st.markdown("""
<style>
    .main {
        background-color: #FAF8F5;
    }
    .stChatMessage {
        border-radius: 12px;
        padding: 10px;
        margin-bottom: 8px;
    }
    .crisis-card {
        background-color: #FFF0F0;
        border-left: 5px solid #FF4D4D;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .grounding-box {
        background-color: #F0F7F4;
        border-left: 5px solid #48BB78;
        padding: 12px;
        border-radius: 8px;
        margin-top: 10px;
    }
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-crisis {
        background-color: #FED7D7;
        color: #C53030;
    }
    .badge-safe {
        background-color: #C6F6D5;
        color: #22543D;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "session_id" not in st.session_state:
    st.session_state.session_id = f"user_{uuid.uuid4().hex[:8]}"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Hello, I am **EmoPal**, your compassionate companion. Whatever is on your heart or mind today—whether you want to vent, share a photo of your day, send a voice note, or practice a grounding breath—I am right here with you. How are you feeling in this moment?",
            "audio_url": None,
            "rag_sources": []
        }
    ]

# Sidebar
with st.sidebar:
    st.title("🌸 EmoPal Companion")
    st.caption("A Safe, Non-Judgmental Multimodal Space")
    
    # Backend Status
    try:
        health_resp = requests.get(f"{API_URL}/health", timeout=2)
        if health_resp.status_code == 200:
            h_data = health_resp.json()
            db_label = h_data.get("database_type", "active").upper()
            gemini_label = "Active 🟢" if h_data.get("gemini_active") else "Config Mode 🟡"
            st.success(f"Backend Connected ({db_label})")
            st.caption(f"Gemini Engine: {gemini_label}")
        else:
            st.warning("Backend responding with non-200")
    except Exception:
        st.error("Backend Server (FastAPI) is offline on port 8000")

    st.markdown("---")
    st.subheader("🎙️ Voice & Multimodal Controls")
    enable_tts = st.toggle("Enable Voice Responses (Audio TTS)", value=True)

    st.markdown("---")
    st.subheader("🧘 Instant Grounding Tools")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌬️ Box Breath", use_container_width=True):
            st.session_state.preset_prompt = "Can you guide me through a 2-minute Box Breathing exercise to slow my heart rate?"
    with col2:
        if st.button("🖐️ 5-4-3-2-1", use_container_width=True):
            st.session_state.preset_prompt = "I feel overwhelmed. Can we do the 5-4-3-2-1 sensory grounding exercise right now?"

    st.markdown("---")
    st.subheader("🆘 Emergency Crisis Resources")
    st.markdown("""
    - **US/Canada**: Call/Text **988**
    - **UK**: Call **111** or **116 123**
    - **India**: Call **9152987821** or **14416**
    - **Global**: [findahelpline.com](https://findahelpline.com)
    """)

    if st.button("🗑️ Clear Session & Start Fresh", use_container_width=True):
        st.session_state.session_id = f"user_{uuid.uuid4().hex[:8]}"
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "A fresh page has started. I'm right here with you whenever you're ready.",
                "audio_url": None,
                "rag_sources": []
            }
        ]
        st.rerun()

# Main Header
st.subheader("💬 Empathetic Conversation")

# Display Message History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Display Audio Player if assistant generated speech
        if msg.get("audio_url"):
            full_audio_url = f"{API_URL}{msg['audio_url']}"
            st.audio(full_audio_url, format="audio/mp3")

        # Display retrieved RAG grounding sources if present
        if msg.get("rag_sources"):
            with st.expander("📚 Coping & Grounding Knowledge Referenced"):
                for src in msg["rag_sources"]:
                    st.markdown(f"**{src.get('title')}** (Relevance: {src.get('score')}):")
                    st.write(src.get("chunk_text"))

# Multimodal Upload Expanders
with st.expander("📎 Share an Image, Audio Note, or Journal Document", expanded=False):
    col_img, col_aud, col_doc = st.columns(3)
    
    with col_img:
        uploaded_image = st.file_uploader("🖼️ Upload an Image", type=["png", "jpg", "jpeg", "webp"], key="img_uploader")
        if uploaded_image:
            st.image(uploaded_image, caption="Shared Image Preview", width=200)

    with col_aud:
        uploaded_audio = st.file_uploader("🎙️ Voice Note / Audio", type=["wav", "mp3", "m4a", "ogg"], key="aud_uploader")
        if uploaded_audio:
            st.audio(uploaded_audio)

    with col_doc:
        uploaded_doc = st.file_uploader("📄 Journal Notes (PDF / TXT)", type=["pdf", "txt"], key="doc_uploader")
        if uploaded_doc:
            st.caption(f"Attached: {uploaded_doc.name}")

# Check for preset prompt triggers
preset_text = st.session_state.pop("preset_prompt", None)

# Chat Input
user_input = st.chat_input("Share how you are feeling, vent, or ask for a calming exercise...") or preset_text

if user_input or uploaded_image or uploaded_audio or uploaded_doc:
    # Build user message preview
    display_content = user_input or "*(Shared multimodal attachment)*"
    st.session_state.messages.append({
        "role": "user",
        "content": display_content,
        "audio_url": None,
        "rag_sources": []
    })
    
    # Rerun immediately to render user bubble
    with st.chat_message("user"):
        st.markdown(display_content)
        if uploaded_image:
            st.image(uploaded_image, width=200)

    # Call FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Listening with care and preparing grounding response..."):
            try:
                files_payload = {}
                if uploaded_image:
                    files_payload["image"] = (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)
                if uploaded_audio:
                    files_payload["audio"] = (uploaded_audio.name, uploaded_audio.getvalue(), uploaded_audio.type)
                if uploaded_doc:
                    files_payload["document"] = (uploaded_doc.name, uploaded_doc.getvalue(), uploaded_doc.type)

                data_payload = {
                    "session_id": st.session_state.session_id,
                    "prompt": user_input or "",
                    "generate_audio": str(enable_tts).lower()
                }

                resp = requests.post(
                    f"{API_URL}/api/chat",
                    data=data_payload,
                    files=files_payload if files_payload else None,
                    timeout=30
                )

                if resp.status_code == 200:
                    resp_data = resp.json()
                    response_text = resp_data.get("response_text", "")
                    audio_url = resp_data.get("audio_url")
                    rag_sources = resp_data.get("rag_sources", [])
                    guardrail_status = resp_data.get("guardrail_status")

                    # Highlight crisis alert if triggered
                    if guardrail_status == "crisis":
                        st.markdown('<div class="crisis-card"><strong>⚠️ Immediate Safety Support Activated</strong></div>', unsafe_allow_html=True)

                    st.markdown(response_text)

                    if audio_url:
                        st.audio(f"{API_URL}{audio_url}", format="audio/mp3")

                    if rag_sources:
                        with st.expander("📚 Coping & Grounding Knowledge Referenced"):
                            for src in rag_sources:
                                st.markdown(f"**{src.get('title')}**:")
                                st.write(src.get("chunk_text"))

                    # Store in conversation state
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_text,
                        "audio_url": audio_url,
                        "rag_sources": rag_sources
                    })
                else:
                    st.error(f"Error from server (Status {resp.status_code}): {resp.text}")

            except Exception as e:
                st.error(f"Could not connect to FastAPI server at {API_URL}. Is it running? Details: {e}")
