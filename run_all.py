"""
Convenient launcher script for running FastAPI backend and Streamlit frontend concurrently.
"""
import subprocess
import sys
import time
import os

def run_services():
    print("=" * 60)
    print("🚀 Starting EmoPal Multimodal Support System")
    print("=" * 60)

    # 1. Start FastAPI Backend on port 8000
    print("Starting FastAPI Backend on http://127.0.0.1:8000 ...")
    backend_cmd = [
        sys.executable, "-m", "uvicorn", "backend.main:app",
        "--host", "127.0.0.1", "--port", "8000", "--reload"
    ]
    backend_proc = subprocess.Popen(backend_cmd)

    # Allow FastAPI a moment to bind
    time.sleep(2)

    # 2. Start Streamlit Frontend on port 8501
    print("Starting Streamlit Frontend on http://localhost:8501 ...")
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run", "frontend/app.py",
        "--server.port", "8501", "--server.headless", "true"
    ]
    frontend_proc = subprocess.Popen(frontend_cmd)

    print("\n✨ Both services are active!")
    print("➡️  Streamlit UI: http://localhost:8501")
    print("➡️  FastAPI Swagger Docs: http://127.0.0.1:8000/docs")
    print("Press Ctrl+C to stop both services.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services gracefully...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    run_services()
