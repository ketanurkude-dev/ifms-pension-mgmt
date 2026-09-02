import { useEffect, useMemo, useState } from "react";
import { downloadFile, get } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";

const monthFormatter = new Intl.DateTimeFormat("en-IN", { month: "short", year: "numeric" });

function formatMonth(dateStr) {
  return monthFormatter.format(new Date(dateStr));
}

// Indian financial year runs April to March, e.g. "2026-27".
function financialYearOf(dateStr) {
  const d = new Date(dateStr);
  const startYear = d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1;
  return `${startYear}-${String(startYear + 1).slice(2)}`;
}

export default function PensionSlip() {
  const { t } = useLanguage();
  const [slips, setSlips] = useState(null);
  const [selected, setSelected] = useState(null);
  const [financialYear, setFinancialYear] = useState("");

  useEffect(() => {
    get("/pension/slips").then((data) => {
      setSlips(data);
      const published = data.find((s) => s.published_on);
      setSelected(published || null);
      setFinancialYear(published ? financialYearOf(published.month) : financialYearOf(new Date().toISOString()));
    });
  }, []);

  const financialYears = useMemo(() => {
    if (!slips) return [];
    return [...new Set(slips.map((s) => financialYearOf(s.month)))].sort().reverse();
  }, [slips]);

  const visibleSlips = useMemo(() => {
    if (!slips) return [];
    return slips.filter((s) => financialYearOf(s.month) === financialYear);
  }, [slips, financialYear]);

  const yearTotals = useMemo(() => {
    const published = visibleSlips.filter((s) => s.published_on);
    return published.reduce(
      (acc, s) => ({
        gross: acc.gross + s.gross,
        deductions: acc.deductions + s.deductions,
        net: acc.net + s.net,
      }),
      { gross: 0, deductions: 0, net: 0 }
    );
  }, [visibleSlips]);

  if (!slips) {
    return (
      <AppLayout>
        <p className="text-slate-500 text-sm">{t("Loading...")}</p>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded p-6">
          <div className="flex items-start justify-between flex-wrap gap-3 mb-1">
            <h1 className="font-semibold text-slate-800">{t("Pension slips")}</h1>
            <div className="flex items-center gap-2">
              <select
                className="border border-slate-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={financialYear}
                onChange={(e) => setFinancialYear(e.target.value)}
              >
                {financialYears.map((fy) => (
                  <option key={fy} value={fy}>
                    FY {fy}
                  </option>
                ))}
              </select>
              <button
                onClick={() =>
                  downloadFile(
                    `/pension/slips/annual-statement/pdf?financial_year=${financialYear}`,
                    `pension-annual-statement-${financialYear}.pdf`
                  )
                }
                className="text-xs font-medium text-blue-800 border border-blue-700 rounded px-2.5 py-1.5 hover:bg-blue-50 whitespace-nowrap"
              >
                {t("Download annual statement")}
              </button>
            </div>
          </div>
          <p className="text-sm text-slate-500 mb-5">{t("Click a month to see the component break-up.")}</p>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                  <th className="py-2 pr-4">{t("Month")}</th>
                  <th className="py-2 pr-4 text-right">{t("Gross")}</th>
                  <th className="py-2 pr-4 text-right">{t("Deductions")}</th>
                  <th className="py-2 pr-4 text-right">{t("Net")}</th>
                  <th className="py-2">{t("Status")}</th>
                </tr>
              </thead>
              <tbody>
                {visibleSlips.map((slip) => (
                  <tr
                    key={slip.month}
                    onClick={() => slip.published_on && setSelected(slip)}
                    className={`border-b border-slate-100 last:border-0 ${
                      slip.published_on ? "cursor-pointer hover:bg-slate-50" : ""
                    } ${selected?.month === slip.month ? "bg-blue-50" : ""}`}
                  >
                    <td className="py-3 pr-4 font-medium text-slate-800">{formatMonth(slip.month)}</td>
                    {slip.published_on ? (
                      <>
                        <td className="py-3 pr-4 text-right tabular-nums">Rs. {slip.gross}</td>
                        <td className="py-3 pr-4 text-right tabular-nums">Rs. {slip.deductions}</td>
                        <td className="py-3 pr-4 text-right tabular-nums font-medium">Rs. {slip.net}</td>
                        <td className="py-3 text-slate-500">{t("Published")} {slip.published_on}</td>
                      </>
                    ) : (
                      <td colSpan={4} className="py-3 text-slate-500 italic">
                        {t("Will be published after bill passing.")}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
              {visibleSlips.some((s) => s.published_on) && (
                <tfoot>
                  <tr className="border-t border-slate-200 font-medium text-slate-800">
                    <td className="py-2 pr-4">{t("Year to date")}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">Rs. {yearTotals.gross.toFixed(2)}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">Rs. {yearTotals.deductions.toFixed(2)}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">Rs. {yearTotals.net.toFixed(2)}</td>
                    <td></td>
                  </tr>
                </tfoot>
              )}
            </table>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded p-6">
          <div className="flex items-start justify-between mb-1">
            <h2 className="font-semibold text-slate-800">
              {selected ? formatMonth(selected.month) : t("Component break-up")}
            </h2>
            {selected && (
              <button
                onClick={() =>
                  downloadFile(`/pension/slips/${selected.id}/pdf`, `pension-slip-${selected.month}.pdf`)
                }
                className="text-xs font-medium text-blue-800 border border-blue-700 rounded px-2.5 py-1 hover:bg-blue-50 shrink-0"
              >
                {t("Download PDF")}
              </button>
            )}
          </div>
          {!selected ? (
            <p className="text-sm text-slate-500">{t("Select a published month to see the break-up.")}</p>
          ) : (
            <div className="text-sm">
              <p className="text-xs text-slate-400 mb-3">
                {selected.disbursing_office} &middot; Bill {selected.bill_number} &middot; Voucher {selected.voucher_number}
              </p>

              <p className="text-xs uppercase tracking-wide text-slate-400 mt-4 mb-2">{t("Payments")}</p>
              <Row label={t("Basic pension")} value={selected.basic_pension} />
              <Row label={t("Dearness relief")} value={selected.dearness_relief} />
              <Row label={t("Fixed medical allowance")} value={selected.fixed_medical_allowance} />
              {selected.additional_pension_age > 0 && (
                <Row label={t("Additional pension (age)")} value={selected.additional_pension_age} />
              )}
              {selected.constant_attendant_allowance > 0 && (
                <Row label={t("Constant attendant allowance")} value={selected.constant_attendant_allowance} />
              )}
              {selected.arrear_instalment > 0 && <Row label={t("Arrear instalment")} value={selected.arrear_instalment} />}
              {selected.other_allowances > 0 && <Row label={t("Other allowances")} value={selected.other_allowances} />}
              <Row label={t("Gross")} value={selected.gross} bold />

              <p className="text-xs uppercase tracking-wide text-slate-400 mt-5 mb-2">{t("Deductions")}</p>
              <Row label={t("Income tax")} value={selected.income_tax} />
              {selected.commutation_recovery > 0 && (
                <Row label={t("Commutation recovery")} value={selected.commutation_recovery} />
              )}
              {selected.overpayment_recovery > 0 && (
                <Row label={t("Overpayment recovery")} value={selected.overpayment_recovery} />
              )}
              {selected.court_attachment > 0 && <Row label={t("Court attachment")} value={selected.court_attachment} />}
              {selected.other_recoveries > 0 && <Row label={t("Other recoveries")} value={selected.other_recoveries} />}
              <Row label={t("Total deductions")} value={selected.deductions} bold />

              <div className="border-t border-slate-200 mt-4 pt-3 flex items-center justify-between">
                <span className="font-semibold text-slate-800">{t("Net pension")}</span>
                <span className="font-semibold text-slate-800 tabular-nums">Rs. {selected.net}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}

function Row({ label, value, bold }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className={bold ? "font-medium text-slate-800" : "text-slate-600"}>{label}</span>
      <span className={`tabular-nums ${bold ? "font-medium text-slate-800" : "text-slate-600"}`}>Rs. {value}</span>
    </div>
  );
}
