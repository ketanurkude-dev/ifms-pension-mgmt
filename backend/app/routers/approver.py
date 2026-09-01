from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_approver
from app.database import get_db
from app.models import BankChangeRequest, Pensioner
from app.schemas import ApproverQueueItem, ReviewRequest

router = APIRouter(prefix="/approver", tags=["approver"])


@router.get("/queue", response_model=list[ApproverQueueItem])
def get_queue(
    approver: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    items = []
    for req in (
        db.query(BankChangeRequest)
        .filter(BankChangeRequest.status == "Submitted", BankChangeRequest.is_deleted.is_(False))
        .order_by(BankChangeRequest.server_date)
        .all()
    ):
        pensioner = db.query(Pensioner).get(req.pensioner_id)
        items.append(
            ApproverQueueItem(
                id=req.id,
                pensioner_id=req.pensioner_id,
                pensioner_name=pensioner.name if pensioner else "Unknown",
                title=f"Bank account change: {req.new_bank_name}",
                status=req.status,
                server_date=req.server_date,
            )
        )
    return items


@router.post("/bank-requests/{request_id}/review", response_model=None)
def review_bank_request(
    request_id: int,
    payload: ReviewRequest,
    approver: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    if payload.status not in ("Approved", "Rejected", "Returned"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    request = db.query(BankChangeRequest).filter(BankChangeRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if payload.status == "Returned" and not payload.review_remarks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Remarks are required to return an item")

    request.status = payload.status
    request.reviewed_by = approver.id
    request.review_remarks = payload.review_remarks
    request.reviewed_at = datetime.utcnow()

    if payload.status == "Approved":
        pensioner = db.query(Pensioner).filter(Pensioner.id == request.pensioner_id).first()
        pensioner.bank_account_number = request.new_account_number
        pensioner.bank_ifsc = request.new_ifsc
        pensioner.bank_name = request.new_bank_name

    db.commit()
    return {"message": f"Bank change request {payload.status.lower()}"}
