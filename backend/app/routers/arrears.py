from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner
from app.database import get_db
from app.events import log_action
from app.models import AdjustmentEntry, ArrearCase, ArrearInstalment, BenefitClaimRequest, BenefitEntitlement, Pensioner
from app.pdf import build_arrears_benefits_statement_pdf
from app.schemas import (
    AdjustmentEntryOut,
    ArrearCaseOut,
    BenefitClaimCreate,
    BenefitClaimOut,
    BenefitEntitlementOut,
)

router = APIRouter(prefix="/arrears-benefits", tags=["arrears-benefits"])

# Benefit types a pensioner may claim, per FR-PP-052.
CLAIMABLE_BENEFIT_TYPES = [
    "Fixed medical allowance",
    "Constant attendant allowance",
    "Additional pension (age)",
    "Restoration of commuted pension",
]

SLA_DAYS = 15


def _arrear_case_to_out(case: ArrearCase, instalments: list[ArrearInstalment]) -> ArrearCaseOut:
    return ArrearCaseOut(
        id=case.id,
        arrear_type=case.arrear_type,
        order_reference=case.order_reference,
        order_date=case.order_date,
        period_from=case.period_from,
        period_to=case.period_to,
        sanctioned_amount=case.sanctioned_amount,
        paid_amount=case.paid_amount,
        balance_amount=float(case.sanctioned_amount) - float(case.paid_amount),
        status=case.status,
        instalments=instalments,
    )


def _adjustment_to_out(adj: AdjustmentEntry) -> AdjustmentEntryOut:
    return AdjustmentEntryOut(
        id=adj.id,
        adjustment_type=adj.adjustment_type,
        reason=adj.reason,
        authority=adj.authority,
        total_amount=adj.total_amount,
        recovered_amount=adj.recovered_amount,
        balance_amount=float(adj.total_amount) - float(adj.recovered_amount),
        status=adj.status,
    )


def _claim_to_out(claim: BenefitClaimRequest) -> BenefitClaimOut:
    return BenefitClaimOut(
        id=claim.id,
        benefit_type=claim.benefit_type,
        details=claim.details,
        document_uploaded=claim.document_uploaded,
        status=claim.status,
        review_remarks=claim.review_remarks,
        reviewed_at=claim.reviewed_at,
        server_date=claim.server_date,
        due_date=claim.due_date,
        is_breached=claim.status == "Submitted" and date.today() > claim.due_date,
        escalated=claim.escalated,
        escalated_at=claim.escalated_at,
    )


@router.get("/cases", response_model=list[ArrearCaseOut])
def list_arrear_cases(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    cases = (
        db.query(ArrearCase)
        .filter(ArrearCase.pensioner_id == pensioner.id, ArrearCase.is_deleted.is_(False))
        .order_by(ArrearCase.order_date.desc())
        .all()
    )
    out = []
    for case in cases:
        instalments = (
            db.query(ArrearInstalment)
            .filter(ArrearInstalment.arrear_case_id == case.id, ArrearInstalment.is_deleted.is_(False))
            .order_by(ArrearInstalment.instalment_number)
            .all()
        )
        out.append(_arrear_case_to_out(case, instalments))
    return out


@router.get("/adjustments", response_model=list[AdjustmentEntryOut])
def list_adjustments(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    entries = (
        db.query(AdjustmentEntry)
        .filter(AdjustmentEntry.pensioner_id == pensioner.id, AdjustmentEntry.is_deleted.is_(False))
        .order_by(AdjustmentEntry.server_date.desc())
        .all()
    )
    return [_adjustment_to_out(e) for e in entries]


@router.get("/entitlements", response_model=list[BenefitEntitlementOut])
def list_entitlements(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    return (
        db.query(BenefitEntitlement)
        .filter(BenefitEntitlement.pensioner_id == pensioner.id, BenefitEntitlement.is_deleted.is_(False))
        .order_by(BenefitEntitlement.effective_from.desc())
        .all()
    )


@router.get("/statement/pdf")
def download_statement_pdf(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    cases = (
        db.query(ArrearCase)
        .filter(ArrearCase.pensioner_id == pensioner.id, ArrearCase.is_deleted.is_(False))
        .all()
    )
    adjustments = (
        db.query(AdjustmentEntry)
        .filter(AdjustmentEntry.pensioner_id == pensioner.id, AdjustmentEntry.is_deleted.is_(False))
        .all()
    )
    benefits = (
        db.query(BenefitEntitlement)
        .filter(BenefitEntitlement.pensioner_id == pensioner.id, BenefitEntitlement.is_deleted.is_(False))
        .all()
    )
    as_of = datetime.utcnow()
    pdf_bytes = build_arrears_benefits_statement_pdf(
        pensioner, as_of, cases, adjustments, benefits, pensioner.preferred_language
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="arrears-benefits-{as_of.strftime("%Y%m%d")}.pdf"'},
    )


@router.get("/claims", response_model=list[BenefitClaimOut])
def list_claims(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    claims = (
        db.query(BenefitClaimRequest)
        .filter(BenefitClaimRequest.pensioner_id == pensioner.id, BenefitClaimRequest.is_deleted.is_(False))
        .order_by(BenefitClaimRequest.server_date.desc())
        .all()
    )
    return [_claim_to_out(c) for c in claims]


@router.post("/claims", response_model=BenefitClaimOut, status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: BenefitClaimCreate,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    if payload.benefit_type not in CLAIMABLE_BENEFIT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown benefit type")

    claim = BenefitClaimRequest(
        pensioner_id=pensioner.id,
        benefit_type=payload.benefit_type,
        details=payload.details,
        document_uploaded=payload.document_uploaded,
        due_date=date.today() + timedelta(days=SLA_DAYS),
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)
    log_action(db, pensioner_id=pensioner.id, actor_id=pensioner.id, actor_role=pensioner.role, action="Benefit claim raised", entity_type="BenefitClaimRequest", entity_id=claim.id, after_value=payload.benefit_type)
    db.commit()
    return _claim_to_out(claim)


@router.post("/claims/{claim_id}/escalate", response_model=BenefitClaimOut)
def escalate_claim(
    claim_id: int,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    claim = (
        db.query(BenefitClaimRequest)
        .filter(BenefitClaimRequest.id == claim_id, BenefitClaimRequest.pensioner_id == pensioner.id)
        .first()
    )
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")
    if claim.status != "Submitted" or date.today() <= claim.due_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This claim has not breached its service level")
    if claim.escalated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This claim has already been escalated")

    claim.escalated = True
    claim.escalated_at = datetime.utcnow()
    db.commit()
    db.refresh(claim)
    log_action(db, pensioner_id=pensioner.id, actor_id=pensioner.id, actor_role=pensioner.role, action="Benefit claim escalated", entity_type="BenefitClaimRequest", entity_id=claim.id)
    db.commit()
    return _claim_to_out(claim)
