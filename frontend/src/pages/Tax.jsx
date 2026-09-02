import { useEffect, useState } from "react";
import { del, downloadFile, get, post } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";

const sections = ["80C", "80CCD(1B)", "80D", "80DD", "80DDB", "80G", "80TTB", "24(b)"];

function currentFinancialYear() {
  const today = new Date();
  const startYear = today.getMonth() >= 3 ? today.getFullYear() : today.getFullYear() - 1;
  return `${startYear}-${String(startYear + 1).slice(2)}`;
}

const emptyLine = { section: sections[0], instrument: "", declared_amount: "" };

export default function Tax() {
  const { t } = useLanguage();
  const [financialYear, setFinancialYear] = useState(currentFinancialYear());
  const [declaration, setDeclaration] = useState(null);
  const [versions, setVersions] = useState(null);
  const [documents, setDocuments] = useState(null);
  const [line, setLine] = useState(emptyLine);
  const [regime, setRegime] = useState("");
  const [otherIncome, setOtherIncome] = useState("");
  const [reviseReason, setReviseReason] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function load() {
    get(`/tax/declaration?financial_year=${financialYear}`).then((data) => {
      setDeclaration(data);
      setRegime(data.regime || "");
      setOtherIncome(data.other_income || "");
    });
    get(`/tax/declaration/versions?financial_year=${financialYear}`).then(setVersions);
    get(`/tax/documents?financial_year=${financialYear}`).then(setDocuments);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [financialYear]);

  const isLocked = declaration?.status === "Submitted";

  async function handleSaveRegime(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await post("/tax/declaration/regime", {
        financial_year: financialYear,
        regime,
        other_income: otherIncome ? Number(otherIncome) : 0,
      });
      load();
    } catch (err) {
      setError(err.response?.data?.detail || t("Could not save regime"));
    } finally {
      setBusy(false);
    }
  }

  async function handleAddLine(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await post("/tax/declaration/lines", {
        ...line,
        financial_year: financialYear,
        declared_amount: Number(line.declared_amount),
      });
      setLine(emptyLine);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || t("Could not add declaration"));
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteLine(lineId) {
    await del(`/tax/declaration/lines/${lineId}?financial_year=${financialYear}`);
    load();
  }

  async function handleSubmit() {
    setError("");
    setBusy(true);
    try {
      await post(`/tax/declaration/submit?financial_year=${financialYear}`);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || t("Could not submit declaration"));
    } finally {
      setBusy(false);
    }
  }

  async function handleRevise(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await post("/tax/declaration/revise", { financial_year: financialYear, reason: reviseReason });
      setReviseReason("");
      load();
    } catch (err) {
      setError(err.response?.data?.detail || t("Could not raise a revision"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="bg-white border border-slate-200 rounded p-6">
          <div className="flex items-start justify-between flex-wrap gap-3 mb-1">
            <h1 className="font-semibold text-slate-800">{t("Tax declaration")}</h1>
            <input
              type="text"
              value={financialYear}
              onChange={(e) => setFinancialYear(e.target.value)}
              className="border border-slate-300 rounded px-2 py-1 text-sm w-28 focus:outline-none focus:ring-2 focus:ring-blue-600"
            />
          </div>
          <p className="text-sm text-slate-500 mb-5">{t("Financial year")} {financialYear}</p>

          {error && (
            <div className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">{error}</div>
          )}

          {isLocked && (
            <div className="mb-5 flex items-center justify-between gap-3 bg-slate-50 border border-slate-200 rounded px-4 py-3">
              <div>
                <p className="text-sm font-medium text-slate-800">
                  {t("Version")} {declaration.version} {t("submitted — locked from further edits.")}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">
                  {t("Submitted")} {declaration.submitted_at?.slice(0, 10)} &middot; {t("Reference")} {declaration.tds_reference}
                </p>
              </div>
            </div>
          )}

          {!declaration ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : (
            <>
              <form onSubmit={handleSaveRegime} className="grid sm:grid-cols-3 gap-4 max-w-2xl mb-6">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Tax regime")}</label>
                  <select
                    className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    value={regime}
                    onChange={(e) => setRegime(e.target.value)}
                    disabled={isLocked}
                  >
                    <option value="">{t("Choose...")}</option>
                    <option value="Old">{t("Old regime")}</option>
                    <option value="New">{t("New regime")}</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Other income (annual)")}</label>
                  <input
                    type="number"
                    className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    value={otherIncome}
                    onChange={(e) => setOtherIncome(e.target.value)}
                    disabled={isLocked}
                  />
                </div>
                {!isLocked && (
                  <div className="flex items-end">
                    <button
                      type="submit"
                      disabled={busy}
                      className="bg-blue-800 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-900 disabled:opacity-60"
                    >
                      {t("Save")}
                    </button>
                  </div>
                )}
              </form>
              <p className="text-xs text-slate-400 mb-6 max-w-2xl">
                {t(
                  "Old regime keeps these deductions admissible; the new regime does not allow most of them — choose based on which gives you the lower tax outgo."
                )}
              </p>

              {!isLocked && (
                <form onSubmit={handleAddLine} className="grid sm:grid-cols-4 gap-4 max-w-3xl mb-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Section")}</label>
                    <select
                      className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                      value={line.section}
                      onChange={(e) => setLine({ ...line, section: e.target.value })}
                    >
                      {sections.map((s) => (
                        <option key={s} value={s}>
                          {s}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Instrument")}</label>
                    <input
                      className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                      value={line.instrument}
                      onChange={(e) => setLine({ ...line, instrument: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Amount")}</label>
                    <input
                      type="number"
                      className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                      value={line.declared_amount}
                      onChange={(e) => setLine({ ...line, declared_amount: e.target.value })}
                      required
                    />
                  </div>
                  <div className="flex items-end">
                    <button
                      type="submit"
                      disabled={busy}
                      className="bg-blue-800 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-900 disabled:opacity-60"
                    >
                      {t("Add")}
                    </button>
                  </div>
                </form>
              )}

              {declaration.lines.length === 0 ? (
                <p className="text-sm text-slate-500">{t("No declarations yet.")}</p>
              ) : (
                <div className="overflow-x-auto mb-4">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                        <th className="py-2 pr-4">{t("Section")}</th>
                        <th className="py-2 pr-4">{t("Instrument")}</th>
                        <th className="py-2 pr-4 text-right">{t("Declared amount")}</th>
                        <th className="py-2"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {declaration.lines.map((l) => (
                        <tr key={l.id} className="border-b border-slate-100 last:border-0">
                          <td className="py-2 pr-4">{l.section}</td>
                          <td className="py-2 pr-4">{l.instrument}</td>
                          <td className="py-2 pr-4 text-right tabular-nums">Rs. {l.declared_amount}</td>
                          <td className="py-2">
                            {!isLocked && (
                              <button
                                onClick={() => handleDeleteLine(l.id)}
                                className="text-xs text-red-700 font-medium hover:text-red-800"
                              >
                                {t("Remove")}
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                      <tr>
                        <td colSpan={2} className="py-2 pr-4 font-medium text-slate-800">
                          {t("Total declared")}
                        </td>
                        <td className="py-2 pr-4 text-right tabular-nums font-medium text-slate-800">
                          Rs. {declaration.total_declared}
                        </td>
                        <td></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              <div className="bg-blue-50 border border-blue-100 rounded p-4 mb-6 max-w-md">
                <p className="text-xs font-medium text-blue-800 uppercase tracking-wide mb-2">
                  {t("Projected (indicative only)")}
                </p>
                <div className="flex justify-between text-sm py-0.5">
                  <span className="text-slate-600">{t("Projected taxable income")}</span>
                  <span className="tabular-nums text-slate-800">Rs. {declaration.indicative_annual_income}</span>
                </div>
                <div className="flex justify-between text-sm py-0.5">
                  <span className="text-slate-600">{t("Projected tax")}</span>
                  <span className="tabular-nums text-slate-800">Rs. {declaration.indicative_tax}</span>
                </div>
                <p className="text-xs text-slate-400 mt-2">{t("Not computed by the TDS module — shown for guidance only.")}</p>
              </div>

              {!isLocked ? (
                <button
                  onClick={handleSubmit}
                  disabled={busy || !declaration.regime}
                  className="bg-blue-800 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-900 disabled:opacity-60"
                >
                  {t("Submit declaration")}
                </button>
              ) : (
                <form onSubmit={handleRevise} className="flex flex-wrap gap-3 items-end max-w-2xl">
                  <div className="flex-1 min-w-[220px]">
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Reason for revision")}</label>
                    <input
                      className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                      value={reviseReason}
                      onChange={(e) => setReviseReason(e.target.value)}
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={busy}
                    className="border border-blue-700 text-blue-800 px-4 py-2 rounded text-sm font-medium hover:bg-blue-50 disabled:opacity-60"
                  >
                    {t("Raise revision")}
                  </button>
                </form>
              )}
            </>
          )}

          {versions && versions.length > 1 && (
            <div className="mt-6 pt-5 border-t border-slate-200">
              <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">{t("Version history")}</p>
              <ul className="text-sm text-slate-600 space-y-1">
                {versions.map((v) => (
                  <li key={v.version}>
                    v{v.version} &middot; {t(v.status)}
                    {v.submitted_at && ` · ${t("submitted")} ${v.submitted_at.slice(0, 10)}`}
                    {v.revision_reason && ` · "${v.revision_reason}"`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded p-6">
          <h2 className="font-semibold text-slate-800 mb-4">{t("Tax documents")}</h2>
          {!documents ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : documents.length === 0 ? (
            <p className="text-sm text-slate-500">
              {t("Documents for FY")} {financialYear} {t("are not yet issued — Form 16 is typically issued by 15 June of the following year.")}
            </p>
          ) : (
            <ul className="text-sm divide-y divide-slate-100">
              {documents.map((d) => (
                <li key={d.id} className="py-2 flex items-center justify-between">
                  <span>
                    {d.doc_type}
                    {d.is_superseded && <span className="text-xs text-slate-400 ml-2">{t("(superseded)")}</span>}
                  </span>
                  <div className="flex items-center gap-4">
                    <span className="text-slate-500">{d.issued_on}</span>
                    <button
                      onClick={() => downloadFile(`/tax/documents/${d.id}/pdf`, `${d.doc_type}-${d.financial_year}.pdf`)}
                      className="text-blue-800 font-medium hover:text-blue-900"
                    >
                      {t("Download")}
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
