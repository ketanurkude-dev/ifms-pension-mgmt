import { useEffect, useState } from "react";
import { get, post } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";
import { StatusChip } from "./StatusChip";

const emptyForm = { mode: "", reference: "" };

export default function LifeCertificate() {
  const { t } = useLanguage();
  const [statusInfo, setStatusInfo] = useState(null);
  const [history, setHistory] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);

  function load() {
    get("/life-certificate/status").then(setStatusInfo);
    get("/life-certificate/history").then(setHistory);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await post("/life-certificate", form);
      setForm(emptyForm);
      load();
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="bg-white border border-slate-200 rounded p-6">
          <h1 className="font-semibold text-slate-800 mb-1">{t("Life certificate")}</h1>
          <p className="text-sm text-slate-500 mb-5">
            {t("Continued disbursement of your pension depends on submitting this annually.")}
          </p>

          {!statusInfo ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : (
            <>
              {statusInfo.is_overdue && (
                <div className="bg-red-50 border border-red-200 rounded p-3 mb-4">
                  <p className="text-sm text-red-700 font-medium">{t("Overdue")}</p>
                  <p className="text-sm text-red-700 mt-1">{statusInfo.stoppage_reason}</p>
                </div>
              )}
              {!statusInfo.is_overdue && statusInfo.is_due_soon && (
                <div className="bg-amber-50 border border-amber-200 rounded p-3 mb-4">
                  <p className="text-sm text-amber-700 font-medium">
                    {t("Due soon — submit before")} {statusInfo.due_date}
                  </p>
                </div>
              )}

              <div className="grid sm:grid-cols-3 gap-4 mb-2">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{t("Current validity")}</p>
                  <p className="text-sm text-slate-700">
                    {statusInfo.current_valid_from
                      ? `${statusInfo.current_valid_from} ${t("to")} ${statusInfo.current_valid_to}`
                      : t("No certificate on record yet")}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{t("Next due date")}</p>
                  <p className="text-sm text-slate-700">{statusInfo.due_date}</p>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded p-6">
          <h2 className="font-semibold text-slate-800 mb-1">{t("Submit life certificate")}</h2>
          <p className="text-sm text-slate-500 mb-5">
            {t(
              "Submit through Jeevan Pramaan for instant verification, or record a physically signed certificate for your disbursing office to verify."
            )}
          </p>

          <form onSubmit={handleSubmit} className="grid sm:grid-cols-2 gap-4 max-w-xl">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Mode")}</label>
              <select
                className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={form.mode}
                onChange={(e) => setForm({ ...form, mode: e.target.value })}
                required
              >
                <option value="" disabled>
                  {t("Select")}
                </option>
                <option value="Digital (Jeevan Pramaan)">{t("Digital (Jeevan Pramaan)")}</option>
                <option value="Physical (uploaded)">{t("Physical (uploaded)")}</option>
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                {form.mode === "Physical (uploaded)" ? t("Certificate number") : t("Jeevan Pramaan reference")}
              </label>
              <input
                className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={form.reference}
                onChange={(e) => setForm({ ...form, reference: e.target.value })}
                required
                minLength={4}
              />
            </div>
            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={submitting}
                className="bg-blue-800 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-900 disabled:opacity-60"
              >
                {submitting ? t("Submitting...") : t("Submit")}
              </button>
            </div>
          </form>
        </div>

        <div className="bg-white border border-slate-200 rounded p-6">
          <h2 className="font-semibold text-slate-800 mb-4">{t("Submission history")}</h2>

          {!history ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : history.length === 0 ? (
            <p className="text-sm text-slate-500">{t("No life certificate submitted yet.")}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                    <th className="py-2 pr-4">{t("Mode")}</th>
                    <th className="py-2 pr-4">{t("Reference")}</th>
                    <th className="py-2 pr-4">{t("Submitted")}</th>
                    <th className="py-2 pr-4">{t("Validity")}</th>
                    <th className="py-2">{t("Status")}</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.id} className="border-b border-slate-100 align-top">
                      <td className="py-2 pr-4">{t(h.mode)}</td>
                      <td className="py-2 pr-4 text-slate-600">{h.reference}</td>
                      <td className="py-2 pr-4 text-slate-500">{h.submitted_on}</td>
                      <td className="py-2 pr-4 text-slate-500">
                        {h.valid_from ? `${h.valid_from} ${t("to")} ${h.valid_to}` : "-"}
                      </td>
                      <td className="py-2">
                        <StatusChip status={h.status} />
                        {h.review_remarks && <p className="text-xs text-slate-500 mt-1 max-w-xs">{h.review_remarks}</p>}
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
