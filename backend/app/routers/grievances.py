from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner, require_approver
from app.database import get_db
from app.models import Grievance, GrievanceEvent, Pensioner
from app.pdf import build_grievance_acknowledgement_pdf
from app.schemas import (
    GrievanceActionRequest,
    GrievanceCreate,
    GrievanceOut,
    GrievanceQueueItem,
    GrievanceReopenRequest,
    GrievanceSatisfactionRequest,
)

router = APIRouter(prefix="/grievances", tags=["grievances"])

# Per FR-PP-107. A configurable list in a real deployment; hardcoded here.
GRIEVANCE_CATEGORIES = [
    "Non-receipt or short receipt of pension",
    "Non-payment of arrears",
    "Incorrect deduction",
    "Incorrect tax deduction",
    "Non-issue of Form 16",
    "Bank credit failure",
    "Non-sanction of a benefit",
    "Delay in disposal of a request",
    "Other",
]

# Service-level and reopen window are configurable per FR-PP-115/FR-PP-116 in
# a real deployment; fixed here to keep the prototype simple.
SLA_DAYS = 15
REOPEN_WINDOW_DAYS = 30


def _log(db: Session, grievance_id: int, action: str, remarks: str | None, actor_id: int | None) -> None:
    db.add(GrievanceEvent(grievance_id=grievance_id, action=action, remarks=remarks, actor_id=actor_id))


def _to_out(grievance: Grievance, db: Session) -> GrievanceOut:
    events = (
        db.query(GrievanceEvent)
        .filter(GrievanceEvent.grievance_id == grievance.id, GrievanceEvent.is_deleted.is_(False))
        .order_by(GrievanceEvent.server_date)
        .all()
    )
    is_breached = grievance.status != "Closed" and date.today() > grievance.due_date
    return GrievanceOut(
        id=grievance.id,
        grievance_number=grievance.grievance_number,
        category=grievance.category,
        description=grievance.description,
        linked_reference_type=grievance.linked_reference_type,
        linked_reference_id=grievance.linked_reference_id,
        attachment_uploaded=grievance.attachment_uploaded,
        status=grievance.status,
        due_date=grievance.due_date,
        is_breached=is_breached,
        reply=grievance.reply,
        closed_at=grievance.closed_at,
        satisfaction=grievance.satisfaction,
        reopened_count=grievance.reopened_count,
        escalated=grievance.escalation_level > 0,
        server_date=grievance.server_date,
        events=events,
    )


def _get_owned(grievance_id: int, pensioner: Pensioner, db: Session) -> Grievance:
    grievance = (
        db.query(Grievance)
        .filter(Grievance.id == grievance_id, Grievance.pensioner_id == pensioner.id, Grievance.is_deleted.is_(False))
        .first()
    )
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")
    return grievance


@router.get("/categories", response_model=list[str])
def list_categories():
    return GRIEVANCE_CATEGORIES


@router.get("", response_model=list[GrievanceOut])
def list_my_grievances(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    grievances = (
        db.query(Grievance)
        .filter(Grievance.pensioner_id == pensioner.id, Grievance.is_deleted.is_(False))
        .order_by(Grievance.server_date.desc())
        .all()
    )
    return [_to_out(g, db) for g in grievances]


@router.post("", response_model=GrievanceOut, status_code=status.HTTP_201_CREATED)
def lodge_grievance(
    payload: GrievanceCreate,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    if payload.category not in GRIEVANCE_CATEGORIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown grievance category")

    seq = db.query(Grievance).count() + 1
    grievance_number = f"GRV/{datetime.utcnow().year}/{seq:06d}"

    grievance = Grievance(
        pensioner_id=pensioner.id,
        grievance_number=grievance_number,
        category=payload.category,
        description=payload.description,
        linked_reference_type=payload.linked_reference_type,
        linked_reference_id=payload.linked_reference_id,
        attachment_uploaded=payload.attachment_uploaded,
        due_date=date.today() + timedelta(days=SLA_DAYS),
    )
    db.add(grievance)
    db.commit()
    db.refresh(grievance)

    _log(db, grievance.id, "Lodged", None, pensioner.id)
    db.commit()
    return _to_out(grievance, db)


@router.get("/{grievance_id}/acknowledgement/pdf")
def download_acknowledgement_pdf(
    grievance_id: int,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    grievance = _get_owned(grievance_id, pensioner, db)
    pdf_bytes = build_grievance_acknowledgement_pdf(pensioner, grievance, pensioner.preferred_language)
    filename = f"grievance-ack-{grievance.grievance_number.replace('/', '-')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/{grievance_id}/reply", response_model=GrievanceOut)
def reply_to_clarification(
    grievance_id: int,
    payload: GrievanceActionRequest,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    """Pensioner's reply while the officer awaits clarification. Resumes
    the service-level clock per FR-PP-113 by extending the due date by the
    number of days the clock was paused."""
    grievance = _get_owned(grievance_id, pensioner, db)
    if grievance.status != "Awaiting Clarification":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This grievance is not awaiting your reply")

    now = datetime.utcnow()
    if grievance.clarification_requested_at:
        paused_days = (now - grievance.clarification_requested_at).days
        grievance.due_date = grievance.due_date + timedelta(days=max(paused_days, 0))
    grievance.clarification_received_at = now
    grievance.status = "Open"
    db.commit()

    _log(db, grievance.id, "Clarification received", payload.remarks, pensioner.id)
    db.commit()
    return _to_out(grievance, db)


@router.post("/{grievance_id}/satisfaction", response_model=GrievanceOut)
def record_satisfaction(
    grievance_id: int,
    payload: GrievanceSatisfactionRequest,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    if payload.satisfaction not in ("Satisfied", "Dissatisfied"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Satisfaction must be Satisfied or Dissatisfied")

    grievance = _get_owned(grievance_id, pensioner, db)
    if grievance.status != "Closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a closed grievance can be rated")

    grievance.satisfaction = payload.satisfaction
    db.commit()

    _log(db, grievance.id, f"Satisfaction recorded: {payload.satisfaction}", None, pensioner.id)
    db.commit()
    return _to_out(grievance, db)


@router.post("/{grievance_id}/reopen", response_model=GrievanceOut)
def reopen_grievance(
    grievance_id: int,
    payload: GrievanceReopenRequest,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    """Per FR-PP-116: one reopen, within the reopen window, escalated to
    the next level on reopening."""
    grievance = _get_owned(grievance_id, pensioner, db)
    if grievance.status != "Closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a closed grievance can be reopened")
    if grievance.reopened_count >= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A grievance can only be reopened once")
    if grievance.closed_at and datetime.utcnow() - grievance.closed_at > timedelta(days=REOPEN_WINDOW_DAYS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The {REOPEN_WINDOW_DAYS}-day window to reopen this grievance has passed",
        )

    grievance.status = "Open"
    grievance.closed_at = None
    grievance.reply = None
    grievance.reopened_count += 1
    grievance.escalation_level += 1
    grievance.due_date = date.today() + timedelta(days=SLA_DAYS)
    db.commit()

    _log(db, grievance.id, "Reopened", payload.reason, pensioner.id)
    db.commit()
    return _to_out(grievance, db)


@router.post("/{grievance_id}/escalate", response_model=GrievanceOut)
def escalate_grievance(
    grievance_id: int,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    """Per FR-PP-106/FR-PP-115: the pensioner can escalate a grievance once
    its service level has been breached."""
    grievance = _get_owned(grievance_id, pensioner, db)
    if grievance.status == "Closed" or date.today() <= grievance.due_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This grievance has not breached its service level")
    if grievance.escalation_level > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This grievance has already been escalated")

    grievance.escalation_level += 1
    db.commit()

    _log(db, grievance.id, "Escalated", None, pensioner.id)
    db.commit()
    return _to_out(grievance, db)


# ---- Officer (pension_officer) endpoints ----


@router.get("/queue", response_model=list[GrievanceQueueItem])
def get_queue(
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    items = []
    grievances = (
        db.query(Grievance)
        .filter(Grievance.status != "Closed", Grievance.is_deleted.is_(False))
        .order_by(Grievance.server_date)
        .all()
    )
    for g in grievances:
        pensioner = db.query(Pensioner).get(g.pensioner_id)
        items.append(
            GrievanceQueueItem(
                id=g.id,
                grievance_number=g.grievance_number,
                pensioner_name=pensioner.name if pensioner else "Unknown",
                category=g.category,
                status=g.status,
                due_date=g.due_date,
                is_breached=date.today() > g.due_date,
                server_date=g.server_date,
            )
        )
    return items


def _get_any(grievance_id: int, db: Session) -> Grievance:
    grievance = db.query(Grievance).filter(Grievance.id == grievance_id, Grievance.is_deleted.is_(False)).first()
    if not grievance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grievance not found")
    return grievance


@router.post("/{grievance_id}/request-clarification", response_model=None)
def request_clarification(
    grievance_id: int,
    payload: GrievanceActionRequest,
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    grievance = _get_any(grievance_id, db)
    if grievance.status != "Open":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only an open grievance can await clarification")

    grievance.status = "Awaiting Clarification"
    grievance.clarification_requested_at = datetime.utcnow()
    db.commit()

    _log(db, grievance.id, "Clarification requested", payload.remarks, officer.id)
    db.commit()
    return {"message": "Clarification requested from pensioner"}


@router.post("/{grievance_id}/interim-reply", response_model=None)
def interim_reply(
    grievance_id: int,
    payload: GrievanceActionRequest,
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    grievance = _get_any(grievance_id, db)
    if grievance.status == "Closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This grievance is already closed")

    _log(db, grievance.id, "Interim reply", payload.remarks, officer.id)
    db.commit()
    return {"message": "Interim reply recorded"}


@router.post("/{grievance_id}/close", response_model=None)
def close_grievance(
    grievance_id: int,
    payload: GrievanceActionRequest,
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    grievance = _get_any(grievance_id, db)
    if grievance.status == "Closed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This grievance is already closed")

    grievance.status = "Closed"
    grievance.reply = payload.remarks
    grievance.reviewed_by = officer.id
    grievance.closed_at = datetime.utcnow()
    db.commit()

    _log(db, grievance.id, "Closed", payload.remarks, officer.id)
    db.commit()
    return {"message": "Grievance closed"}
