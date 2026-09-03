"""MIS-style summary reports. Approver-only reports aggregate across all
pensioners; "my-summary" is available to any logged-in pensioner for
their own records. Kept as simple status-count queries against the
existing tables -- no separate audit-log infrastructure needed here."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner, require_approver
from app.database import get_db
from app.models import BankChangeRequest, BenefitClaimRequest, Grievance, LifeCertificate, Pensioner

router = APIRouter(prefix="/reports", tags=["reports"])


def _status_counts(db: Session, model, extra_filter=None) -> dict[str, int]:
    query = db.query(model).filter(model.is_deleted.is_(False))
    if extra_filter is not None:
        query = query.filter(extra_filter)
    counts: dict[str, int] = {}
    for row in query.all():
        counts[row.status] = counts.get(row.status, 0) + 1
    return counts


@router.get("/bank-requests-pipeline")
def bank_requests_pipeline(approver: Pensioner = Depends(require_approver), db: Session = Depends(get_db)):
    return _status_counts(db, BankChangeRequest)


@router.get("/benefit-claims-pipeline")
def benefit_claims_pipeline(approver: Pensioner = Depends(require_approver), db: Session = Depends(get_db)):
    return _status_counts(db, BenefitClaimRequest)


@router.get("/grievances-pipeline")
def grievances_pipeline(approver: Pensioner = Depends(require_approver), db: Session = Depends(get_db)):
    return _status_counts(db, Grievance)


@router.get("/life-certificate-pipeline")
def life_certificate_pipeline(approver: Pensioner = Depends(require_approver), db: Session = Depends(get_db)):
    return _status_counts(db, LifeCertificate)


@router.get("/my-summary")
def my_summary(pensioner: Pensioner = Depends(get_current_pensioner), db: Session = Depends(get_db)):
    return {
        "bank_requests": _status_counts(db, BankChangeRequest, BankChangeRequest.pensioner_id == pensioner.id),
        "benefit_claims": _status_counts(db, BenefitClaimRequest, BenefitClaimRequest.pensioner_id == pensioner.id),
        "grievances": _status_counts(db, Grievance, Grievance.pensioner_id == pensioner.id),
        "life_certificates": _status_counts(db, LifeCertificate, LifeCertificate.pensioner_id == pensioner.id),
    }
