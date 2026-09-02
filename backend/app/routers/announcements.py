from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner, require_approver
from app.database import get_db
from app.models import Announcement, Faq, Pensioner
from app.schemas import AnnouncementCreate, AnnouncementOut, FaqCreate, FaqOut

router = APIRouter(prefix="/announcements", tags=["announcements"])

# Categories a pensioner-facing announcement or FAQ may be filed under.
CATEGORIES = ["General", "Policy", "Payment", "Outage / maintenance", "Scheme update"]


@router.get("/categories", response_model=list[str])
def list_categories():
    return CATEGORIES


@router.get("", response_model=list[AnnouncementOut])
def list_published_announcements(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    """Per FR-PP-132. No audience-segmentation is modelled here -- every
    pensioner sees every published, currently-valid announcement."""
    today = date.today()
    return (
        db.query(Announcement)
        .filter(
            Announcement.status == "Published",
            Announcement.valid_from <= today,
            Announcement.valid_to >= today,
            Announcement.is_deleted.is_(False),
        )
        .order_by(Announcement.valid_from.desc())
        .all()
    )


@router.get("/admin", response_model=list[AnnouncementOut])
def list_all_announcements(
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    return (
        db.query(Announcement)
        .filter(Announcement.is_deleted.is_(False))
        .order_by(Announcement.server_date.desc())
        .all()
    )


@router.post("/admin", response_model=AnnouncementOut, status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreate,
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    if payload.category not in CATEGORIES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category")
    if payload.valid_to < payload.valid_from:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid-to date must be on or after valid-from")

    announcement = Announcement(
        title=payload.title,
        body=payload.body,
        category=payload.category,
        target_audience=payload.target_audience,
        valid_from=payload.valid_from,
        valid_to=payload.valid_to,
        has_attachment=payload.has_attachment,
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


@router.post("/admin/{announcement_id}/publish", response_model=AnnouncementOut)
def publish_announcement(
    announcement_id: int,
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    if announcement.status != "Draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a draft can be published")

    announcement.status = "Published"
    announcement.published_at = datetime.utcnow()
    announcement.published_by = officer.id
    db.commit()
    db.refresh(announcement)
    return announcement


@router.post("/admin/{announcement_id}/withdraw", response_model=AnnouncementOut)
def withdraw_announcement(
    announcement_id: int,
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    if announcement.status != "Published":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only a published announcement can be withdrawn")

    announcement.status = "Withdrawn"
    db.commit()
    db.refresh(announcement)
    return announcement


@router.get("/faqs", response_model=list[FaqOut])
def list_active_faqs(
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    return (
        db.query(Faq)
        .filter(Faq.status == "Active", Faq.is_deleted.is_(False))
        .order_by(Faq.category, Faq.display_order)
        .all()
    )


@router.get("/faqs/admin", response_model=list[FaqOut])
def list_all_faqs(
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    return (
        db.query(Faq)
        .filter(Faq.is_deleted.is_(False))
        .order_by(Faq.category, Faq.display_order)
        .all()
    )


@router.post("/faqs/admin", response_model=FaqOut, status_code=status.HTTP_201_CREATED)
def create_faq(
    payload: FaqCreate,
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    faq = Faq(
        question=payload.question,
        answer=payload.answer,
        category=payload.category,
        display_order=payload.display_order,
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq


@router.post("/faqs/admin/{faq_id}/toggle", response_model=FaqOut)
def toggle_faq(
    faq_id: int,
    officer: Pensioner = Depends(require_approver),
    db: Session = Depends(get_db),
):
    faq = db.query(Faq).filter(Faq.id == faq_id).first()
    if not faq:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="FAQ not found")

    faq.status = "Inactive" if faq.status == "Active" else "Active"
    db.commit()
    db.refresh(faq)
    return faq
