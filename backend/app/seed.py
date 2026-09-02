from datetime import date

from app.models import (
    AdjustmentEntry,
    ArrearCase,
    ArrearInstalment,
    BenefitEntitlement,
    DisbursementRecord,
    PensionSlip,
    TaxDocument,
)


def financial_year_label(d: date) -> str:
    """Indian financial year runs April to March, e.g. "2026-27"."""
    start_year = d.year if d.month >= 4 else d.year - 1
    return f"{start_year}-{str(start_year + 1)[2:]}"


def previous_financial_year_label() -> str:
    today = date.today()
    end_year = today.year if today.month >= 4 else today.year - 1
    start_year = end_year - 1
    return f"{start_year}-{str(end_year)[2:]}"


def months_back(count: int) -> list[date]:
    """First-of-month dates for the last `count` months, oldest first."""
    today = date.today()
    months = []
    for months_ago in range(count - 1, -1, -1):
        year = today.year
        month = today.month - months_ago
        while month <= 0:
            month += 12
            year -= 1
        months.append(date(year, month, 1))
    return months


def build_pension_slips(pensioner_id: int, basic_pension: float, retired_from_office: str) -> list[PensionSlip]:
    """Create 12 months of mock pension slips for a newly registered
    pensioner, so the Pension Slip page has data right away. The current
    month is left unpublished, like a real pension bill cycle."""

    dearness_relief = round(basic_pension * 0.46, 2)  # roughly current DR rate
    fixed_medical_allowance = 1000.00  # standard flat amount
    gross = round(basic_pension + dearness_relief + fixed_medical_allowance, 2)

    income_tax = round(gross * 0.03, 2)
    deductions = income_tax
    net = round(gross - deductions, 2)

    today = date.today()
    slips = []
    for index, slip_month in enumerate(months_back(12)):
        is_current_month = slip_month.year == today.year and slip_month.month == today.month
        slips.append(
            PensionSlip(
                pensioner_id=pensioner_id,
                month=slip_month,
                basic_pension=basic_pension,
                dearness_relief=dearness_relief,
                fixed_medical_allowance=fixed_medical_allowance,
                income_tax=income_tax,
                gross=gross,
                deductions=deductions,
                net=net,
                disbursing_office=retired_from_office,
                treasury_code="DEL-TRY-001",
                bill_number=f"BILL/{slip_month.strftime('%Y%m')}/{pensioner_id:04d}",
                voucher_number=f"VCH/{slip_month.strftime('%Y%m')}/{pensioner_id:04d}{index:02d}",
                published_on=None if is_current_month else date(slip_month.year, slip_month.month, 7),
            )
        )
    return slips


def build_tax_documents(pensioner_id: int, issuing_office: str) -> list[TaxDocument]:
    """Issue Form 16 and related documents for the last completed financial
    year, so the Tax Documents list has something real to download."""

    fy = previous_financial_year_label()
    end_year = int(fy.split("-")[0]) + 1
    issued_on = date(end_year, 6, 15)  # Form 16 is typically issued by mid-June

    doc_types = [
        "Form 16 Part A",
        "Form 16 Part B",
        "Annual Tax Computation Sheet",
        "Certificate of Tax Deducted",
    ]
    return [
        TaxDocument(
            pensioner_id=pensioner_id,
            financial_year=fy,
            doc_type=doc_type,
            issued_on=issued_on,
            issuing_office=issuing_office,
        )
        for doc_type in doc_types
    ]


def add_months(d: date, count: int) -> date:
    month = d.month - 1 + count
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)


def build_arrear_case_and_instalments(
    pensioner_id: int, basic_pension: float, slips: list[PensionSlip], records: list[DisbursementRecord]
) -> tuple[ArrearCase, list[ArrearInstalment]]:
    """One dearness-relief revision arrear case, partly paid, so the Arrears
    & Benefits page has a realistic in-progress case to show (FR-PP-046/047)."""

    published_slips = [s for s in slips if s.published_on]
    # The order was raised a couple of months before the first instalment
    # was actually paid out, which is the oldest published slip we have.
    paid_slip = published_slips[0] if published_slips else None
    order_date = add_months(paid_slip.month, -2) if paid_slip else date.today()
    period_from = order_date
    period_to = add_months(order_date, 3)

    instalment_amount = round(basic_pension * 0.05, 2)
    total_instalments = 3
    sanctioned_amount = round(instalment_amount * total_instalments, 2)

    paid_record = None
    if paid_slip:
        paid_record = next((r for r in records if r.pension_slip_id == paid_slip.id or r.pay_month == paid_slip.month), None)

    paid_amount = instalment_amount if paid_slip else 0
    case = ArrearCase(
        pensioner_id=pensioner_id,
        arrear_type="Dearness relief revision arrears",
        order_reference=f"DA-REV/{order_date.strftime('%Y')}/{pensioner_id:05d}",
        order_date=order_date,
        period_from=period_from,
        period_to=period_to,
        sanctioned_amount=sanctioned_amount,
        paid_amount=paid_amount,
        status="Partly paid" if paid_slip else "Sanctioned",
    )

    first_scheduled_month = paid_slip.month if paid_slip else add_months(date.today(), 1)
    instalments = []
    for i in range(total_instalments):
        is_first = i == 0
        instalments.append(
            ArrearInstalment(
                instalment_number=i + 1,
                scheduled_pay_month=add_months(first_scheduled_month, i),
                scheduled_amount=instalment_amount,
                paid_pay_month=paid_slip.month if (is_first and paid_slip) else None,
                paid_amount=instalment_amount if (is_first and paid_slip) else None,
                status="Paid" if (is_first and paid_slip) else "Pending",
                pension_slip_id=paid_slip.id if (is_first and paid_slip) else None,
                disbursement_record_id=paid_record.id if (is_first and paid_record) else None,
            )
        )
    return case, instalments


def build_adjustment_entries(pensioner_id: int) -> list[AdjustmentEntry]:
    """A single ongoing overpayment recovery, per FR-PP-049."""
    total = 6000.00
    recovered = 2000.00
    return [
        AdjustmentEntry(
            pensioner_id=pensioner_id,
            adjustment_type="Overpayment recovery",
            reason="Excess dearness relief credited for two months due to a rate revision applied late.",
            authority="Directorate of Pension, GNCTD",
            total_amount=total,
            recovered_amount=recovered,
            status="In progress" if recovered < total else "Closed",
        )
    ]


def build_benefit_entitlements(pensioner_id: int, date_of_birth: date) -> list[BenefitEntitlement]:
    """Standard entitlements every pensioner has, plus the age-linked
    additional pension shown as upcoming or active (FR-PP-050)."""
    today = date.today()
    age = today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))

    entitlements = [
        BenefitEntitlement(
            pensioner_id=pensioner_id,
            benefit_type="Fixed medical allowance",
            rate_amount=1000.00,
            effective_from=date(today.year - 1, 4, 1),
            status="Active",
        )
    ]

    age_80_date = date(date_of_birth.year + 80, date_of_birth.month, date_of_birth.day)
    if age >= 80:
        entitlements.append(
            BenefitEntitlement(
                pensioner_id=pensioner_id,
                benefit_type="Additional pension (age 80+)",
                rate_amount=0,  # a percentage of basic pension in a real deployment; shown as active only here
                effective_from=age_80_date,
                status="Active",
            )
        )
    else:
        entitlements.append(
            BenefitEntitlement(
                pensioner_id=pensioner_id,
                benefit_type="Additional pension (age 80+)",
                rate_amount=0,
                effective_from=age_80_date,
                next_review_date=age_80_date,
                status="Pending review",
            )
        )
    return entitlements


def build_disbursement_records(pensioner_id: int, slips: list[PensionSlip]) -> list[DisbursementRecord]:
    """One disbursement record per published slip, matching its net amount."""
    records = []
    for slip in slips:
        if not slip.published_on:
            continue
        records.append(
            DisbursementRecord(
                pensioner_id=pensioner_id,
                pay_month=slip.month,
                payment_type="Regular pension",
                voucher_number=slip.voucher_number,
                voucher_date=slip.published_on,
                paid_date=slip.published_on,
                paid_amount=slip.net,
                mode_of_payment="Bank transfer",
                bank_reference=f"REF{slip.voucher_number.replace('/', '')}",
                credit_status="Credited",
            )
        )
    return records
