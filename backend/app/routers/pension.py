from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner
from app.database import get_db
from app.models import PensionSlip, Pensioner
from app.pdf import build_annual_pension_statement_pdf, build_pension_slip_pdf
from app.schemas import PensionSlipOut
from app.seed import financial_year_label

router = APIRouter(prefix="/pension", tags=["pension"])


@router.get("/slips", response_model=list[PensionSlipOut])
def list_pension_slips(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    return (
        db.query(PensionSlip)
        .filter(PensionSlip.pensioner_id == pensioner.id, PensionSlip.is_deleted.is_(False))
        .order_by(PensionSlip.month.desc())
        .all()
    )


# This must be declared before /slips/{slip_id}/pdf -- otherwise FastAPI
# matches "annual-statement" against the {slip_id}:int path parameter and
# fails validation before this route is ever considered.
@router.get("/slips/annual-statement/pdf")
def download_annual_statement_pdf(
    financial_year: str,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    all_slips = (
        db.query(PensionSlip)
        .filter(
            PensionSlip.pensioner_id == pensioner.id,
            PensionSlip.is_deleted.is_(False),
            PensionSlip.published_on.isnot(None),
        )
        .order_by(PensionSlip.month)
        .all()
    )
    slips = [s for s in all_slips if financial_year_label(s.month) == financial_year]
    if not slips:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No published slips for that financial year")

    pdf_bytes = build_annual_pension_statement_pdf(pensioner, slips, financial_year, pensioner.preferred_language)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="pension-annual-statement-{financial_year}.pdf"'},
    )


@router.get("/slips/{slip_id}/pdf")
def download_pension_slip_pdf(
    slip_id: int,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    slip = (
        db.query(PensionSlip)
        .filter(PensionSlip.id == slip_id, PensionSlip.pensioner_id == pensioner.id)
        .first()
    )
    if not slip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pension slip not found")
    if not slip.published_on:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This month's slip is not published yet")

    pdf_bytes = build_pension_slip_pdf(pensioner, slip, pensioner.preferred_language)
    filename = f"pension-slip-{slip.month.strftime('%Y-%m')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
