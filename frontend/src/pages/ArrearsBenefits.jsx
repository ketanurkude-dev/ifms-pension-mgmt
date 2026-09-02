import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { downloadFile, get, post } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";
import { StatusChip } from "./StatusChip";

const CLAIM_TYPES = [
  "Fixed medical allowance",
  "Constant attendant allowance",
  "Additional pension (age)",
  "Restoration of commuted pension",
];

const claimForm = { benefit_type: "", details: "" };

export default function ArrearsBenefits() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [cases, setCases] = useState(null);
  const [adjustments, setAdjustments] = useState(null);
  const [benefits, setBenefits] = useState(null);
  const [claims, setClaims] = useState(null);
  const [expandedCaseId, setExpandedCaseId] = useState(null);
  const [form, setForm] = useState(claimForm);
  const [submitting, setSubmitting] = useState(false);

  function load() {
    get("/arrears-benefits/cases").then(setCases);
    get("/arrears-benefits/adjustments").then(setAdjustments);
    get("/arrears-benefits/entitlements").then(setBenefits);
    get("/arrears-benefits/claims").then(setClaims);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleClaimSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await post("/arrears-benefits/claims", form);
      setForm(claimForm);
      load();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleEscalate(claimId) {
    await post(`/arrears-benefits/claims/${claimId}/escalate`);
    load();
  }

  function raiseGrievance(category, linkedType, linkedId) {
    navigate(
      `/grievances?category=${encodeURIComponent(category)}&linked_type=${linkedType}&linked_id=${linkedId}`
    );
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="bg-white border border-slate-200 rounded p-6">
          <div className="flex items-start justify-between mb-1">
            <h1 className="font-semibold text-slate-800">{t("Arrears & benefits")}</h1>
            <button
              onClick={() => downloadFile("/arrears-benefits/statement/pdf", "arrears-benefits-statement.pdf")}
              className="text-sm text-blue-800 font-medium hover:text-blue-900"
            >
              {t("Download statement")}
            </button>
          </div>
          <p className="text-sm text-slate-500 mb-5">
            {t("Arrear cases, recoveries and benefit entitlements recorded against your pension.")}
          </p>

          <h2 className="text-sm font-semibold text-slate-700 mb-3">{t("Arrear cases")}</h2>
          {!cases ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : cases.length === 0 ? (
            <p className="text-sm text-slate-500 mb-5">{t("No arrear cases on record.")}</p>
          ) : (
            <div className="overflow-x-auto mb-6">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                    <th className="py-2 pr-4">{t("Type")}</th>
                    <th className="py-2 pr-4">{t("Order ref.")}</th>
                    <th className="py-2 pr-4">{t("Period")}</th>
                    <th className="py-2 pr-4">{t("Sanctioned")}</th>
                    <th className="py-2 pr-4">{t("Paid")}</th>
                    <th className="py-2 pr-4">{t("Balance")}</th>
                    <th className="py-2 pr-4">{t("Status")}</th>
                    <th className="py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {cases.map((c) => (
                    <React.Fragment key={c.id}>
                      <tr className="border-b border-slate-100 align-top">
                        <td className="py-2 pr-4">
                          <button
                            onClick={() => setExpandedCaseId(expandedCaseId === c.id ? null : c.id)}
                            className="font-medium text-blue-800 hover:text-blue-900 text-left"
                          >
                            {c.arrear_type}
                          </button>
                        </td>
                        <td className="py-2 pr-4 text-slate-600">{c.order_reference}</td>
                        <td className="py-2 pr-4 text-slate-500">
                          {c.period_from} {t("to")} {c.period_to}
                        </td>
                        <td className="py-2 pr-4">Rs. {c.sanctioned_amount}</td>
                        <td className="py-2 pr-4">Rs. {c.paid_amount}</td>
                        <td className="py-2 pr-4">Rs. {c.balance_amount.toFixed(2)}</td>
                        <td className="py-2 pr-4">
                          <StatusChip status={c.status} />
                        </td>
                        <td className="py-2">
                          <button
                            onClick={() => raiseGrievance("Non-payment of arrears", "arrear_case", c.id)}
                            className="text-xs text-orange-700 font-medium hover:text-orange-800"
                          >
                            {t("Raise grievance")}
                          </button>
                        </td>
                      </tr>
                      {expandedCaseId === c.id && (
                        <tr className="border-b border-slate-100 bg-slate-50">
                          <td colSpan={8} className="py-3 px-4">
                            <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">
                              {t("Instalment schedule")}
                            </p>
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="text-left text-xs text-slate-400">
                                  <th className="py-1 pr-4">#</th>
                                  <th className="py-1 pr-4">{t("Scheduled month")}</th>
                                  <th className="py-1 pr-4">{t("Scheduled amount")}</th>
                                  <th className="py-1 pr-4">{t("Paid month")}</th>
                                  <th className="py-1 pr-4">{t("Paid amount")}</th>
                                  <th className="py-1 pr-4">{t("Status")}</th>
                                </tr>
                              </thead>
                              <tbody>
                                {c.instalments.map((i) => (
                                  <tr key={i.id}>
                                    <td className="py-1 pr-4">{i.instalment_number}</td>
                                    <td className="py-1 pr-4">{i.scheduled_pay_month}</td>
                                    <td className="py-1 pr-4">Rs. {i.scheduled_amount}</td>
                                    <td className="py-1 pr-4">{i.paid_pay_month || "-"}</td>
                                    <td className="py-1 pr-4">{i.paid_amount != null ? `Rs. ${i.paid_amount}` : "-"}</td>
                                    <td className="py-1 pr-4">
                                      <StatusChip status={i.status} />
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h2 className="text-sm font-semibold text-slate-700 mb-3">{t("Adjustments & recoveries")}</h2>
          {!adjustments ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : adjustments.length === 0 ? (
            <p className="text-sm text-slate-500 mb-5">{t("No adjustment or recovery entries on record.")}</p>
          ) : (
            <div className="overflow-x-auto mb-6">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                    <th className="py-2 pr-4">{t("Type")}</th>
                    <th className="py-2 pr-4">{t("Reason")}</th>
                    <th className="py-2 pr-4">{t("Total")}</th>
                    <th className="py-2 pr-4">{t("Recovered")}</th>
                    <th className="py-2 pr-4">{t("Balance")}</th>
                    <th className="py-2 pr-4">{t("Status")}</th>
                    <th className="py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {adjustments.map((a) => (
                    <tr key={a.id} className="border-b border-slate-100 align-top">
                      <td className="py-2 pr-4 font-medium text-slate-700">{a.adjustment_type}</td>
                      <td className="py-2 pr-4 text-slate-500 max-w-xs">{a.reason}</td>
                      <td className="py-2 pr-4">Rs. {a.total_amount}</td>
                      <td className="py-2 pr-4">Rs. {a.recovered_amount}</td>
                      <td className="py-2 pr-4">Rs. {a.balance_amount.toFixed(2)}</td>
                      <td className="py-2 pr-4">
                        <StatusChip status={a.status} />
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => raiseGrievance("Incorrect deduction", "adjustment_entry", a.id)}
                          className="text-xs text-orange-700 font-medium hover:text-orange-800"
                        >
                          {t("Raise grievance")}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <h2 className="text-sm font-semibold text-slate-700 mb-3">{t("Benefit entitlements")}</h2>
          {!benefits ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : benefits.length === 0 ? (
            <p className="text-sm text-slate-500">{t("No benefit entitlements on record.")}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                    <th className="py-2 pr-4">{t("Benefit")}</th>
                    <th className="py-2 pr-4">{t("Effective from")}</th>
                    <th className="py-2 pr-4">{t("Effective to")}</th>
                    <th className="py-2 pr-4">{t("Next review")}</th>
                    <th className="py-2">{t("Status")}</th>
                  </tr>
                </thead>
                <tbody>
                  {benefits.map((b) => (
                    <tr key={b.id} className="border-b border-slate-100">
                      <td className="py-2 pr-4 font-medium text-slate-700">{t(b.benefit_type)}</td>
                      <td className="py-2 pr-4 text-slate-500">{b.effective_from}</td>
                      <td className="py-2 pr-4 text-slate-500">{b.effective_to || "-"}</td>
                      <td className="py-2 pr-4 text-slate-500">{b.next_review_date || "-"}</td>
                      <td className="py-2">
                        <StatusChip status={b.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded p-6">
          <h2 className="font-semibold text-slate-800 mb-1">{t("Claim a benefit")}</h2>
          <p className="text-sm text-slate-500 mb-5">
            {t("Not seeing a benefit you're entitled to, such as fixed medical allowance? Raise a claim here.")}
          </p>

          <form onSubmit={handleClaimSubmit} className="grid sm:grid-cols-2 gap-4 max-w-2xl mb-6">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="benefit_type">
                {t("Benefit type")}
              </label>
              <select
                id="benefit_type"
                className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={form.benefit_type}
                onChange={(e) => setForm({ ...form, benefit_type: e.target.value })}
                required
              >
                <option value="" disabled>
                  {t("Select a benefit")}
                </option>
                {CLAIM_TYPES.map((claimType) => (
                  <option key={claimType} value={claimType}>
                    {t(claimType)}
                  </option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="details">
                {t("Details")}
              </label>
              <textarea
                id="details"
                rows={2}
                className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={form.details}
                onChange={(e) => setForm({ ...form, details: e.target.value })}
                required
                minLength={10}
              />
            </div>
            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={submitting}
                className="bg-blue-800 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-900 disabled:opacity-60"
              >
                {submitting ? t("Submitting...") : t("Submit claim")}
              </button>
            </div>
          </form>

          <h2 className="font-semibold text-slate-800 mb-3">{t("My claims")}</h2>
          {!claims ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : claims.length === 0 ? (
            <p className="text-sm text-slate-500">{t("No benefit claims raised yet.")}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                    <th className="py-2 pr-4">{t("Benefit")}</th>
                    <th className="py-2 pr-4">{t("Status")}</th>
                    <th className="py-2 pr-4">{t("Raised on")}</th>
                    <th className="py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {claims.map((c) => (
                    <tr key={c.id} className="border-b border-slate-100 align-top">
                      <td className="py-2 pr-4">{t(c.benefit_type)}</td>
                      <td className="py-2 pr-4">
                        <StatusChip status={c.status} />
                        {c.is_breached && <p className="text-xs text-red-600 font-medium mt-1">{t("Breached")}</p>}
                        {c.escalated && <p className="text-xs text-orange-600 mt-1">{t("Escalated")}</p>}
                        {c.review_remarks && <p className="text-xs text-slate-500 mt-1 max-w-xs">{c.review_remarks}</p>}
                      </td>
                      <td className="py-2 pr-4 text-slate-500">{c.server_date.slice(0, 10)}</td>
                      <td className="py-2">
                        {c.is_breached && !c.escalated && (
                          <button
                            onClick={() => handleEscalate(c.id)}
                            className="text-sm text-orange-700 font-medium hover:text-orange-800"
                          >
                            {t("Escalate")}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
