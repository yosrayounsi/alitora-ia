import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from openai import OpenAI
import uuid

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_COLLECTION = os.environ["QDRANT_COLLECTION"]

client_openai = OpenAI(api_key=OPENAI_API_KEY)
client_qdrant = QdrantClient(url=QDRANT_URL)


def chunk_text(text: str, max_chars: int = 800):
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


def embed_texts(texts: list[str]):
    response = client_openai.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [item.embedding for item in response.data]


def ensure_collection():
    collections = client_qdrant.get_collections().collections
    names = [c.name for c in collections]

    if QDRANT_COLLECTION not in names:
        client_qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=qm.VectorParams(
                size=1536,
                distance=qm.Distance.COSINE
            ),
        )
        print(f"Collection '{QDRANT_COLLECTION}' created.")
    else:
        print(f"Collection '{QDRANT_COLLECTION}' already exists.")




def ingest_document(doc_id: str, text: str, classification: str, source: str):
    chunks = chunk_text(text)
    vectors = embed_texts(chunks)

    points = []
    for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
        points.append(
            qm.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "doc_id": doc_id,
                    "text": chunk,
                    "classification": classification,
                    "source": source
                }
            )
        )

    client_qdrant.upsert(
        collection_name=QDRANT_COLLECTION,
        points=points
    )

    print(f"Ingested {len(points)} chunks for document {doc_id}")


if __name__ == "__main__":
    ensure_collection()

    docs = [
        {
            "doc_id": "solar_project_001",
            "classification": "Restricted",
            "source": "SharePoint",
            "text": """
            The Solar Energy Project is a strategic initiative at Altiora Group.
            Its objective is to improve renewable energy production efficiency across EU regions.
            The project includes photovoltaic infrastructure optimization, monitoring dashboards,
            and predictive maintenance features supported by AI analytics.
            """
        },
        {
            "doc_id": "security_policy_001",
            "classification": "Restricted",
            "source": "Confluence",
            "text": """
            Altiora security policy requires all internal AI usage to pass through a governed AI platform.
            Public AI tools must not be used for classified or confidential documents.
            Access control is enforced through RBAC and ABAC mechanisms.
            """
        },
        {
            "doc_id": "budget_report_001",
            "classification": "Restricted",
            "source": "Jira",
            "text": """
            The AI platform budget must remain under controlled monthly usage thresholds.
            FinOps dashboards track token usage, estimated operational costs,
            and environmental indicators for AI workloads.
            """
        }
    ]

    for doc in docs:
        ingest_document(
            doc_id=doc["doc_id"],
            text=doc["text"],
            classification=doc["classification"],
            source=doc["source"]
        )

    print("All test documents ingested successfully.")