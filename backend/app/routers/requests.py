from datetime import date, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner
from app.database import get_db
from app.models import BankChangeRequest, BenefitClaimRequest, Grievance, GrievanceEvent, Pensioner
from app.schemas import RequestEventOut, RequestSummaryOut

router = APIRouter(prefix="/requests", tags=["requests"])


def _bank_request_to_summary(r: BankChangeRequest) -> RequestSummaryOut:
    events = [RequestEventOut(action="Submitted", remarks=r.reason, server_date=r.server_date)]
    if r.reviewed_at:
        events.append(RequestEventOut(action=r.status, remarks=r.review_remarks, server_date=r.reviewed_at))
    if r.escalated_at:
        events.append(RequestEventOut(action="Escalated", remarks=None, server_date=r.escalated_at))

    return RequestSummaryOut(
        request_type="Bank account change",
        request_id=r.id,
        request_number=f"BANK/{r.id:06d}",
        title=f"Change bank to {r.new_bank_name}",
        status=r.status,
        submitted_on=r.server_date,
        due_date=r.due_date,
        is_breached=r.status == "Submitted" and date.today() > r.due_date,
        disposed_on=r.reviewed_at,
        escalated=r.escalated,
        events=sorted(events, key=lambda e: e.server_date),
    )


def _benefit_claim_to_summary(c: BenefitClaimRequest) -> RequestSummaryOut:
    events = [RequestEventOut(action="Submitted", remarks=c.details, server_date=c.server_date)]
    if c.reviewed_at:
        events.append(RequestEventOut(action=c.status, remarks=c.review_remarks, server_date=c.reviewed_at))
    if c.escalated_at:
        events.append(RequestEventOut(action="Escalated", remarks=None, server_date=c.escalated_at))

    return RequestSummaryOut(
        request_type="Benefit claim",
        request_id=c.id,
        request_number=f"BEN/{c.id:06d}",
        title=c.benefit_type,
        status=c.status,
        submitted_on=c.server_date,
        due_date=c.due_date,
        is_breached=c.status == "Submitted" and date.today() > c.due_date,
        disposed_on=c.reviewed_at,
        escalated=c.escalated,
        events=sorted(events, key=lambda e: e.server_date),
    )


def _grievance_to_summary(g: Grievance, events: list[GrievanceEvent]) -> RequestSummaryOut:
    return RequestSummaryOut(
        request_type="Grievance",
        request_id=g.id,
        request_number=g.grievance_number,
        title=g.category,
        status=g.status,
        submitted_on=g.server_date,
        due_date=g.due_date,
        is_breached=g.status != "Closed" and date.today() > g.due_date,
        disposed_on=g.closed_at,
        escalated=g.escalation_level > 0,
        events=[RequestEventOut(action=e.action, remarks=e.remarks, server_date=e.server_date) for e in events],
    )


@router.get("", response_model=list[RequestSummaryOut])
def list_my_requests(
    request_type: str | None = None,
    status: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    """Unified 'My Requests' screen per FR-PP-101/FR-PP-102, aggregating
    every officer-reviewed request type raised by the pensioner."""
    summaries = []

    if request_type in (None, "Bank account change"):
        bank_requests = (
            db.query(BankChangeRequest)
            .filter(BankChangeRequest.pensioner_id == pensioner.id, BankChangeRequest.is_deleted.is_(False))
            .all()
        )
        summaries.extend(_bank_request_to_summary(r) for r in bank_requests)

    if request_type in (None, "Benefit claim"):
        claims = (
            db.query(BenefitClaimRequest)
            .filter(BenefitClaimRequest.pensioner_id == pensioner.id, BenefitClaimRequest.is_deleted.is_(False))
            .all()
        )
        summaries.extend(_benefit_claim_to_summary(c) for c in claims)

    if request_type in (None, "Grievance"):
        grievances = (
            db.query(Grievance)
            .filter(Grievance.pensioner_id == pensioner.id, Grievance.is_deleted.is_(False))
            .all()
        )
        for g in grievances:
            events = (
                db.query(GrievanceEvent)
                .filter(GrievanceEvent.grievance_id == g.id, GrievanceEvent.is_deleted.is_(False))
                .order_by(GrievanceEvent.server_date)
                .all()
            )
            summaries.append(_grievance_to_summary(g, events))

    if status:
        summaries = [s for s in summaries if s.status == status]
    if date_from:
        summaries = [s for s in summaries if s.submitted_on.date() >= date_from]
    if date_to:
        summaries = [s for s in summaries if s.submitted_on.date() <= date_to]

    return sorted(summaries, key=lambda s: s.submitted_on, reverse=True)
