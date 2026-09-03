from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_approver
from app.csv_export import rows_to_csv_response
from app.database import get_db
from app.events import log_action
from app.models import AuditLog, Pensioner
from app.schemas import AuditLogOut

router = APIRouter(prefix="/audit", tags=["audit"])


def _query_logs(
    db: Session, entity_type: str | None, action: str | None, pensioner_id: int | None,
    result: str | None, date_from: date | None, date_to: date | None,
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if pensioner_id:
        query = query.filter(AuditLog.pensioner_id == pensioner_id)
    if result:
        query = query.filter(AuditLog.result == result)
    if date_from:
        query = query.filter(AuditLog.server_date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(AuditLog.server_date <= datetime.combine(date_to, datetime.max.time()))
    return query.order_by(AuditLog.server_date.desc())


@router.get("/logs", response_model=list[AuditLogOut])
def search_audit_logs(
    approver: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
    entity_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
    pensioner_id: int | None = Query(default=None),
    result: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    limit: int = Query(default=200, le=1000),
):
    logs = _query_logs(db, entity_type, action, pensioner_id, result, date_from, date_to).limit(limit).all()
    log_action(db, pensioner_id=None, actor_id=approver.id, actor_role=approver.role, action="Audit log searched", entity_type="AuditLog", entity_id=None)
    db.commit()
    return logs


@router.get("/logs/export")
def export_audit_logs(
    approver: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
    entity_type: str | None = Query(default=None),
    action: str | None = Query(default=None),
    pensioner_id: int | None = Query(default=None),
    result: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
):
    logs = _query_logs(db, entity_type, action, pensioner_id, result, date_from, date_to).limit(5000).all()
    rows = [
        {
            "event_id": log.id, "timestamp": log.server_date, "actor_id": log.actor_id, "actor_role": log.actor_role,
            "pensioner_id": log.pensioner_id, "entity_type": log.entity_type, "entity_id": log.entity_id,
            "action": log.action, "result": log.result, "correlation_id": log.correlation_id,
            "before_value": log.before_value, "after_value": log.after_value, "details": log.details,
        }
        for log in logs
    ]
    log_action(db, pensioner_id=None, actor_id=approver.id, actor_role=approver.role, action="Audit log exported", entity_type="AuditLog", entity_id=None)
    db.commit()
    return rows_to_csv_response(rows, "audit_log.csv")
