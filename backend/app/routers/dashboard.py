from fastapi import APIRouter, Depends

from app.auth import get_current_pensioner
from app.models import Pensioner
from app.schemas import PensionerOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/me", response_model=PensionerOut)
def get_my_profile(pensioner: Pensioner = Depends(get_current_pensioner)):
    return pensioner
