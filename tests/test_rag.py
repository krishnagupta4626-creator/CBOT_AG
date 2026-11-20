import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database import init_db, SessionLocal, DB_ENGINE_TYPE
from backend.models import KnowledgeDocument
from backend.rag_engine import RAGEngine

def test_rag_and_db():
    print(f"Testing DB on engine: {DB_ENGINE_TYPE}...")
    init_db()
    
    db = SessionLocal()
    try:
        rag = RAGEngine()
        # Ingest knowledge directory
        rag.ingest_directory(db)
        
        # Verify chunks exist
        count = db.query(KnowledgeDocument).count()
        assert count > 0, "No knowledge documents found in DB after ingestion."
        print(f"Successfully ingested {count} grounding knowledge chunks.")

        # Test query 1: Panic and anxiety
        results = rag.retrieve(db, "I feel sudden panic and rapid heartbeat, help me calm down", top_k=2)
        assert len(results) > 0, "RAG failed to retrieve grounding techniques for panic query."
        print(f"Query 1 Retrieved: {[r['title'] for r in results]}")

        # Test query 2: Overwhelming thoughts
        results_thoughts = rag.retrieve(db, "My negative thoughts are spiraling and I feel like a failure", top_k=2)
        assert len(results_thoughts) > 0, "RAG failed to retrieve reframing techniques."
        print(f"Query 2 Retrieved: {[r['title'] for r in results_thoughts]}")

        print("ALL RAG AND DATABASE TESTS PASSED SUCCESSFULLY!")
    finally:
        db.close()

if __name__ == "__main__":
    test_rag_and_db()
