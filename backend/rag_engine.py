import json
import math
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models import KnowledgeDocument

logger = logging.getLogger("emopal.rag")

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two numeric vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = math.sqrt(sum(a * a for a in vec1))
    norm_b = math.sqrt(sum(b * b for b in vec2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

class RAGEngine:
    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Generates embedding for a chunk using Gemini API or fallback."""
        if not self.gemini_client or not settings.GEMINI_API_KEY:
            return None
        try:
            # Using google-genai SDK embed_content
            response = self.gemini_client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=text
            )
            # Depending on SDK version, embeddings is in response.embedding.values or response.embeddings[0].values
            if hasattr(response, "embedding") and hasattr(response.embedding, "values"):
                return list(response.embedding.values)
            elif hasattr(response, "embeddings") and len(response.embeddings) > 0:
                return list(response.embeddings[0].values)
        except Exception as e:
            logger.warning(f"Gemini embedding API call failed ({e}). Fallback matching will be used.")
        return None

    def chunk_text(self, text: str, max_chunk_chars: int = 600) -> List[str]:
        """Splits document text into coherent paragraphs/chunks."""
        raw_paragraphs = text.split("\n\n")
        chunks = []
        current = ""
        for p in raw_paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue
            if len(current) + len(p_clean) < max_chunk_chars:
                current += "\n\n" + p_clean if current else p_clean
            else:
                if current:
                    chunks.append(current)
                current = p_clean
        if current:
            chunks.append(current)
        return chunks

    def ingest_directory(self, db: Session, directory: Path = settings.KNOWLEDGE_BASE_DIR):
        """Scans the knowledge base directory, chunks text, and stores in database."""
        if not directory.exists():
            return
        
        # Check if already ingested
        existing_count = db.query(KnowledgeDocument).count()
        if existing_count > 0:
            logger.info(f"Knowledge base already contains {existing_count} chunks. Skipping re-ingestion.")
            return

        logger.info(f"Ingesting knowledge base from {directory}...")
        for file_path in directory.glob("*.txt"):
            title = file_path.stem.replace("_", " ").title()
            category = file_path.stem
            try:
                content = file_path.read_text(encoding="utf-8")
                chunks = self.chunk_text(content)
                for idx, chunk in enumerate(chunks):
                    embedding = self.get_embedding(chunk)
                    embedding_str = json.dumps(embedding) if embedding else None
                    doc = KnowledgeDocument(
                        title=title,
                        category=category,
                        chunk_index=idx,
                        chunk_text=chunk,
                        embedding_json=embedding_str
                    )
                    db.add(doc)
                db.commit()
                logger.info(f"Ingested {len(chunks)} chunks from {file_path.name}")
            except Exception as e:
                logger.error(f"Error ingesting {file_path.name}: {e}")
                db.rollback()

    def retrieve(self, db: Session, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Retrieves top_k relevant grounding chunks using vector cosine similarity
        or keyword-overlap fallback.
        """
        query_embedding = self.get_embedding(query)
        all_docs = db.query(KnowledgeDocument).all()
        if not all_docs:
            return []

        scored_docs = []
        query_words = set(query.lower().split())

        for doc in all_docs:
            score = 0.0
            if query_embedding and doc.embedding_json:
                try:
                    doc_vec = json.loads(doc.embedding_json)
                    score = cosine_similarity(query_embedding, doc_vec)
                except Exception:
                    score = 0.0
            
            # Hybrid: If no vector or score is low, incorporate keyword relevance
            if score == 0.0:
                doc_words = set(doc.chunk_text.lower().split())
                overlap = len(query_words.intersection(doc_words))
                score = overlap / max(len(query_words), 1)

            scored_docs.append((score, doc))

        # Sort descending by relevance score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, doc in scored_docs[:top_k]:
            if score > 0.1:  # Threshold to filter out noise
                results.append({
                    "title": doc.title,
                    "category": doc.category,
                    "chunk_text": doc.chunk_text,
                    "score": round(score, 3)
                })
        return results
