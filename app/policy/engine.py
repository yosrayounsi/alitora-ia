# app/policy/engine.py

from app.policy.models import RequestContext, Decision
from typing import Dict


# Mapping groupes -> rôles
GROUP_TO_ROLE = {
    "Dev": "Dev",
    "Legal": "Legal",
    "Admin": "Admin",
}


ROLE_PERMS = {
    "Dev": {"chat", "code_assistant"},
    "Legal": {"chat", "contract_review"},
    "Admin": {"chat", "view_logs", "manage_policies"},
}


def roles_from_groups(groups: list[str]) -> set[str]:
    return {GROUP_TO_ROLE[g] for g in groups if g in GROUP_TO_ROLE}


def authorize(user: Dict, action: str, ctx: RequestContext) -> Decision:

    # FIX : utiliser dictionnaire
    roles = roles_from_groups(user["groups"])

    # RBAC
    allowed_by_role = any(action in ROLE_PERMS.get(r, set()) for r in roles)

    if not allowed_by_role:
        return Decision(
            allow=False,
            reason="RBAC: role not permitted"
        )

    # ABAC examples
    if ctx.classification in {"Confidential", "Secret"}:

        if "Admin" not in roles and "Legal" not in roles:
            return Decision(
                allow=False,
                reason="ABAC: classified data requires Legal/Admin"
            )

    if ctx.country == "EU" and ctx.classification == "Secret":

        return Decision(
            allow=True,
            reason="OK (ABAC)",
            routed_model="self_hosted_eu"
        )

    return Decision(
        allow=True,
        reason="OK",
        routed_model="managed"
    )