# app/rag/query.py
import os
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from app.models.openai_client import embed_texts

QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_COLLECTION = os.environ["QDRANT_COLLECTION"]

client = QdrantClient(url=QDRANT_URL)


def allowed_classifications_for_roles(roles: set[str]) -> list[str]:
    allowed = ["Public", "Restricted"]

    if "Legal" in roles or "Admin" in roles:
        allowed.append("Confidential")

    # Secret is intentionally excluded from RAG indexing in our design
    return allowed


async def retrieve(
    query: str,
    allowed_classes: list[str],
    top_k: int = 5,
    region: str | None = None
) -> list[dict]:

    query_vector = (await embed_texts([query]))[0]

    must_conditions = [
        qm.FieldCondition(
            key="classification",
            match=qm.MatchAny(any=allowed_classes)
        )
    ]

    if region:
        must_conditions.append(
            qm.FieldCondition(
                key="region",
                match=qm.MatchValue(value=region)
            )
        )

    search_filter = qm.Filter(must=must_conditions)

    results = client.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        query_filter=search_filter,
        with_payload=True
    )

    docs = []
    seen_doc_ids = set()
    for r in results:
        doc_id = r.payload["doc_id"]
        if doc_id in seen_doc_ids:
            continue

        seen_doc_ids.add(doc_id)
        docs.append({
            "text": r.payload["text"],
            "doc_id": doc_id,
            "score": r.score,
            "classification": r.payload.get("classification"),
            "region": r.payload.get("region"),
            "source": r.payload.get("source")
        })
        
    return docs