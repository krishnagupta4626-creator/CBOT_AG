import re
import logging
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from backend.models import GuardrailLog

logger = logging.getLogger("emopal.guardrails")

# 1. High-Priority Crisis & Self-Harm Indicators
CRISIS_PATTERNS = [
    r"\b(suicide|kill myself|end my life|want to die|ending it all|hang myself|slit my wrist|overdose on pills)\b",
    r"\b(better off dead|no reason to live|can'?t go on anymore|tired of living|give up on life)\b",
    r"\b(self[- ]?harm|cutting myself|burn myself|hurt myself badly)\b"
]

# Standardized Crisis Emergency Response (Instant override)
CRISIS_RESPONSE_TEXT = """I hear how deeply in pain and overwhelmed you are right now, and I want you to know that you are not alone in this dark moment. 

Your life, your presence, and your safety matter immensely. Because I am an AI and cannot be there physically with you, **please reach out to people who can support you right now**:

- **USA & Canada**: Call or text **988** (Suicide & Crisis Lifeline — Free, 24/7, Confidential)
- **United Kingdom**: Call **111** (NHS) or **116 123** (Samaritans)
- **India**: Call **9152987821** (KIRAN Mental Health Helpline) or **14416** (Tele-MANAS)
- **International / Anywhere**: Visit [findahelpline.com](https://findahelpline.com/) to find free, confidential support in your area.

If you are in immediate physical danger, please call your local emergency services (such as 911, 999, or 112) or go to the nearest emergency room.

Take a gentle, unhurried breath with me right now. Let's focus on feeling your feet on the floor. I am right here with you while you reach out for help."""

# 2. PII Redaction Patterns
PII_PATTERNS = {
    "phone": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
    "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b"
}

# 3. Prompt Injection Defense Patterns
PROMPT_INJECTION_PATTERNS = [
    r"\b(ignore (all )?previous instructions|disregard instructions|system override|developer mode)\b",
    r"\b(bypass guardrails|jailbreak|pretend you are dan|act as an unrestricted ai)\b"
]

class GuardrailEngine:
    @staticmethod
    def check_crisis(text: str) -> Optional[str]:
        """Checks for direct or indirect self-harm/suicide signals."""
        if not text:
            return None
        text_lower = text.lower()
        for pattern in CRISIS_PATTERNS:
            if re.search(pattern, text_lower):
                return pattern
        return None

    @staticmethod
    def check_prompt_injection(text: str) -> Optional[str]:
        """Detects prompt injection or adversarial jailbreak attempts."""
        if not text:
            return None
        text_lower = text.lower()
        for pattern in PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return pattern
        return None

    @staticmethod
    def redact_pii(text: str) -> Tuple[str, bool]:
        """Scrubs personal identifiable information before logging or sending to models."""
        if not text:
            return text, False
        redacted = text
        detected = False
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, redacted):
                detected = True
                redacted = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", redacted)
        return redacted, detected

    @classmethod
    def process_input(
        cls,
        text: str,
        session_id: str,
        db: Optional[Session] = None
    ) -> dict:
        """
        Executes pre-inference guardrail checks.
        Returns dict with status: 'pass', 'crisis', or 'injection'.
        """
        clean_text, pii_found = cls.redact_pii(text)
        if pii_found and db:
            cls.log_incident(db, session_id, "pii_leak", text, "Redacted sensitive PII from input.")

        # 1. Check for crisis
        crisis_match = cls.check_crisis(text)
        if crisis_match:
            logger.warning(f"CRISIS DETECTED for session {session_id}: pattern '{crisis_match}'")
            if db:
                cls.log_incident(db, session_id, "crisis_self_harm", crisis_match, "Triggered emergency helpline response.")
            return {
                "status": "crisis",
                "clean_text": clean_text,
                "response": CRISIS_RESPONSE_TEXT
            }

        # 2. Check for prompt injection
        injection_match = cls.check_prompt_injection(text)
        if injection_match:
            logger.warning(f"PROMPT INJECTION ATTEMPT for session {session_id}: pattern '{injection_match}'")
            if db:
                cls.log_incident(db, session_id, "prompt_injection", injection_match, "Deflected adversarial system prompt instruction.")
            return {
                "status": "injection",
                "clean_text": clean_text,
                "response": "I am here solely to offer compassionate emotional support and calming grounding exercises. Let's focus on how you are feeling today."
            }

        return {
            "status": "pass",
            "clean_text": clean_text,
            "response": None
        }

    @staticmethod
    def log_incident(db: Session, session_id: str, trigger_type: str, phrase: str, action: str):
        """Logs guardrail violations in the MySQL database."""
        try:
            log_entry = GuardrailLog(
                session_id=session_id,
                trigger_type=trigger_type,
                detected_phrase=phrase[:255] if phrase else "",
                action_taken=action
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log guardrail incident to DB: {e}")
            db.rollback()
