# app/rag/ingest.py
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from app.rag.eligibility import DocMeta, eligibility_check
from app.models.openai_client import embed_texts

QDRANT_URL = os.environ["QDRANT_URL"]
COLLECTION = os.environ["QDRANT_COLLECTION"]

client = QdrantClient(url=QDRANT_URL)

def ensure_collection(vector_size: int = 1536):
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=qm.VectorParams(size=vector_size, distance=qm.Distance.COSINE),
        )

def chunk_text(text: str, max_chars: int = 1200) -> list[str]:
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

async def ingest_document(meta: DocMeta, raw_text: str):
    dec = eligibility_check(meta)
    if not dec.eligible:
        # ici: envoyer une alerte / ticket si escalation_required
        return {"status": "blocked", "reason": dec.reason, "escalate": dec.escalation_required}

    chunks = chunk_text(raw_text)
    vectors = await embed_texts(chunks)  # embeddings “vrais”
    points = []
    for i, (c, v) in enumerate(zip(chunks, vectors)):
        points.append(qm.PointStruct(
            id=f"{meta.doc_id}:{i}",
            vector=v,
            payload={
                "doc_id": meta.doc_id,
                "source": meta.source,
                "classification": meta.classification,
                "text": c,
                "owner": meta.owner,
            }
        ))

    client.upsert(collection_name=COLLECTION, points=points)
    return {"status": "indexed", "chunks": len(chunks)}