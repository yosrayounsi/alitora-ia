# app/rag/eligibility.py
from pydantic import BaseModel

class DocMeta(BaseModel):
    doc_id: str
    source: str  # SharePoint/Jira/Git/...
    classification: str  # Public/Restricted/Confidential/Secret
    owner: str | None = None

class EligibilityDecision(BaseModel):
    eligible: bool
    reason: str
    escalation_required: bool = False

def eligibility_check(meta: DocMeta) -> EligibilityDecision:
    if meta.classification == "Secret":
        return EligibilityDecision(
            eligible=False,
            reason="Secret documents must never be indexed",
            escalation_required=False
        )

    if meta.classification == "Confidential":
        # MVP: bloqué par défaut, nécessite un process d’approbation
        return EligibilityDecision(
            eligible=False,
            reason="Confidential requires explicit approval / allowlist",
            escalation_required=True
        )

    return EligibilityDecision(eligible=True, reason="OK to index")