from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner
from app.database import get_db
from app.models import BankChangeRequest, Pensioner
from app.schemas import BankChangeRequestCreate, BankChangeRequestOut

router = APIRouter(prefix="/bank-requests", tags=["bank-requests"])

# Same fixed service level used for grievances, kept simple for the prototype.
SLA_DAYS = 15


def _to_out(request: BankChangeRequest) -> BankChangeRequestOut:
    is_breached = request.status == "Submitted" and date.today() > request.due_date
    return BankChangeRequestOut(
        id=request.id,
        pensioner_id=request.pensioner_id,
        new_account_number=request.new_account_number,
        new_ifsc=request.new_ifsc,
        new_bank_name=request.new_bank_name,
        reason=request.reason,
        status=request.status,
        review_remarks=request.review_remarks,
        reviewed_at=request.reviewed_at,
        server_date=request.server_date,
        due_date=request.due_date,
        is_breached=is_breached,
        escalated=request.escalated,
        escalated_at=request.escalated_at,
        resubmitted_from_id=request.resubmitted_from_id,
    )


@router.get("", response_model=list[BankChangeRequestOut])
def list_my_requests(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    requests = (
        db.query(BankChangeRequest)
        .filter(BankChangeRequest.pensioner_id == pensioner.id, BankChangeRequest.is_deleted.is_(False))
        .order_by(BankChangeRequest.server_date.desc())
        .all()
    )
    return [_to_out(r) for r in requests]


@router.post("", response_model=BankChangeRequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: BankChangeRequestCreate,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    request = BankChangeRequest(
        pensioner_id=pensioner.id,
        new_account_number=payload.new_account_number,
        new_ifsc=payload.new_ifsc,
        new_bank_name=payload.new_bank_name,
        reason=payload.reason,
        due_date=date.today() + timedelta(days=SLA_DAYS),
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return _to_out(request)


@router.post("/{request_id}/withdraw", response_model=BankChangeRequestOut)
def withdraw_request(
    request_id: int,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    request = (
        db.query(BankChangeRequest)
        .filter(BankChangeRequest.id == request_id, BankChangeRequest.pensioner_id == pensioner.id)
        .first()
    )
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if request.status != "Submitted":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a submitted request can be withdrawn")

    request.status = "Withdrawn"
    db.commit()
    db.refresh(request)
    return _to_out(request)


@router.post("/{request_id}/resubmit", response_model=BankChangeRequestOut, status_code=status.HTTP_201_CREATED)
def resubmit_request(
    request_id: int,
    payload: BankChangeRequestCreate,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    """Per FR-PP-105: a rejected request can be re-submitted as a fresh
    request that keeps a reference to the one it replaces."""
    original = (
        db.query(BankChangeRequest)
        .filter(BankChangeRequest.id == request_id, BankChangeRequest.pensioner_id == pensioner.id)
        .first()
    )
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if original.status != "Rejected":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a rejected request can be re-submitted")

    new_request = BankChangeRequest(
        pensioner_id=pensioner.id,
        new_account_number=payload.new_account_number,
        new_ifsc=payload.new_ifsc,
        new_bank_name=payload.new_bank_name,
        reason=payload.reason,
        due_date=date.today() + timedelta(days=SLA_DAYS),
        resubmitted_from_id=original.id,
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return _to_out(new_request)


@router.post("/{request_id}/escalate", response_model=BankChangeRequestOut)
def escalate_request(
    request_id: int,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    """Per FR-PP-106: the pensioner can escalate a request once its
    service level has been breached."""
    request = (
        db.query(BankChangeRequest)
        .filter(BankChangeRequest.id == request_id, BankChangeRequest.pensioner_id == pensioner.id)
        .first()
    )
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if request.status != "Submitted" or date.today() <= request.due_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This request has not breached its service level")
    if request.escalated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This request has already been escalated")

    request.escalated = True
    request.escalated_at = datetime.utcnow()
    db.commit()
    db.refresh(request)
    return _to_out(request)
