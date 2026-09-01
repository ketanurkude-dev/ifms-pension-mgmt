from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner
from app.database import get_db
from app.models import BankChangeRequest, Pensioner
from app.schemas import BankChangeRequestCreate, BankChangeRequestOut

router = APIRouter(prefix="/bank-requests", tags=["bank-requests"])


@router.get("", response_model=list[BankChangeRequestOut])
def list_my_requests(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    return (
        db.query(BankChangeRequest)
        .filter(BankChangeRequest.pensioner_id == pensioner.id, BankChangeRequest.is_deleted.is_(False))
        .order_by(BankChangeRequest.server_date.desc())
        .all()
    )


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
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


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
    return request
