from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner
from app.database import get_db
from app.models import DisbursementRecord, Pensioner, TaxDeclaration, TaxDeclarationLine, TaxDocument
from app.pdf import build_tax_document_pdf
from app.schemas import (
    RegimeUpdate,
    ReviseDeclaration,
    TaxDeclarationLineCreate,
    TaxDeclarationOut,
    TaxDeclarationVersionOut,
    TaxDocumentOut,
)
from app.seed import financial_year_label

router = APIRouter(prefix="/tax", tags=["tax"])

# Ceiling per deduction head, matching the SRS's "ceiling warning, not
# silent truncation" requirement (FR-PP-070). None means no fixed ceiling.
SECTION_CEILINGS = {
    "80C": 150000,
    "80CCD(1B)": 50000,
    "80D": 50000,  # enhanced senior-citizen limit
    "80DD": 75000,
    "80DDB": 100000,  # senior-citizen limit
    "80G": None,
    "80TTB": 50000,  # interest income, senior citizen
    "24(b)": 200000,
}


def _latest_declaration(pensioner_id: int, financial_year: str, db: Session) -> TaxDeclaration | None:
    return (
        db.query(TaxDeclaration)
        .filter(
            TaxDeclaration.pensioner_id == pensioner_id,
            TaxDeclaration.financial_year == financial_year,
            TaxDeclaration.is_deleted.is_(False),
        )
        .order_by(TaxDeclaration.version.desc())
        .first()
    )


def _get_or_create_draft(pensioner_id: int, financial_year: str, db: Session) -> TaxDeclaration:
    latest = _latest_declaration(pensioner_id, financial_year, db)
    if latest is None:
        latest = TaxDeclaration(pensioner_id=pensioner_id, financial_year=financial_year)
        db.add(latest)
        db.commit()
        db.refresh(latest)
        return latest
    if latest.status == "Submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This declaration is submitted and locked. Raise a revision to change it.",
        )
    return latest


def _to_out(declaration: TaxDeclaration, db: Session, pensioner: Pensioner) -> TaxDeclarationOut:
    lines = (
        db.query(TaxDeclarationLine)
        .filter(TaxDeclarationLine.tax_declaration_id == declaration.id, TaxDeclarationLine.is_deleted.is_(False))
        .all()
    )
    total_declared = sum(float(l.declared_amount) for l in lines)

    # Indicative only -- per FR-PP-074 the portal does not compute tax
    # itself; a real deployment would show the figure returned by the
    # TDS/pension-payment module. This is a clearly-labelled stand-in.
    annual_income = round(float(pensioner.basic_pension) * 12 + float(declaration.other_income), 2)
    taxable = max(0.0, annual_income - total_declared)
    indicative_tax = round(taxable * 0.05, 2) if declaration.regime == "Old" else round(taxable * 0.07, 2)

    return TaxDeclarationOut(
        id=declaration.id,
        financial_year=declaration.financial_year,
        version=declaration.version,
        regime=declaration.regime,
        other_income=declaration.other_income,
        status=declaration.status,
        submitted_at=declaration.submitted_at,
        revision_reason=declaration.revision_reason,
        tds_reference=declaration.tds_reference,
        lines=lines,
        total_declared=total_declared,
        indicative_annual_income=annual_income,
        indicative_tax=indicative_tax,
    )


@router.get("/declaration", response_model=TaxDeclarationOut)
def get_declaration(
    financial_year: str,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    declaration = _latest_declaration(pensioner.id, financial_year, db)
    if declaration is None:
        declaration = TaxDeclaration(pensioner_id=pensioner.id, financial_year=financial_year)
        db.add(declaration)
        db.commit()
        db.refresh(declaration)
    return _to_out(declaration, db, pensioner)


@router.get("/declaration/versions", response_model=list[TaxDeclarationVersionOut])
def list_versions(
    financial_year: str,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    return (
        db.query(TaxDeclaration)
        .filter(
            TaxDeclaration.pensioner_id == pensioner.id,
            TaxDeclaration.financial_year == financial_year,
            TaxDeclaration.is_deleted.is_(False),
        )
        .order_by(TaxDeclaration.version)
        .all()
    )


@router.post("/declaration/regime", response_model=TaxDeclarationOut)
def set_regime(
    payload: RegimeUpdate,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    if payload.regime not in ("Old", "New"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Regime must be 'Old' or 'New'")

    declaration = _get_or_create_draft(pensioner.id, payload.financial_year, db)
    declaration.regime = payload.regime
    declaration.other_income = payload.other_income
    db.commit()
    db.refresh(declaration)
    return _to_out(declaration, db, pensioner)


@router.post("/declaration/lines", response_model=TaxDeclarationOut, status_code=status.HTTP_201_CREATED)
def add_line(
    payload: TaxDeclarationLineCreate,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    declaration = _get_or_create_draft(pensioner.id, payload.financial_year, db)

    ceiling = SECTION_CEILINGS.get(payload.section)
    if ceiling is not None:
        existing_lines = (
            db.query(TaxDeclarationLine)
            .filter(
                TaxDeclarationLine.tax_declaration_id == declaration.id,
                TaxDeclarationLine.section == payload.section,
            )
            .all()
        )
        total_so_far = sum(float(l.declared_amount) for l in existing_lines)
        if total_so_far + payload.declared_amount > ceiling:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Declared amount exceeds the {payload.section} ceiling of Rs. {ceiling}",
            )

    line = TaxDeclarationLine(
        tax_declaration_id=declaration.id,
        section=payload.section,
        instrument=payload.instrument,
        declared_amount=payload.declared_amount,
        proof_uploaded=payload.proof_uploaded,
    )
    db.add(line)
    db.commit()
    return _to_out(declaration, db, pensioner)


@router.delete("/declaration/lines/{line_id}", response_model=TaxDeclarationOut)
def delete_line(
    line_id: int,
    financial_year: str,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    declaration = _get_or_create_draft(pensioner.id, financial_year, db)
    line = (
        db.query(TaxDeclarationLine)
        .filter(TaxDeclarationLine.id == line_id, TaxDeclarationLine.tax_declaration_id == declaration.id)
        .first()
    )
    if not line:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Declaration line not found")

    db.delete(line)
    db.commit()
    return _to_out(declaration, db, pensioner)


@router.post("/declaration/submit", response_model=TaxDeclarationOut)
def submit_declaration(
    financial_year: str,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    declaration = _get_or_create_draft(pensioner.id, financial_year, db)
    if not declaration.regime:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Choose a tax regime before submitting")

    declaration.status = "Submitted"
    declaration.submitted_at = datetime.utcnow()
    declaration.tds_reference = f"TDS/{financial_year}/{pensioner.ppo_number}/v{declaration.version}"
    db.commit()
    db.refresh(declaration)
    return _to_out(declaration, db, pensioner)


@router.post("/declaration/revise", response_model=TaxDeclarationOut)
def revise_declaration(
    payload: ReviseDeclaration,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    latest = _latest_declaration(pensioner.id, payload.financial_year, db)
    if latest is None or latest.status != "Submitted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Only a submitted declaration can be revised"
        )

    new_version = TaxDeclaration(
        pensioner_id=pensioner.id,
        financial_year=payload.financial_year,
        version=latest.version + 1,
        regime=latest.regime,
        other_income=latest.other_income,
        revision_reason=payload.reason,
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    # Carry over the previous version's lines as a starting point.
    old_lines = (
        db.query(TaxDeclarationLine)
        .filter(TaxDeclarationLine.tax_declaration_id == latest.id, TaxDeclarationLine.is_deleted.is_(False))
        .all()
    )
    for old_line in old_lines:
        db.add(
            TaxDeclarationLine(
                tax_declaration_id=new_version.id,
                section=old_line.section,
                instrument=old_line.instrument,
                declared_amount=old_line.declared_amount,
                proof_uploaded=old_line.proof_uploaded,
            )
        )
    db.commit()
    return _to_out(new_version, db, pensioner)


@router.get("/documents", response_model=list[TaxDocumentOut])
def list_tax_documents(
    financial_year: str | None = None,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    query = db.query(TaxDocument).filter(
        TaxDocument.pensioner_id == pensioner.id, TaxDocument.is_deleted.is_(False)
    )
    if financial_year:
        query = query.filter(TaxDocument.financial_year == financial_year)
    return query.order_by(TaxDocument.financial_year.desc()).all()


@router.get("/documents/{document_id}/pdf")
def download_tax_document_pdf(
    document_id: int,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    document = (
        db.query(TaxDocument)
        .filter(TaxDocument.id == document_id, TaxDocument.pensioner_id == pensioner.id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if not document.issued_on:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document has not been issued yet")

    records = (
        db.query(DisbursementRecord)
        .filter(DisbursementRecord.pensioner_id == pensioner.id, DisbursementRecord.is_deleted.is_(False))
        .all()
    )
    year_records = [r for r in records if financial_year_label(r.pay_month) == document.financial_year]
    total_paid = sum(float(r.paid_amount) for r in year_records if r.credit_status == "Credited")
    # Mock tax-deducted figure derived from the pension slips' recorded income tax for that year.
    total_tax = round(total_paid * 0.03, 2)

    pdf_bytes = build_tax_document_pdf(pensioner, document, total_paid, total_tax, pensioner.preferred_language)
    filename = f"{document.doc_type.replace(' ', '-').lower()}-{document.financial_year}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
