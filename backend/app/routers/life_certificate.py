from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner, require_approver
from app.database import get_db
from app.models import LifeCertificate, Pensioner
from app.schemas import (
    LifeCertificateCreate,
    LifeCertificateOut,
    LifeCertificateQueueItem,
    LifeCertificateReview,
    LifeCertificateStatusOut,
)

router = APIRouter(prefix="/life-certificate", tags=["life-certificate"])

MODES = ["Digital (Jeevan Pramaan)", "Physical (uploaded)"]
VALIDITY_DAYS = 365
DUE_SOON_WINDOW_DAYS = 30


def _latest_verified(pensioner_id: int, db: Session) -> LifeCertificate | None:
    return (
        db.query(LifeCertificate)
        .filter(
            LifeCertificate.pensioner_id == pensioner_id,
            LifeCertificate.status == "Verified",
            LifeCertificate.is_deleted.is_(False),
        )
        .order_by(LifeCertificate.valid_to.desc())
        .first()
    )


def _compute_status(pensioner: Pensioner, db: Session) -> LifeCertificateStatusOut:
    latest = _latest_verified(pensioner.id, db)
    if latest:
        due_date = latest.valid_to
        current_valid_from, current_valid_to = latest.valid_from, latest.valid_to
    else:
        # No certificate on record yet -- treat one year from registration as the first due date.
        due_date = (pensioner.server_date + timedelta(days=VALIDITY_DAYS)).date()
        current_valid_from, current_valid_to = None, None

    today = date.today()
    is_overdue = today > due_date
    is_due_soon = not is_overdue and (due_date - today).days <= DUE_SOON_WINDOW_DAYS

    stoppage_reason = None
    if is_overdue:
        stoppage_reason = (
            "Your annual life certificate has not been submitted since it fell due on "
            f"{due_date.strftime('%d-%m-%Y')}. Further pension disbursement may be withheld until a valid "
            "certificate is submitted and verified."
        )

    return LifeCertificateStatusOut(
        current_valid_from=current_valid_from,
        current_valid_to=current_valid_to,
        due_date=due_date,
        is_due_soon=is_due_soon,
        is_overdue=is_overdue,
        stoppage_reason=stoppage_reason,
    )


@router.get("/status", response_model=LifeCertificateStatusOut)
def get_status(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    return _compute_status(pensioner, db)


@router.get("/history", response_model=list[LifeCertificateOut])
def get_history(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    return (
        db.query(LifeCertificate)
        .filter(LifeCertificate.pensioner_id == pensioner.id, LifeCertificate.is_deleted.is_(False))
        .order_by(LifeCertificate.server_date.desc())
        .all()
    )


@router.post("", response_model=LifeCertificateOut, status_code=status.HTTP_201_CREATED)
def submit_certificate(
    payload: LifeCertificateCreate,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    if payload.mode not in MODES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown submission mode")

    today = date.today()
    certificate = LifeCertificate(
        pensioner_id=pensioner.id,
        mode=payload.mode,
        reference=payload.reference,
        submitted_on=today,
    )

    if payload.mode == "Digital (Jeevan Pramaan)":
        # Mock of interface IF-12: the digital route always verifies immediately.
        certificate.status = "Verified"
        certificate.valid_from = today
        certificate.valid_to = today + timedelta(days=VALIDITY_DAYS)
        certificate.verified_at = datetime.utcnow()
    else:
        certificate.status = "Pending verification"

    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return certificate


@router.get("/queue", response_model=list[LifeCertificateQueueItem])
def get_queue(
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    items = []
    for cert in (
        db.query(LifeCertificate)
        .filter(LifeCertificate.status == "Pending verification", LifeCertificate.is_deleted.is_(False))
        .order_by(LifeCertificate.server_date)
        .all()
    ):
        pensioner = db.query(Pensioner).get(cert.pensioner_id)
        items.append(
            LifeCertificateQueueItem(
                id=cert.id,
                pensioner_id=cert.pensioner_id,
                pensioner_name=pensioner.name if pensioner else "Unknown",
                mode=cert.mode,
                reference=cert.reference,
                submitted_on=cert.submitted_on,
                server_date=cert.server_date,
            )
        )
    return items


@router.post("/{certificate_id}/verify", response_model=LifeCertificateOut)
def verify_certificate(
    certificate_id: int,
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    certificate = db.query(LifeCertificate).filter(LifeCertificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    if certificate.status != "Pending verification":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a pending certificate can be verified")

    certificate.status = "Verified"
    certificate.valid_from = certificate.submitted_on
    certificate.valid_to = certificate.submitted_on + timedelta(days=VALIDITY_DAYS)
    certificate.verified_by = officer.id
    certificate.verified_at = datetime.utcnow()
    db.commit()
    db.refresh(certificate)
    return certificate


@router.post("/{certificate_id}/reject", response_model=LifeCertificateOut)
def reject_certificate(
    certificate_id: int,
    payload: LifeCertificateReview,
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    certificate = db.query(LifeCertificate).filter(LifeCertificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    if certificate.status != "Pending verification":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a pending certificate can be rejected")
    if not payload.remarks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Remarks are required to reject a certificate")

    certificate.status = "Rejected"
    certificate.verified_by = officer.id
    certificate.verified_at = datetime.utcnow()
    certificate.review_remarks = payload.remarks
    db.commit()
    db.refresh(certificate)
    return certificate
