import logging
from typing import Optional, List, Dict, Any
from google import genai
from google.genai import types
from backend.config import settings
from backend.prompts import EMOPAL_MASTER_SYSTEM_PROMPT, format_rag_context

logger = logging.getLogger("emopal.gemini")

class GeminiService:
    def __init__(self):
        self.client = None
        if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() != "your_gemini_api_key_here":
            try:
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY.strip())
                logger.info("Google Gemini Client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
        else:
            logger.warning("No valid GEMINI_API_KEY configured. Running in simulated fallback mode.")

    def generate_response(
        self,
        prompt: str,
        rag_chunks: Optional[List[Dict[str, Any]]] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: Optional[str] = "image/png",
        audio_bytes: Optional[bytes] = None,
        audio_mime: Optional[str] = "audio/wav",
        document_text: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Executes multimodal generation using Google Gemini.
        """
        # If no client or API key, provide helpful simulated empathetic response
        if not self.client:
            return self._simulated_response(prompt, rag_chunks, image_bytes is not None, audio_bytes is not None, document_text is not None)

        try:
            # 1. Build System Instruction with RAG context
            rag_context_str = format_rag_context(rag_chunks or [])
            full_system_instruction = EMOPAL_MASTER_SYSTEM_PROMPT + rag_context_str

            # 2. Build Contents list
            contents = []

            # Add previous turn history if available (limit to last 6 for brevity)
            if history:
                for msg in history[-6:]:
                    role = "user" if msg.get("sender") == "user" else "model"
                    contents.append(f"{role.upper()}: {msg.get('content_text', '')}")

            # Prepare current turn multimodal parts
            user_parts = []

            # Attach Image Part
            if image_bytes:
                img_part = types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image_mime or "image/png"
                )
                user_parts.append(img_part)
                user_parts.append("Here is an image I would like to share with you.")

            # Attach Audio Part
            if audio_bytes:
                aud_part = types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=audio_mime or "audio/wav"
                )
                user_parts.append(aud_part)
                user_parts.append("Here is a voice recording of how I am feeling.")

            # Attach Document Context
            if document_text:
                user_parts.append(f"\n--- Attached Document / Notes ---\n{document_text}\n--- End of Document ---")

            # Main user prompt
            if prompt:
                user_parts.append(prompt)
            elif not user_parts:
                user_parts.append("Hello EmoPal, I need someone to talk to.")

            contents.extend(user_parts)

            # 3. Call Gemini API
            config = types.GenerateContentConfig(
                system_instruction=full_system_instruction,
                temperature=0.7,
                max_output_tokens=1000
            )

            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=contents,
                config=config
            )

            if response and response.text:
                return response.text.strip()
            return "I am right here with you. Could you share a little more about what is on your mind?"

        except Exception as e:
            logger.error(f"Gemini API generation error: {e}")
            return f"I hear you, and I am sitting with you. (Note: Gemini API reported a temporary error: {e}. Please ensure your API key and connection are configured.)"

    def _simulated_response(
        self,
        prompt: str,
        rag_chunks: Optional[List[Dict[str, Any]]],
        has_image: bool,
        has_audio: bool,
        has_doc: bool
    ) -> str:
        """Fallback response when GEMINI_API_KEY is not set yet in .env."""
        parts = ["I hear you, and thank you for trusting me with how you are feeling."]
        if has_image:
            parts.append("I received your image and can feel the emotion captured in it.")
        if has_audio:
            parts.append("I listened to your voice message; your tone and courage in sharing mean a lot.")
        if has_doc:
            parts.append("I reviewed the journal notes you uploaded.")
        
        if rag_chunks:
            top_tip = rag_chunks[0]
            parts.append(f"\nHere is a gentle practice from our knowledge base on **{top_tip.get('title')}**:\n{top_tip.get('chunk_text')}")
        else:
            parts.append("\nLet's take a slow, unhurried breath together. Inhale for 4 seconds, and exhale slowly for 4 seconds.")

        parts.append("\n*(EmoPal system notice: Set your GEMINI_API_KEY in the `.env` file to activate live Gemini multimodal responses!)*")
        return "\n\n".join(parts)
