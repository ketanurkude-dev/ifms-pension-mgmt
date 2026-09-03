from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_token, decode_token, get_current_pensioner, hash_password, verify_password
from app.config import settings
from app.database import get_db
from app.events import log_action
from app.models import ROLES, Pensioner
from app.schemas import LoginRequest, LoginResponse, RegisterRequest, TokenResponse, VerifyOtpRequest
from app.seed import (
    build_adjustment_entries,
    build_arrear_case_and_instalments,
    build_benefit_entitlements,
    build_disbursement_records,
    build_pension_slips,
    build_tax_documents,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = (
        db.query(Pensioner)
        .filter(Pensioner.ppo_number == payload.ppo_number, Pensioner.is_deleted.is_(False))
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="PPO number already registered")

    role = payload.role if payload.role in ROLES else "pensioner"

    pensioner = Pensioner(
        ppo_number=payload.ppo_number,
        name=payload.name,
        email=payload.email,
        mobile=payload.mobile,
        date_of_birth=payload.date_of_birth,
        retired_from_office=payload.retired_from_office,
        bank_account_number=payload.bank_account_number,
        bank_ifsc=payload.bank_ifsc,
        bank_name=payload.bank_name,
        basic_pension=payload.basic_pension,
        password_hash=hash_password(payload.password),
        role=role,
    )
    db.add(pensioner)
    db.commit()
    db.refresh(pensioner)

    slips = build_pension_slips(pensioner.id, float(pensioner.basic_pension), pensioner.retired_from_office)
    db.add_all(slips)
    db.commit()

    records = build_disbursement_records(pensioner.id, slips)
    db.add_all(records)
    db.commit()

    db.add_all(build_tax_documents(pensioner.id, pensioner.retired_from_office))
    db.commit()

    case, instalments = build_arrear_case_and_instalments(
        pensioner.id, float(pensioner.basic_pension), slips, records
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    for instalment in instalments:
        instalment.arrear_case_id = case.id
    db.add_all(instalments)
    db.commit()

    db.add_all(build_adjustment_entries(pensioner.id))
    db.add_all(build_benefit_entitlements(pensioner.id, pensioner.date_of_birth))
    log_action(db, pensioner_id=pensioner.id, actor_id=pensioner.id, actor_role=role, action="Registered", entity_type="Pensioner", entity_id=pensioner.id)
    db.commit()

    return {"message": "Registration successful. You can now log in."}


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    pensioner = (
        db.query(Pensioner)
        .filter(Pensioner.ppo_number == payload.ppo_number, Pensioner.is_deleted.is_(False))
        .first()
    )
    if not pensioner or not verify_password(payload.password, pensioner.password_hash):
        log_action(
            db, pensioner_id=pensioner.id if pensioner else None, actor_id=pensioner.id if pensioner else None,
            actor_role=pensioner.role if pensioner else None, action="Failed login", entity_type="Pensioner",
            entity_id=pensioner.id if pensioner else None, result="Failure",
            details=f"Attempted login for {payload.ppo_number}",
        )
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PPO number or password")
    if not pensioner.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    pending_token = create_token(pensioner.ppo_number, purpose="otp_pending", expires_minutes=5)
    log_action(db, pensioner_id=pensioner.id, actor_id=pensioner.id, actor_role=pensioner.role, action="Password verified", entity_type="Pensioner", entity_id=pensioner.id)
    db.commit()
    return LoginResponse(pending_token=pending_token)


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    if not payload.otp.isdigit():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP must be 6 digits")

    ppo_number = decode_token(payload.pending_token, expected_purpose="otp_pending")
    pensioner = (
        db.query(Pensioner)
        .filter(Pensioner.ppo_number == ppo_number, Pensioner.is_deleted.is_(False))
        .first()
    )
    if not pensioner:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Pensioner not found")

    access_token = create_token(
        pensioner.ppo_number, purpose="access", expires_minutes=settings.access_token_expire_minutes
    )
    log_action(db, pensioner_id=pensioner.id, actor_id=pensioner.id, actor_role=pensioner.role, action="Login", entity_type="Pensioner", entity_id=pensioner.id)
    db.commit()
    return TokenResponse(access_token=access_token)


@router.post("/logout")
def logout(pensioner: Pensioner = Depends(get_current_pensioner), db: Session = Depends(get_db)):
    log_action(db, pensioner_id=pensioner.id, actor_id=pensioner.id, actor_role=pensioner.role, action="Logout", entity_type="Pensioner", entity_id=pensioner.id)
    db.commit()
    return {"message": "Logged out"}
