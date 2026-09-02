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
    basic_pension: float
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
    basic_pension: float
    role: str
    preferred_language: str

    class Config:
        from_attributes = True


class LanguageUpdate(BaseModel):
    language: str  # "en" | "hi"


class PensionSlipOut(BaseModel):
    id: int
    month: date
    basic_pension: float
    dearness_relief: float
    additional_pension_age: float
    fixed_medical_allowance: float
    constant_attendant_allowance: float
    arrear_instalment: float
    other_allowances: float
    income_tax: float
    commutation_recovery: float
    overpayment_recovery: float
    court_attachment: float
    other_recoveries: float
    gross: float
    deductions: float
    net: float
    disbursing_office: str
    treasury_code: str
    bill_number: str
    voucher_number: str
    published_on: date | None

    class Config:
        from_attributes = True


class DisbursementRecordOut(BaseModel):
    id: int
    pay_month: date
    payment_type: str
    voucher_number: str
    voucher_date: date
    paid_date: date | None
    paid_amount: float
    mode_of_payment: str
    bank_reference: str | None
    credit_status: str
    status_reason: str | None

    class Config:
        from_attributes = True


class TaxDeclarationLineOut(BaseModel):
    id: int
    section: str
    instrument: str
    declared_amount: float
    proof_uploaded: bool

    class Config:
        from_attributes = True


class TaxDeclarationOut(BaseModel):
    id: int
    financial_year: str
    version: int
    regime: str | None
    other_income: float
    status: str
    submitted_at: datetime | None
    revision_reason: str | None
    tds_reference: str | None
    lines: list[TaxDeclarationLineOut]
    total_declared: float
    indicative_annual_income: float
    indicative_tax: float


class TaxDeclarationVersionOut(BaseModel):
    version: int
    status: str
    submitted_at: datetime | None
    revision_reason: str | None
    server_date: datetime

    class Config:
        from_attributes = True


class RegimeUpdate(BaseModel):
    financial_year: str
    regime: str  # "Old" | "New"
    other_income: float = 0


class TaxDeclarationLineCreate(BaseModel):
    financial_year: str
    section: str
    instrument: str
    declared_amount: float
    proof_uploaded: bool = False


class ReviseDeclaration(BaseModel):
    financial_year: str
    reason: str


class TaxDocumentOut(BaseModel):
    id: int
    financial_year: str
    doc_type: str
    issued_on: date | None
    issuing_office: str
    is_superseded: bool

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
    due_date: date
    is_breached: bool
    escalated: bool
    escalated_at: datetime | None
    resubmitted_from_id: int | None

    class Config:
        from_attributes = True


class ReviewRequest(BaseModel):
    status: str  # "Approved" | "Rejected" | "Returned"
    review_remarks: str | None = None


class GrievanceCreate(BaseModel):
    category: str
    description: str = Field(min_length=10)
    linked_reference_type: str | None = None
    linked_reference_id: int | None = None
    attachment_uploaded: bool = False


class GrievanceEventOut(BaseModel):
    action: str
    remarks: str | None
    server_date: datetime

    class Config:
        from_attributes = True


class GrievanceOut(BaseModel):
    id: int
    grievance_number: str
    category: str
    description: str
    linked_reference_type: str | None
    linked_reference_id: int | None
    attachment_uploaded: bool
    status: str
    due_date: date
    is_breached: bool
    reply: str | None
    closed_at: datetime | None
    satisfaction: str | None
    reopened_count: int
    escalated: bool
    server_date: datetime
    events: list[GrievanceEventOut]

    class Config:
        from_attributes = True


class GrievanceQueueItem(BaseModel):
    id: int
    grievance_number: str
    pensioner_name: str
    category: str
    status: str
    due_date: date
    is_breached: bool
    server_date: datetime


class GrievanceActionRequest(BaseModel):
    remarks: str = Field(min_length=3)


class GrievanceSatisfactionRequest(BaseModel):
    satisfaction: str  # "Satisfied" | "Dissatisfied"


class GrievanceReopenRequest(BaseModel):
    reason: str = Field(min_length=5)


class LifeCertificateCreate(BaseModel):
    mode: str  # "Digital (Jeevan Pramaan)" | "Physical (uploaded)"
    reference: str = Field(min_length=4)


class LifeCertificateOut(BaseModel):
    id: int
    mode: str
    reference: str
    submitted_on: date
    status: str
    valid_from: date | None
    valid_to: date | None
    verified_at: datetime | None
    review_remarks: str | None
    server_date: datetime

    class Config:
        from_attributes = True


class LifeCertificateStatusOut(BaseModel):
    current_valid_from: date | None
    current_valid_to: date | None
    due_date: date
    is_due_soon: bool
    is_overdue: bool
    stoppage_reason: str | None


class LifeCertificateQueueItem(BaseModel):
    id: int
    pensioner_id: int
    pensioner_name: str
    mode: str
    reference: str
    submitted_on: date
    server_date: datetime


class LifeCertificateReview(BaseModel):
    remarks: str | None = None


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=3)
    body: str = Field(min_length=10)
    category: str
    target_audience: str = "All pensioners"
    valid_from: date
    valid_to: date
    has_attachment: bool = False


class AnnouncementOut(BaseModel):
    id: int
    title: str
    body: str
    category: str
    target_audience: str
    valid_from: date
    valid_to: date
    has_attachment: bool
    status: str
    published_at: datetime | None
    server_date: datetime

    class Config:
        from_attributes = True


class FaqCreate(BaseModel):
    question: str = Field(min_length=5)
    answer: str = Field(min_length=5)
    category: str
    display_order: int = 0


class FaqOut(BaseModel):
    id: int
    question: str
    answer: str
    category: str
    display_order: int
    status: str

    class Config:
        from_attributes = True


class ArrearInstalmentOut(BaseModel):
    id: int
    instalment_number: int
    scheduled_pay_month: date
    scheduled_amount: float
    paid_pay_month: date | None
    paid_amount: float | None
    status: str
    pension_slip_id: int | None
    disbursement_record_id: int | None

    class Config:
        from_attributes = True


class ArrearCaseOut(BaseModel):
    id: int
    arrear_type: str
    order_reference: str
    order_date: date
    period_from: date
    period_to: date
    sanctioned_amount: float
    paid_amount: float
    balance_amount: float
    status: str
    instalments: list[ArrearInstalmentOut]

    class Config:
        from_attributes = True


class AdjustmentEntryOut(BaseModel):
    id: int
    adjustment_type: str
    reason: str
    authority: str
    total_amount: float
    recovered_amount: float
    balance_amount: float
    status: str

    class Config:
        from_attributes = True


class BenefitEntitlementOut(BaseModel):
    id: int
    benefit_type: str
    rate_amount: float
    effective_from: date
    effective_to: date | None
    next_review_date: date | None
    status: str

    class Config:
        from_attributes = True


class BenefitClaimCreate(BaseModel):
    benefit_type: str
    details: str = Field(min_length=10)
    document_uploaded: bool = False


class BenefitClaimOut(BaseModel):
    id: int
    benefit_type: str
    details: str
    document_uploaded: bool
    status: str
    review_remarks: str | None
    reviewed_at: datetime | None
    server_date: datetime
    due_date: date
    is_breached: bool
    escalated: bool
    escalated_at: datetime | None

    class Config:
        from_attributes = True


class RequestEventOut(BaseModel):
    action: str
    remarks: str | None
    server_date: datetime


class RequestSummaryOut(BaseModel):
    """Unified row for the 'My Requests' screen (FR-PP-101), covering every
    request type the pensioner has raised that carries an officer review."""

    request_type: str  # "Bank account change" | "Grievance"
    request_id: int
    request_number: str
    title: str
    status: str
    submitted_on: datetime
    due_date: date
    is_breached: bool
    disposed_on: datetime | None
    escalated: bool
    events: list[RequestEventOut]


class ApproverQueueItem(BaseModel):
    id: int
    item_type: str  # "bank_request" | "benefit_claim"
    pensioner_id: int
    pensioner_name: str
    title: str
    status: str
    server_date: datetime
