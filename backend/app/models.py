from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
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
