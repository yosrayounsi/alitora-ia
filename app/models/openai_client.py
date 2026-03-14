
# app/models/openai_client.py
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
EMBED_MODEL = "text-embedding-3-small"

async def embed_texts(texts: list[str]) -> list[list[float]]:
    # SDK sync => ok en MVP. (Plus tard: async client)
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]