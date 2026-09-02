from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_pensioner
from app.database import get_db
from app.models import Pensioner
from app.schemas import LanguageUpdate, PensionerOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/me", response_model=PensionerOut)
def get_my_profile(pensioner: Pensioner = Depends(get_current_pensioner)):
    return pensioner


@router.put("/language", response_model=PensionerOut)
def set_language(
    payload: LanguageUpdate,
    pensioner: Pensioner = Depends(get_current_pensioner),
    db: Session = Depends(get_db),
):
    """Per FR-PP-127: the language choice is retained as a user preference
    for subsequent sessions, not just for the current browser."""
    if payload.language not in ("en", "hi"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Language must be 'en' or 'hi'")

    pensioner.preferred_language = payload.language
    db.commit()
    db.refresh(pensioner)
    return pensioner
