# app/main.py
import time
import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.policy.engine import authorize
from app.policy.models import RequestContext
from app.gateway.dlp import dlp_check
from app.gateway.quotas import check_and_add
from app.rag.query import retrieve, allowed_classifications_for_roles
from app.models.router import call_managed_llm
from app.telemetry.metrics import REQS, TOKENS, LAT
from app.telemetry.audit import audit_log

app = FastAPI(title="Altiora AI Gateway API")


class ChatIn(BaseModel):
    message: str
    country: str | None = None
    project: str | None = None
    classification: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(payload: ChatIn):
    try:
       
        user = {
            "oid": "user-123",
            "upn": "yosra@altiora.local",
            "name": "Yosra",
            "groups": ["Dev"],
            "roles": ["Dev"],
            "attributes": {
                "country": "EU",         
                "clearance": "Confidential",
                "ops_region": "EU"   
            }
        }

        roles = set(user["roles"])

        dec = authorize(
            user=user,
            action="chat",
            ctx=RequestContext(
                country=payload.country,
                project=payload.project,
                classification=payload.classification
            ),
        )

        if not dec.allow:
            raise HTTPException(403, dec.reason)

       
        ok, reason = dlp_check(payload.message)
        if not ok:
            raise HTTPException(400, reason)

       
        allowed_classes = allowed_classifications_for_roles(roles)

        t0 = time.time()

        with LAT.labels(stage="rag").time():
            ctx_chunks = await retrieve(
                query=payload.message,
                allowed_classes=allowed_classes,
                top_k=5,
                region=payload.country
            )

        context = "\n\n".join([f"- {c['text']}" for c in ctx_chunks])

        full_prompt = f"""
You are the Altiora internal AI assistant.

Use ONLY the provided internal context if it is relevant.

Context:
{context}

User question:
{payload.message}
"""

        with LAT.labels(stage="model").time():
            answer, meta = call_managed_llm(full_prompt)

       
        est_tokens = meta.get("total_tokens") or 0
        if est_tokens and not check_and_add(user["oid"], est_tokens):
            raise HTTPException(429, "Quota exceeded")

        
        REQS.labels(model=meta["model"], action="chat").inc()

        if meta.get("input_tokens") is not None:
            TOKENS.labels(model=meta["model"], type="input").inc(meta["input_tokens"])

        if meta.get("output_tokens") is not None:
            TOKENS.labels(model=meta["model"], type="output").inc(meta["output_tokens"])

       
        audit_log({
            "event": "chat",
            "user": user["upn"],
            "roles": list(roles),
            "model": meta["model"],
            "tokens": meta.get("total_tokens"),
            "country": payload.country,
            "project": payload.project,
            "user_region": user["attributes"]["country"],
            "ops_region": user["attributes"]["ops_region"],
            "routed_runtime": dec.routed_model,
            "docs_used": list({c["doc_id"] for c in ctx_chunks}),
            "latency_ms": int((time.time() - t0) * 1000),
        })

        return {
            "answer": answer,
            "meta": meta,
            "docs": ctx_chunks,
            "routing": {
                "runtime": dec.routed_model,
                "user_region": user["attributes"]["country"],
                "ops_region": user["attributes"]["ops_region"]
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        print("===================================")
        print("INTERNAL SERVER ERROR")
        traceback.print_exc()
        print("===================================")

        raise HTTPException(status_code=500, detail=str(e))