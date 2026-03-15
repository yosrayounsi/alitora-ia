# app/rag/query.py
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from app.models.openai_client import embed_texts

QDRANT_URL = os.environ["QDRANT_URL"]
COLLECTION = os.environ["QDRANT_COLLECTION"]
client = QdrantClient(url=QDRANT_URL)

def allowed_classifications_for_roles(roles: set[str]) -> list[str]:
    # exemple simple
    allowed = ["Public", "Restricted"]
    if "Legal" in roles or "Admin" in roles:
        allowed.append("Confidential")
    if "Admin" in roles:
        allowed.append("Secret")  # mais rappel: Secret n’est jamais indexé dans notre gate
    return allowed

async def retrieve(query: str, allowed_classes: list[str], top_k: int = 5) -> list[dict]:
    qvec = (await embed_texts([query]))[0]

    flt = qm.Filter(
        must=[qm.FieldCondition(key="classification", match=qm.MatchAny(any=allowed_classes))]
    )

    res = client.search(
        collection_name=COLLECTION,
        query_vector=qvec,
        limit=top_k,
        query_filter=flt,
        with_payload=True,
    )
    return [{"text": r.payload["text"], "doc_id": r.payload["doc_id"], "score": r.score} for r in res]