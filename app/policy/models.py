
# app/policy/models.py
from pydantic import BaseModel

class RequestContext(BaseModel):
    country: str | None = None
    project: str | None = None
    classification: str | None = None  # Public/Restricted/Confidential/Secret

class Decision(BaseModel):
    allow: bool
    reason: str
    routed_model: str | None = None