import { useEffect, useMemo, useState } from "react";
import { downloadFile, get } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";

const monthFormatter = new Intl.DateTimeFormat("en-IN", { month: "short", year: "numeric" });
const paymentTypes = ["Regular pension", "Arrear", "Benefit", "Other"];

function financialYearOf(dateStr) {
  const d = new Date(dateStr);
  const startYear = d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1;
  return `${startYear}-${String(startYear + 1).slice(2)}`;
}

const statusStyles = {
  Credited: "bg-green-50 text-green-700 border-green-200",
  "Passed for payment": "bg-amber-50 text-amber-700 border-amber-200",
  Returned: "bg-red-50 text-red-700 border-red-200",
  Reversed: "bg-red-50 text-red-700 border-red-200",
};

export default function DisbursementHistory() {
  const { t } = useLanguage();
  const [allRecords, setAllRecords] = useState(null);
  const [paymentType, setPaymentType] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [financialYear, setFinancialYear] = useState("");

  function load() {
    const params = new URLSearchParams();
    if (paymentType) params.set("payment_type", paymentType);
    if (fromDate) params.set("from_date", fromDate);
    if (toDate) params.set("to_date", toDate);
    get(`/disbursements?${params.toString()}`).then(setAllRecords);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paymentType, fromDate, toDate]);

  const financialYears = useMemo(() => {
    if (!allRecords) return [];
    return [...new Set(allRecords.map((r) => financialYearOf(r.pay_month)))].sort().reverse();
  }, [allRecords]);

  const visibleRecords = useMemo(() => {
    if (!allRecords) return [];
    if (!financialYear) return allRecords;
    return allRecords.filter((r) => financialYearOf(r.pay_month) === financialYear);
  }, [allRecords, financialYear]);

  return (
    <AppLayout>
      <div className="bg-white border border-slate-200 rounded p-6">
        <div className="flex items-start justify-between flex-wrap gap-3 mb-1">
          <h1 className="font-semibold text-slate-800">{t("Disbursement history")}</h1>
          {financialYear && (
            <button
              onClick={() =>
                downloadFile(
                  `/disbursements/certificate/pdf?financial_year=${financialYear}`,
                  `disbursement-certificate-${financialYear}.pdf`
                )
              }
              className="text-xs font-medium text-blue-800 border border-blue-700 rounded px-2.5 py-1.5 hover:bg-blue-50 whitespace-nowrap"
            >
              {t("Download certified statement")}
            </button>
          )}
        </div>
        <p className="text-sm text-slate-500 mb-5">{t("Every payment recorded in IFMS, with filters below.")}</p>

        <div className="flex flex-wrap gap-3 mb-5">
          <select
            className="border border-slate-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
            value={financialYear}
            onChange={(e) => setFinancialYear(e.target.value)}
          >
            <option value="">{t("All financial years")}</option>
            {financialYears.map((fy) => (
              <option key={fy} value={fy}>
                FY {fy}
              </option>
            ))}
          </select>
          <select
            className="border border-slate-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
            value={paymentType}
            onChange={(e) => setPaymentType(e.target.value)}
          >
            <option value="">{t("All payment types")}</option>
            {paymentTypes.map((pt) => (
              <option key={pt} value={pt}>
                {t(pt)}
              </option>
            ))}
          </select>
          <input
            type="date"
            className="border border-slate-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
          />
          <span className="text-slate-400 text-sm self-center">{t("to")}</span>
          <input
            type="date"
            className="border border-slate-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
            value={toDate}
            onChange={(e) => setToDate(e.target.value)}
          />
        </div>

        {!allRecords ? (
          <p className="text-sm text-slate-500">{t("Loading...")}</p>
        ) : visibleRecords.length === 0 ? (
          <p className="text-sm text-slate-500">{t("No disbursement records match these filters.")}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                  <th className="py-2 pr-4">{t("Pay month")}</th>
                  <th className="py-2 pr-4">{t("Type")}</th>
                  <th className="py-2 pr-4">{t("Voucher")}</th>
                  <th className="py-2 pr-4">{t("Paid date")}</th>
                  <th className="py-2 pr-4 text-right">{t("Amount")}</th>
                  <th className="py-2 pr-4">{t("Mode")}</th>
                  <th className="py-2">{t("Status")}</th>
                </tr>
              </thead>
              <tbody>
                {visibleRecords.map((r) => (
                  <tr key={r.id} className="border-b border-slate-100 last:border-0 align-top">
                    <td className="py-2 pr-4 font-medium text-slate-800">
                      {monthFormatter.format(new Date(r.pay_month))}
                    </td>
                    <td className="py-2 pr-4">{t(r.payment_type)}</td>
                    <td className="py-2 pr-4 text-slate-500">{r.voucher_number}</td>
                    <td className="py-2 pr-4">{r.paid_date || "-"}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">Rs. {r.paid_amount}</td>
                    <td className="py-2 pr-4">{r.mode_of_payment}</td>
                    <td className="py-2">
                      <span
                        className={`inline-block text-xs font-medium px-2 py-0.5 rounded border ${
                          statusStyles[r.credit_status] || "bg-slate-100 text-slate-600 border-slate-200"
                        }`}
                      >
                        {t(r.credit_status)}
                      </span>
                      {r.status_reason && <p className="text-xs text-slate-500 mt-1">{r.status_reason}</p>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <p className="text-xs text-slate-400 mt-5">
          {t("Source: IFMS Pension Payment and Bill")} &middot; {t("synced")} {new Date().toISOString().slice(0, 10)}
        </p>
      </div>
    </AppLayout>
  );
}
