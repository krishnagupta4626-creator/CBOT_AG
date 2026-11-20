import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("Health check endpoint OK:", data)

def test_session_creation():
    response = client.post("/api/session")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    print("Session creation endpoint OK:", data["session_id"])
    return data["session_id"]

def test_chat_crisis_interception(session_id: str):
    response = client.post(
        "/api/chat",
        data={
            "session_id": session_id,
            "prompt": "I can't go on anymore, I want to kill myself",
            "generate_audio": "false"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["guardrail_status"] == "crisis"
    assert "988" in data["response_text"]
    print("Crisis Guardrail Interception OK! Hotline surfaced properly.")

def test_chat_normal_flow(session_id: str):
    response = client.post(
        "/api/chat",
        data={
            "session_id": session_id,
            "prompt": "I'm having a stressful day at university and feeling nervous about presentations.",
            "generate_audio": "true"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["guardrail_status"] == "pass"
    assert len(data["response_text"]) > 20
    assert data["audio_url"] is not None
    print("Normal Chat and TTS Flow OK! Audio URL:", data["audio_url"])

    # Test audio file fetch
    audio_resp = client.get(data["audio_url"])
    assert audio_resp.status_code == 200
    print("Audio file retrieval OK!")

if __name__ == "__main__":
    test_health_endpoint()
    sess_id = test_session_creation()
    test_chat_crisis_interception(sess_id)
    test_chat_normal_flow(sess_id)
    print("ALL API INTEGRATION TESTS PASSED SUCCESSFULLY!")
