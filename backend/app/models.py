from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditMixin:
    """Common columns every table should have. Add this to any new model."""

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    server_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    operation_date: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


# Roles for approval workflow.
ROLES = ["pensioner", "pension_officer"]


class Pensioner(AuditMixin, Base):
    __tablename__ = "pensioners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ppo_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(120), unique=True, nullable=True)
    mobile: Mapped[str] = mapped_column(String(15), nullable=False)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    retired_from_office: Mapped[str] = mapped_column(String(150), nullable=False)
    bank_account_number: Mapped[str] = mapped_column(String(30), nullable=False)
    bank_ifsc: Mapped[str] = mapped_column(String(15), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="pensioner", nullable=False)
    basic_pension: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)  # "en" | "hi"


class PensionSlip(AuditMixin, Base):
    __tablename__ = "pension_slips"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    month: Mapped[date] = mapped_column(Date, nullable=False)

    # Payments, per FR-PP-037
    basic_pension: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    dearness_relief: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    additional_pension_age: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    fixed_medical_allowance: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    constant_attendant_allowance: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    arrear_instalment: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    other_allowances: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    # Deductions, per FR-PP-037
    income_tax: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    commutation_recovery: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    overpayment_recovery: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    court_attachment: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    other_recoveries: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)

    gross: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    deductions: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    net: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Disbursement particulars shown on the slip, per FR-PP-038
    disbursing_office: Mapped[str] = mapped_column(String(150), nullable=False)
    treasury_code: Mapped[str] = mapped_column(String(30), nullable=False)
    bill_number: Mapped[str] = mapped_column(String(30), nullable=False)
    voucher_number: Mapped[str] = mapped_column(String(30), nullable=False)

    published_on: Mapped[date | None] = mapped_column(Date, nullable=True)


class DisbursementRecord(AuditMixin, Base):
    __tablename__ = "disbursement_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    pension_slip_id: Mapped[int | None] = mapped_column(ForeignKey("pension_slips.id"), nullable=True)

    pay_month: Mapped[date] = mapped_column(Date, nullable=False)
    payment_type: Mapped[str] = mapped_column(String(30), default="Regular pension", nullable=False)
    voucher_number: Mapped[str] = mapped_column(String(30), nullable=False)
    voucher_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    mode_of_payment: Mapped[str] = mapped_column(String(30), default="Bank transfer", nullable=False)
    bank_reference: Mapped[str | None] = mapped_column(String(40), nullable=True)
    credit_status: Mapped[str] = mapped_column(String(30), default="Credited", nullable=False)
    status_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class TaxDeclaration(AuditMixin, Base):
    """One header per financial year per pensioner, versioned. Per
    FR-PP-073, a submitted declaration is locked; a further change creates
    a new version rather than editing the submitted one."""

    __tablename__ = "tax_declarations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(10), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    regime: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "Old" | "New"
    other_income: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Draft", nullable=False)  # Draft | Submitted
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    tds_reference: Mapped[str | None] = mapped_column(String(60), nullable=True)


class TaxDeclarationLine(AuditMixin, Base):
    __tablename__ = "tax_declaration_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tax_declaration_id: Mapped[int] = mapped_column(ForeignKey("tax_declarations.id"), nullable=False, index=True)
    section: Mapped[str] = mapped_column(String(20), nullable=False)
    instrument: Mapped[str] = mapped_column(String(120), nullable=False)
    declared_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    proof_uploaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class TaxDocument(AuditMixin, Base):
    __tablename__ = "tax_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    financial_year: Mapped[str] = mapped_column(String(10), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(60), nullable=False)
    issued_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    issuing_office: Mapped[str] = mapped_column(String(150), nullable=False)
    is_superseded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Grievance(AuditMixin, Base):
    """Per FR-PP-107 to FR-PP-118. Status moves Open -> Awaiting
    Clarification -> Open -> Closed, with an optional single Reopened
    cycle per FR-PP-116."""

    __tablename__ = "grievances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    grievance_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional link to the record the grievance is about, per FR-PP-108.
    linked_reference_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    linked_reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    attachment_uploaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[str] = mapped_column(String(30), default="Open", nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Service-level clock pause/resume while awaiting the pensioner's reply, per FR-PP-113.
    clarification_requested_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    clarification_received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("pensioners.id"), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    satisfaction: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Satisfied | Dissatisfied
    reopened_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    escalation_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class GrievanceEvent(AuditMixin, Base):
    """One row per action on a grievance, per FR-PP-114's requirement to
    show every action taken with its date."""

    __tablename__ = "grievance_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grievance_id: Mapped[int] = mapped_column(ForeignKey("grievances.id"), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(40), nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("pensioners.id"), nullable=True)


class Announcement(AuditMixin, Base):
    """Per FR-PP-132. Content is English-only in this build -- the
    bilingual interface itself (PEN_13) is a separate, not-yet-built
    sub-module, so there is no title_hi/body_hi pair yet."""

    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    target_audience: Mapped[str] = mapped_column(String(120), default="All pensioners", nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    has_attachment: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Draft", nullable=False)  # Draft | Published | Withdrawn
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_by: Mapped[int | None] = mapped_column(ForeignKey("pensioners.id"), nullable=True)


class Faq(AuditMixin, Base):
    """Per FR-PP-132, maintained alongside announcements."""

    __tablename__ = "faqs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Active", nullable=False)  # Active | Inactive


class LifeCertificate(AuditMixin, Base):
    """Per FR-PP-120 to FR-PP-125. One row per submission attempt; the
    latest Verified row determines the pensioner's current validity."""

    __tablename__ = "life_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(30), nullable=False)  # Digital (Jeevan Pramaan) | Physical (uploaded)
    reference: Mapped[str] = mapped_column(String(60), nullable=False)
    submitted_on: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Pending verification", nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    verified_by: Mapped[int | None] = mapped_column(ForeignKey("pensioners.id"), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    review_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


class ArrearCase(AuditMixin, Base):
    """Per FR-PP-046. One row per arrear/revision case sanctioned for the
    pensioner (e.g. a DA revision or a pay-commission arrear)."""

    __tablename__ = "arrear_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    arrear_type: Mapped[str] = mapped_column(String(80), nullable=False)
    order_reference: Mapped[str] = mapped_column(String(60), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_from: Mapped[date] = mapped_column(Date, nullable=False)
    period_to: Mapped[date] = mapped_column(Date, nullable=False)
    sanctioned_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Under processing", nullable=False)


class ArrearInstalment(AuditMixin, Base):
    """Per FR-PP-047/FR-PP-048. The pay-out schedule of an arrear case,
    each paid instalment linked to the slip and disbursement it rode on."""

    __tablename__ = "arrear_instalments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    arrear_case_id: Mapped[int] = mapped_column(ForeignKey("arrear_cases.id"), nullable=False, index=True)
    instalment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_pay_month: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    paid_pay_month: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Pending", nullable=False)  # Pending | Paid
    pension_slip_id: Mapped[int | None] = mapped_column(ForeignKey("pension_slips.id"), nullable=True)
    disbursement_record_id: Mapped[int | None] = mapped_column(ForeignKey("disbursement_records.id"), nullable=True)


class AdjustmentEntry(AuditMixin, Base):
    """Per FR-PP-049. Recovery/adjustment entries against the pension."""

    __tablename__ = "adjustment_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    adjustment_type: Mapped[str] = mapped_column(String(60), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    authority: Mapped[str] = mapped_column(String(150), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    recovered_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="In progress", nullable=False)


class BenefitEntitlement(AuditMixin, Base):
    """Per FR-PP-050. Current/past benefit entitlements of the pensioner."""

    __tablename__ = "benefit_entitlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    benefit_type: Mapped[str] = mapped_column(String(80), nullable=False)
    rate_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_review_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Active", nullable=False)


class BenefitClaimRequest(AuditMixin, Base):
    """Per FR-PP-052. A claim for a benefit not currently reflected (e.g.
    fixed medical allowance), reviewed the same way as a bank change
    request."""

    __tablename__ = "benefit_claim_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    benefit_type: Mapped[str] = mapped_column(String(80), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    document_uploaded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Submitted", nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("pensioners.id"), nullable=True)
    review_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class BankChangeRequest(AuditMixin, Base):
    __tablename__ = "bank_change_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pensioner_id: Mapped[int] = mapped_column(ForeignKey("pensioners.id"), nullable=False, index=True)
    new_account_number: Mapped[str] = mapped_column(String(30), nullable=False)
    new_ifsc: Mapped[str] = mapped_column(String(15), nullable=False)
    new_bank_name: Mapped[str] = mapped_column(String(120), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="Submitted", nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("pensioners.id"), nullable=True)
    review_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Per FR-PP-101/106: every trackable request carries a service-level
    # due date and can be escalated once breached.
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Per FR-PP-105: a rejected request can be re-submitted, keeping a link
    # back to the one it replaces so the audit chain is preserved.
    resubmitted_from_id: Mapped[int | None] = mapped_column(ForeignKey("bank_change_requests.id"), nullable=True)
