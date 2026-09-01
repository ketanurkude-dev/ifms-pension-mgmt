from datetime import date, datetime

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    ppo_number: str = Field(min_length=3, max_length=30)
    name: str
    email: str | None = None
    mobile: str = Field(min_length=10, max_length=15)
    date_of_birth: date
    retired_from_office: str
    bank_account_number: str
    bank_ifsc: str
    bank_name: str
    password: str = Field(min_length=6)
    role: str = "pensioner"  # "pensioner" | "pension_officer" -- lets a demo approver account be created


class LoginRequest(BaseModel):
    ppo_number: str
    password: str


class LoginResponse(BaseModel):
    pending_token: str
    message: str = "Password verified. Enter the OTP sent to your registered mobile."


class VerifyOtpRequest(BaseModel):
    pending_token: str
    otp: str = Field(min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PensionerOut(BaseModel):
    ppo_number: str
    name: str
    email: str | None
    mobile: str
    date_of_birth: date
    retired_from_office: str
    bank_account_number: str
    bank_ifsc: str
    bank_name: str
    role: str

    class Config:
        from_attributes = True


class BankChangeRequestCreate(BaseModel):
    new_account_number: str
    new_ifsc: str
    new_bank_name: str
    reason: str


class BankChangeRequestOut(BaseModel):
    id: int
    pensioner_id: int
    new_account_number: str
    new_ifsc: str
    new_bank_name: str
    reason: str
    status: str
    review_remarks: str | None
    reviewed_at: datetime | None
    server_date: datetime

    class Config:
        from_attributes = True


class ReviewRequest(BaseModel):
    status: str  # "Approved" | "Rejected" | "Returned"
    review_remarks: str | None = None


class ApproverQueueItem(BaseModel):
    id: int
    pensioner_id: int
    pensioner_name: str
    title: str
    status: str
    server_date: datetime
