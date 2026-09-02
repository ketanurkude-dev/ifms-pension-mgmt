from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner
from app.database import get_db
from app.models import DisbursementRecord, Pensioner
from app.pdf import build_disbursement_certificate_pdf
from app.schemas import DisbursementRecordOut
from app.seed import financial_year_label

router = APIRouter(prefix="/disbursements", tags=["disbursements"])


@router.get("", response_model=list[DisbursementRecordOut])
def list_disbursements(
    financial_year: str | None = None,
    payment_type: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    query = db.query(DisbursementRecord).filter(
        DisbursementRecord.pensioner_id == pensioner.id, DisbursementRecord.is_deleted.is_(False)
    )
    if payment_type:
        query = query.filter(DisbursementRecord.payment_type == payment_type)
    if from_date:
        query = query.filter(DisbursementRecord.pay_month >= from_date)
    if to_date:
        query = query.filter(DisbursementRecord.pay_month <= to_date)

    records = query.order_by(DisbursementRecord.pay_month.desc()).all()
    if financial_year:
        records = [r for r in records if financial_year_label(r.pay_month) == financial_year]
    return records


@router.get("/certificate/pdf")
def download_disbursement_certificate_pdf(
    financial_year: str,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    all_records = (
        db.query(DisbursementRecord)
        .filter(DisbursementRecord.pensioner_id == pensioner.id, DisbursementRecord.is_deleted.is_(False))
        .order_by(DisbursementRecord.pay_month)
        .all()
    )
    records = [r for r in all_records if financial_year_label(r.pay_month) == financial_year]
    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No disbursement records for that financial year")

    pdf_bytes = build_disbursement_certificate_pdf(pensioner, records, financial_year, pensioner.preferred_language)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="disbursement-certificate-{financial_year}.pdf"'
        },
    )
