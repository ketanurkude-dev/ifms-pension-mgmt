import os
from datetime import datetime

from fpdf import FPDF

from app.models import Pensioner
from app.signing import SIGNER_NAME, sign_pdf

# Every generated PDF shares this letterhead + footer so they look like they
# belong to the same system. Kept deliberately plain (no logos/QR) --
# this is a prototype, not a production document generator.

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")

# Per FR-PP-129: PDFs must render Devanagari correctly, not as an image.
# Noto Sans Devanagari also covers basic Latin, so one font family is used
# for both languages -- avoids width/metric mismatches from font-switching
# mid-document.
PDF_HI = {
    "Government of NCT of Delhi": "राष्ट्रीय राजधानी क्षेत्र दिल्ली सरकार",
    "Integrated Financial Management System - Pensioner Portal": "एकीकृत वित्तीय प्रबंधन प्रणाली - पेंशनभोगी पोर्टल",
    "Reference": "संदर्भ",
    "Generated on": "पर तैयार किया गया",
    "Digitally signed by": "द्वारा डिजिटल हस्ताक्षरित",
    "This is a computer-generated statement from IFMS. Prototype - mock data only.":
        "यह आईएफएमएस से कंप्यूटर-जनित विवरण है। प्रोटोटाइप - केवल नमूना डेटा।",
    "Pensioner name": "पेंशनभोगी का नाम",
    "PPO number": "पीपीओ नंबर",
    "Retired from": "सेवानिवृत्ति स्थान",
    "Bank account (masked)": "बैंक खाता (छिपा हुआ)",
    "Pension Slip": "पेंशन पर्ची",
    "Payments": "भुगतान",
    "Deductions": "कटौती",
    "Basic pension": "मूल पेंशन",
    "Dearness relief": "महंगाई राहत",
    "Additional pension (age)": "अतिरिक्त पेंशन (आयु)",
    "Fixed medical allowance": "निश्चित चिकित्सा भत्ता",
    "Constant attendant allowance": "स्थायी परिचारक भत्ता",
    "Arrear instalment": "बकाया किस्त",
    "Other allowances": "अन्य भत्ते",
    "Gross": "सकल",
    "Income tax": "आयकर",
    "Commutation recovery": "कम्यूटेशन वसूली",
    "Overpayment recovery": "अधिक भुगतान वसूली",
    "Court attachment": "न्यायालय संलग्नक",
    "Other recoveries": "अन्य वसूली",
    "Total deductions": "कुल कटौती",
    "Net pension": "नेट पेंशन",
    "Disbursing office": "संवितरण कार्यालय",
    "Treasury code": "कोषागार कोड",
    "Bill number": "बिल संख्या",
    "Voucher number": "वाउचर संख्या",
    "Annual Pension Statement": "वार्षिक पेंशन विवरण",
    "Month": "माह",
    "Net": "नेट",
    "Total": "कुल",
    "Issuing office": "जारीकर्ता कार्यालय",
    "Issued on": "जारी तिथि",
    "Summary for the financial year": "वित्तीय वर्ष का सारांश",
    "Total pension paid": "कुल पेंशन भुगतान",
    "Total tax deducted at source": "स्रोत पर कुल कर कटौती",
    "Grievance Acknowledgement": "शिकायत पावती",
    "Grievance details": "शिकायत विवरण",
    "Grievance number": "शिकायत संख्या",
    "Category": "श्रेणी",
    "Lodged on": "दर्ज तिथि",
    "Service level due date": "सेवा स्तर देय तिथि",
    "Description": "विवरण",
    "Arrears & Benefits Statement": "बकाया एवं लाभ विवरण",
    "as at": "इस तिथि तक",
    "Arrear cases": "बकाया मामले",
    "No arrear cases on record.": "रिकॉर्ड में कोई बकाया मामला नहीं।",
    "Type": "प्रकार",
    "Order ref.": "आदेश संदर्भ",
    "Sanctioned": "स्वीकृत",
    "Paid": "भुगतान किया गया",
    "Balance": "शेष",
    "Status": "स्थिति",
    "Adjustments and recoveries": "समायोजन एवं वसूली",
    "No adjustment or recovery entries on record.": "रिकॉर्ड में कोई समायोजन या वसूली प्रविष्टि नहीं।",
    "Authority": "प्राधिकरण",
    "Recovered": "वसूल किया गया",
    "Benefit entitlements": "लाभ हक",
    "No benefit entitlements on record.": "रिकॉर्ड में कोई लाभ हक नहीं।",
    "Benefit": "लाभ",
    "Effective from": "प्रभावी तिथि (से)",
    "Effective to": "प्रभावी तिथि (तक)",
    "Certified Statement of Pension Paid": "पेंशन भुगतान का प्रमाणित विवरण",
    "This is to certify that the amounts below were disbursed to":
        "यह प्रमाणित किया जाता है कि नीचे दी गई राशियां वितरित की गईं",
    "during Financial Year": "वित्तीय वर्ष के दौरान",
    "as recorded in IFMS.": "जैसा कि आईएफएमएस में दर्ज है।",
    "Pay month": "भुगतान माह",
    "Total credited during": "के दौरान कुल जमा",
    "Paid date": "भुगतान तिथि",
    "Amount": "राशि",
}


def _t(language: str, key: str) -> str:
    if language == "hi":
        return PDF_HI.get(key, key)
    return key


def _mask_account(account_number: str) -> str:
    if len(account_number) <= 4:
        return account_number
    return "X" * (len(account_number) - 4) + account_number[-4:]


def _register_font(pdf: FPDF) -> None:
    pdf.add_font("Noto", "", os.path.join(FONT_DIR, "NotoSansDevanagari.ttf"))
    pdf.add_font("Noto", "B", os.path.join(FONT_DIR, "NotoSansDevanagari-Bold.ttf"))
    # Use the bold face for italic too -- there's no separate italic file,
    # and this only affects the small italic footer note.
    pdf.add_font("Noto", "I", os.path.join(FONT_DIR, "NotoSansDevanagari.ttf"))


def _new_pdf(title: str, language: str = "en") -> FPDF:
    pdf = FPDF()
    _register_font(pdf)
    pdf.add_page()
    pdf.set_font("Noto", "B", 14)
    pdf.cell(0, 8, _t(language, "Government of NCT of Delhi"), ln=True, align="C")
    pdf.set_font("Noto", "", 10)
    pdf.cell(0, 6, _t(language, "Integrated Financial Management System - Pensioner Portal"), ln=True, align="C")
    pdf.ln(4)
    pdf.set_font("Noto", "B", 12)
    pdf.cell(0, 8, title, ln=True, align="C")
    pdf.ln(4)
    return pdf


def _footer(pdf: FPDF, reference: str, language: str = "en") -> None:
    pdf.ln(10)
    pdf.set_font("Noto", "I", 8)
    pdf.multi_cell(
        0,
        5,
        f"{_t(language, 'Reference')}: {reference}\n"
        f"{_t(language, 'Generated on')} {datetime.utcnow().strftime('%d-%m-%Y %H:%M')} UTC.\n"
        f"{_t(language, 'Digitally signed by')} {SIGNER_NAME}.\n"
        f"{_t(language, 'This is a computer-generated statement from IFMS. Prototype - mock data only.')}",
    )


def _pensioner_block(pdf: FPDF, pensioner: Pensioner, language: str = "en") -> None:
    pdf.set_font("Noto", "", 10)
    rows = [
        (_t(language, "Pensioner name"), pensioner.name),
        (_t(language, "PPO number"), pensioner.ppo_number),
        (_t(language, "Retired from"), pensioner.retired_from_office),
        (_t(language, "Bank account (masked)"), _mask_account(pensioner.bank_account_number)),
    ]
    for label, value in rows:
        pdf.cell(55, 6, label)
        pdf.cell(0, 6, str(value), ln=True)
    pdf.ln(2)


def _kv_table(pdf: FPDF, rows: list[tuple[str, str]]) -> None:
    pdf.set_font("Noto", "", 10)
    for label, value in rows:
        pdf.cell(90, 7, label, border=1)
        pdf.cell(0, 7, str(value), border=1, ln=True, align="R")


def build_pension_slip_pdf(pensioner: Pensioner, slip, language: str = "en") -> bytes:
    t = lambda key: _t(language, key)  # noqa: E731
    pdf = _new_pdf(f"{t('Pension Slip')} - {slip.month.strftime('%B %Y')}", language)
    _pensioner_block(pdf, pensioner, language)

    pdf.set_font("Noto", "", 10)
    pdf.cell(0, 6, f"{t('Disbursing office')}: {slip.disbursing_office}    {t('Treasury code')}: {slip.treasury_code}", ln=True)
    pdf.cell(0, 6, f"{t('Bill number')}: {slip.bill_number}    {t('Voucher number')}: {slip.voucher_number}", ln=True)
    pdf.ln(3)

    pdf.set_font("Noto", "B", 10)
    pdf.cell(0, 7, t("Payments"), ln=True)
    _kv_table(
        pdf,
        [
            (t("Basic pension"), f"Rs. {slip.basic_pension}"),
            (t("Dearness relief"), f"Rs. {slip.dearness_relief}"),
            (t("Additional pension (age)"), f"Rs. {slip.additional_pension_age}"),
            (t("Fixed medical allowance"), f"Rs. {slip.fixed_medical_allowance}"),
            (t("Constant attendant allowance"), f"Rs. {slip.constant_attendant_allowance}"),
            (t("Arrear instalment"), f"Rs. {slip.arrear_instalment}"),
            (t("Other allowances"), f"Rs. {slip.other_allowances}"),
            (t("Gross"), f"Rs. {slip.gross}"),
        ],
    )
    pdf.ln(3)
    pdf.set_font("Noto", "B", 10)
    pdf.cell(0, 7, t("Deductions"), ln=True)
    _kv_table(
        pdf,
        [
            (t("Income tax"), f"Rs. {slip.income_tax}"),
            (t("Commutation recovery"), f"Rs. {slip.commutation_recovery}"),
            (t("Overpayment recovery"), f"Rs. {slip.overpayment_recovery}"),
            (t("Court attachment"), f"Rs. {slip.court_attachment}"),
            (t("Other recoveries"), f"Rs. {slip.other_recoveries}"),
            (t("Total deductions"), f"Rs. {slip.deductions}"),
        ],
    )
    pdf.ln(3)
    pdf.set_font("Noto", "B", 11)
    pdf.cell(90, 8, t("Net pension"), border=1)
    pdf.cell(0, 8, f"Rs. {slip.net}", border=1, ln=True, align="R")

    _footer(pdf, f"SLIP/{pensioner.ppo_number}/{slip.month.strftime('%Y%m')}", language)
    return sign_pdf(bytes(pdf.output()), reason=f"Pension slip for {slip.month.strftime('%B %Y')}")


def build_annual_pension_statement_pdf(pensioner: Pensioner, slips: list, year_label: str, language: str = "en") -> bytes:
    t = lambda key: _t(language, key)  # noqa: E731
    pdf = _new_pdf(f"{t('Annual Pension Statement')} - {year_label}", language)
    _pensioner_block(pdf, pensioner, language)

    pdf.set_font("Noto", "B", 9)
    headers = [t("Month"), t("Gross"), t("Deductions"), t("Net")]
    widths = [40, 45, 45, 45]
    for header, width in zip(headers, widths):
        pdf.cell(width, 7, header, border=1)
    pdf.ln()

    pdf.set_font("Noto", "", 9)
    total_gross = total_deductions = total_net = 0.0
    for slip in slips:
        values = [slip.month.strftime("%b %Y"), f"Rs. {slip.gross}", f"Rs. {slip.deductions}", f"Rs. {slip.net}"]
        for value, width in zip(values, widths):
            pdf.cell(width, 7, str(value), border=1)
        pdf.ln()
        total_gross += float(slip.gross)
        total_deductions += float(slip.deductions)
        total_net += float(slip.net)

    pdf.set_font("Noto", "B", 9)
    totals = [t("Total"), f"Rs. {total_gross:.2f}", f"Rs. {total_deductions:.2f}", f"Rs. {total_net:.2f}"]
    for value, width in zip(totals, widths):
        pdf.cell(width, 7, str(value), border=1)
    pdf.ln()

    _footer(pdf, f"ANNUAL/{pensioner.ppo_number}/{year_label}", language)
    return sign_pdf(bytes(pdf.output()), reason=f"Annual pension statement {year_label}")


def build_tax_document_pdf(
    pensioner: Pensioner, document, total_pension_paid: float, total_tax_deducted: float, language: str = "en"
) -> bytes:
    t = lambda key: _t(language, key)  # noqa: E731
    pdf = _new_pdf(f"{document.doc_type} - FY {document.financial_year}", language)
    _pensioner_block(pdf, pensioner, language)

    pdf.set_font("Noto", "", 10)
    pdf.cell(0, 6, f"{t('Issuing office')}: {document.issuing_office}", ln=True)
    pdf.cell(0, 6, f"{t('Issued on')}: {document.issued_on}", ln=True)
    pdf.ln(4)

    pdf.set_font("Noto", "B", 10)
    pdf.cell(0, 7, t("Summary for the financial year"), ln=True)
    _kv_table(
        pdf,
        [
            (t("Total pension paid"), f"Rs. {total_pension_paid:.2f}"),
            (t("Total tax deducted at source"), f"Rs. {total_tax_deducted:.2f}"),
        ],
    )

    _footer(pdf, f"TAX/{pensioner.ppo_number}/{document.financial_year}/{document.doc_type.replace(' ', '')}", language)
    return sign_pdf(bytes(pdf.output()), reason=f"{document.doc_type} for FY {document.financial_year}")


def build_grievance_acknowledgement_pdf(pensioner: Pensioner, grievance, language: str = "en") -> bytes:
    """Printable acknowledgement issued on lodging a grievance, per FR-PP-110."""
    t = lambda key: _t(language, key)  # noqa: E731
    pdf = _new_pdf(t("Grievance Acknowledgement"), language)
    _pensioner_block(pdf, pensioner, language)

    pdf.set_font("Noto", "B", 10)
    pdf.cell(0, 7, t("Grievance details"), ln=True)
    _kv_table(
        pdf,
        [
            (t("Grievance number"), grievance.grievance_number),
            (t("Category"), grievance.category),
            (t("Lodged on"), grievance.server_date.strftime("%d-%m-%Y %H:%M")),
            (t("Service level due date"), grievance.due_date.strftime("%d-%m-%Y")),
        ],
    )
    pdf.ln(4)
    pdf.set_font("Noto", "", 10)
    pdf.multi_cell(0, 6, f"{t('Description')}: {grievance.description}")

    _footer(pdf, grievance.grievance_number, language)
    return sign_pdf(bytes(pdf.output()), reason=f"Grievance acknowledgement {grievance.grievance_number}")


def build_arrears_benefits_statement_pdf(
    pensioner: Pensioner, as_of: datetime, cases: list, adjustments: list, benefits: list, language: str = "en"
) -> bytes:
    """Printable arrear and benefit statement as at a chosen date, per FR-PP-056."""
    t = lambda key: _t(language, key)  # noqa: E731
    pdf = _new_pdf(f"{t('Arrears & Benefits Statement')} - {t('as at')} {as_of.strftime('%d-%m-%Y')}", language)
    _pensioner_block(pdf, pensioner, language)

    pdf.set_font("Noto", "B", 10)
    pdf.cell(0, 7, t("Arrear cases"), ln=True)
    if not cases:
        pdf.set_font("Noto", "", 9)
        pdf.cell(0, 6, t("No arrear cases on record."), ln=True)
    else:
        pdf.set_font("Noto", "B", 8)
        headers = [t("Type"), t("Order ref."), t("Sanctioned"), t("Paid"), t("Balance"), t("Status")]
        widths = [40, 30, 27, 27, 27, 29]
        for header, width in zip(headers, widths):
            pdf.cell(width, 7, header, border=1)
        pdf.ln()
        pdf.set_font("Noto", "", 8)
        for case in cases:
            balance = float(case.sanctioned_amount) - float(case.paid_amount)
            values = [
                case.arrear_type,
                case.order_reference,
                f"Rs. {case.sanctioned_amount}",
                f"Rs. {case.paid_amount}",
                f"Rs. {balance:.2f}",
                case.status,
            ]
            for value, width in zip(values, widths):
                pdf.cell(width, 7, str(value), border=1)
            pdf.ln()
    pdf.ln(3)

    pdf.set_font("Noto", "B", 10)
    pdf.cell(0, 7, t("Adjustments and recoveries"), ln=True)
    if not adjustments:
        pdf.set_font("Noto", "", 9)
        pdf.cell(0, 6, t("No adjustment or recovery entries on record."), ln=True)
    else:
        pdf.set_font("Noto", "B", 8)
        headers = [t("Type"), t("Authority"), t("Total"), t("Recovered"), t("Balance"), t("Status")]
        widths = [35, 40, 27, 27, 27, 24]
        for header, width in zip(headers, widths):
            pdf.cell(width, 7, header, border=1)
        pdf.ln()
        pdf.set_font("Noto", "", 8)
        for adj in adjustments:
            balance = float(adj.total_amount) - float(adj.recovered_amount)
            values = [
                adj.adjustment_type,
                adj.authority,
                f"Rs. {adj.total_amount}",
                f"Rs. {adj.recovered_amount}",
                f"Rs. {balance:.2f}",
                adj.status,
            ]
            for value, width in zip(values, widths):
                pdf.cell(width, 7, str(value), border=1)
            pdf.ln()
    pdf.ln(3)

    pdf.set_font("Noto", "B", 10)
    pdf.cell(0, 7, t("Benefit entitlements"), ln=True)
    if not benefits:
        pdf.set_font("Noto", "", 9)
        pdf.cell(0, 6, t("No benefit entitlements on record."), ln=True)
    else:
        pdf.set_font("Noto", "B", 8)
        headers = [t("Benefit"), t("Effective from"), t("Effective to"), t("Status")]
        widths = [55, 45, 45, 35]
        for header, width in zip(headers, widths):
            pdf.cell(width, 7, header, border=1)
        pdf.ln()
        pdf.set_font("Noto", "", 8)
        for benefit in benefits:
            values = [
                benefit.benefit_type,
                benefit.effective_from.strftime("%d-%m-%Y"),
                benefit.effective_to.strftime("%d-%m-%Y") if benefit.effective_to else "-",
                benefit.status,
            ]
            for value, width in zip(values, widths):
                pdf.cell(width, 7, str(value), border=1)
            pdf.ln()

    _footer(pdf, f"ARR-BEN/{pensioner.ppo_number}/{as_of.strftime('%Y%m%d')}", language)
    return sign_pdf(bytes(pdf.output()), reason="Arrears and benefits statement")


def build_disbursement_certificate_pdf(pensioner: Pensioner, records: list, year_label: str, language: str = "en") -> bytes:
    """A certified statement of pension paid during a financial year, for
    submission to a bank or income-tax authority (FR-PP-062)."""
    t = lambda key: _t(language, key)  # noqa: E731
    pdf = _new_pdf(f"{t('Certified Statement of Pension Paid')} - {year_label}", language)
    _pensioner_block(pdf, pensioner, language)

    pdf.set_font("Noto", "", 10)
    pdf.multi_cell(
        0,
        6,
        f"{t('This is to certify that the amounts below were disbursed to')} {pensioner.name} "
        f"(PPO {pensioner.ppo_number}) {t('during Financial Year')} {year_label}, {t('as recorded in IFMS.')}",
    )
    pdf.ln(4)

    pdf.set_font("Noto", "B", 9)
    headers = [t("Pay month"), t("Type"), t("Paid date"), t("Amount"), t("Status")]
    widths = [30, 40, 30, 35, 40]
    for header, width in zip(headers, widths):
        pdf.cell(width, 7, header, border=1)
    pdf.ln()

    pdf.set_font("Noto", "", 9)
    total_paid = 0.0
    for record in records:
        values = [
            record.pay_month.strftime("%b %Y"),
            record.payment_type,
            record.paid_date.strftime("%d-%m-%Y") if record.paid_date else "-",
            f"Rs. {record.paid_amount}",
            record.credit_status,
        ]
        for value, width in zip(values, widths):
            pdf.cell(width, 7, str(value), border=1)
        pdf.ln()
        if record.credit_status == "Credited":
            total_paid += float(record.paid_amount)

    pdf.ln(3)
    pdf.set_font("Noto", "B", 10)
    pdf.cell(0, 7, f"{t('Total credited during')} {year_label}: Rs. {total_paid:.2f}", ln=True)

    _footer(pdf, f"CERT-DISB/{pensioner.ppo_number}/{year_label}", language)
    return sign_pdf(bytes(pdf.output()), reason=f"Certified disbursement statement {year_label}")
