"""Shared helper for writing an audit-log row. Kept in one place so every
router records history the same way."""

import uuid

from app.models import AuditLog


def log_action(
    db,
    *,
    pensioner_id: int | None,
    actor_id: int | None,
    actor_role: str | None = None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    before_value: str | None = None,
    after_value: str | None = None,
    result: str = "Success",
    details: str | None = None,
):
    db.add(
        AuditLog(
            pensioner_id=pensioner_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_value=before_value,
            after_value=after_value,
            result=result,
            correlation_id=uuid.uuid4().hex[:12],
            details=details,
        )
    )
