import { useEffect, useState } from "react";
import { get, post } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";
import { StatusChip } from "./StatusChip";

const emptyForm = { new_account_number: "", new_ifsc: "", new_bank_name: "", reason: "" };

export default function BankRequests() {
  const { t } = useLanguage();
  const [requests, setRequests] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);

  function load() {
    get("/bank-requests").then(setRequests);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await post("/bank-requests", form);
      setForm(emptyForm);
      load();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleWithdraw(id) {
    await post(`/bank-requests/${id}/withdraw`);
    load();
  }

  async function handleResubmit(r) {
    await post(`/bank-requests/${r.id}/resubmit`, {
      new_account_number: r.new_account_number,
      new_ifsc: r.new_ifsc,
      new_bank_name: r.new_bank_name,
      reason: r.reason,
    });
    load();
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="bg-white border border-slate-200 rounded p-6">
          <h1 className="font-semibold text-slate-800 mb-1">{t("Request a bank account change")}</h1>
          <p className="text-sm text-slate-500 mb-5">
            {t("Your pension officer will review this before it takes effect.")}
          </p>

          <form onSubmit={handleSubmit} className="grid sm:grid-cols-2 gap-4 max-w-2xl">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="new_account_number">
                {t("New account number")}
              </label>
              <input
                id="new_account_number"
                className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={form.new_account_number}
                onChange={(e) => setForm({ ...form, new_account_number: e.target.value })}
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="new_ifsc">
                {t("New IFSC")}
              </label>
              <input
                id="new_ifsc"
                className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={form.new_ifsc}
                onChange={(e) => setForm({ ...form, new_ifsc: e.target.value })}
                required
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="new_bank_name">
                {t("New bank name")}
              </label>
              <input
                id="new_bank_name"
                className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={form.new_bank_name}
                onChange={(e) => setForm({ ...form, new_bank_name: e.target.value })}
                required
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="reason">
                {t("Reason")}
              </label>
              <textarea
                id="reason"
                rows={2}
                className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={form.reason}
                onChange={(e) => setForm({ ...form, reason: e.target.value })}
                required
              />
            </div>
            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={submitting}
                className="bg-blue-800 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-900 disabled:opacity-60"
              >
                {submitting ? t("Submitting...") : t("Submit request")}
              </button>
            </div>
          </form>
        </div>

        <div className="bg-white border border-slate-200 rounded p-6">
          <h2 className="font-semibold text-slate-800 mb-4">{t("My requests")}</h2>

          {!requests ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : requests.length === 0 ? (
            <p className="text-sm text-slate-500">{t("No bank change requests yet.")}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                    <th className="py-2 pr-4">{t("New bank")}</th>
                    <th className="py-2 pr-4">{t("New account")}</th>
                    <th className="py-2 pr-4">{t("Status")}</th>
                    <th className="py-2 pr-4">{t("Raised on")}</th>
                    <th className="py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {requests.map((r) => (
                    <tr key={r.id} className="border-b border-slate-100 last:border-0 align-top">
                      <td className="py-2 pr-4">{r.new_bank_name}</td>
                      <td className="py-2 pr-4">{r.new_account_number}</td>
                      <td className="py-2 pr-4">
                        <StatusChip status={r.status} />
                        {r.review_remarks && (
                          <p className="text-xs text-slate-500 mt-1 max-w-xs">{r.review_remarks}</p>
                        )}
                      </td>
                      <td className="py-2 pr-4 text-slate-500">{r.server_date.slice(0, 10)}</td>
                      <td className="py-2">
                        {r.status === "Submitted" && (
                          <button
                            onClick={() => handleWithdraw(r.id)}
                            className="text-sm text-red-700 font-medium hover:text-red-800"
                          >
                            {t("Withdraw")}
                          </button>
                        )}
                        {r.status === "Rejected" && (
                          <button
                            onClick={() => handleResubmit(r)}
                            className="text-sm text-blue-800 font-medium hover:text-blue-900"
                          >
                            {t("Resubmit")}
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
