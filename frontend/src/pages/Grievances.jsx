import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { downloadFile, get, post } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";
import { StatusChip } from "./StatusChip";

const emptyForm = { category: "", description: "", linked_reference_type: null, linked_reference_id: null };

function translateAction(t, action) {
  if (action.startsWith("Satisfaction recorded: ")) {
    const value = action.slice("Satisfaction recorded: ".length);
    return `${t("Satisfaction recorded")}: ${t(value)}`;
  }
  return t(action);
}

export default function Grievances() {
  const { t } = useLanguage();
  const [searchParams] = useSearchParams();
  const [grievances, setGrievances] = useState(null);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(() => {
    const category = searchParams.get("category");
    const linkedType = searchParams.get("linked_type");
    const linkedId = searchParams.get("linked_id");
    return {
      ...emptyForm,
      category: category || "",
      linked_reference_type: linkedType || null,
      linked_reference_id: linkedId ? Number(linkedId) : null,
    };
  });
  const [submitting, setSubmitting] = useState(false);
  const [replyDraft, setReplyDraft] = useState({});
  const [reopenDraft, setReopenDraft] = useState({});

  function load() {
    get("/grievances").then(setGrievances);
  }

  useEffect(() => {
    load();
    get("/grievances/categories").then(setCategories);
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await post("/grievances", form);
      setForm(emptyForm);
      load();
    } finally {
      setSubmitting(false);
    }
  }

  async function handleReply(id) {
    const remarks = replyDraft[id] || "";
    if (!remarks) {
      alert(t("Enter a reply before sending."));
      return;
    }
    await post(`/grievances/${id}/reply`, { remarks });
    setReplyDraft({ ...replyDraft, [id]: "" });
    load();
  }

  async function handleSatisfaction(id, satisfaction) {
    await post(`/grievances/${id}/satisfaction`, { satisfaction });
    load();
  }

  async function handleReopen(id) {
    const reason = reopenDraft[id] || "";
    if (!reason) {
      alert(t("Enter a reason to reopen this grievance."));
      return;
    }
    await post(`/grievances/${id}/reopen`, { reason });
    setReopenDraft({ ...reopenDraft, [id]: "" });
    load();
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="bg-white border border-slate-200 rounded p-6">
          <h1 className="font-semibold text-slate-800 mb-1">{t("Lodge a grievance")}</h1>
          <p className="text-sm text-slate-500 mb-5">
            {t("Your grievance is routed to the concerned officer and tracked until resolution.")}
          </p>

          <form onSubmit={handleSubmit} className="grid sm:grid-cols-2 gap-4 max-w-2xl">
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="category">
                {t("Category")}
              </label>
              <select
                id="category"
                className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
                required
              >
                <option value="" disabled>
                  {t("Select a category")}
                </option>
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {t(c)}
                  </option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="description">
                {t("Description")}
              </label>
              <textarea
                id="description"
                rows={3}
                className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                required
                minLength={10}
              />
            </div>
            {form.linked_reference_type && (
              <div className="sm:col-span-2">
                <p className="text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded px-3 py-2">
                  {t("This grievance will carry a reference to the record you raised it from.")}
                </p>
              </div>
            )}
            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={submitting}
                className="bg-blue-800 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-900 disabled:opacity-60"
              >
                {submitting ? t("Submitting...") : t("Lodge grievance")}
              </button>
            </div>
          </form>
        </div>

        <div className="bg-white border border-slate-200 rounded p-6">
          <h2 className="font-semibold text-slate-800 mb-4">{t("My grievances")}</h2>

          {!grievances ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : grievances.length === 0 ? (
            <p className="text-sm text-slate-500">{t("No grievances lodged yet.")}</p>
          ) : (
            <div className="space-y-4">
              {grievances.map((g) => (
                <div key={g.id} className="border border-slate-200 rounded p-4">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{g.grievance_number}</p>
                      <h3 className="font-medium text-slate-800">{t(g.category)}</h3>
                    </div>
                    <div className="text-right shrink-0">
                      <StatusChip status={g.status} />
                      {g.is_breached && (
                        <p className="text-xs text-red-600 font-medium mt-1">{t("Service level breached")}</p>
                      )}
                    </div>
                  </div>

                  <p className="text-sm text-slate-600 mb-2">{g.description}</p>
                  <p className="text-xs text-slate-400 mb-3">
                    {t("Lodged")} {g.server_date.slice(0, 10)} &middot; {t("Due")} {g.due_date}
                  </p>

                  <button
                    onClick={() => downloadFile(`/grievances/${g.id}/acknowledgement/pdf`, `${g.grievance_number.replace(/\//g, "-")}.pdf`)}
                    className="text-sm text-blue-800 font-medium hover:text-blue-900 mb-3"
                  >
                    {t("Download acknowledgement")}
                  </button>

                  {g.events.length > 0 && (
                    <div className="border-t border-slate-100 pt-3 mt-1 mb-3">
                      <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">{t("Activity")}</p>
                      <ul className="space-y-1.5">
                        {g.events.map((ev, i) => (
                          <li key={i} className="text-sm text-slate-600">
                            <span className="font-medium text-slate-700">{translateAction(t, ev.action)}</span>{" "}
                            <span className="text-xs text-slate-400">{ev.server_date.slice(0, 16).replace("T", " ")}</span>
                            {ev.remarks && <span className="block text-xs text-slate-500">{ev.remarks}</span>}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {g.reply && (
                    <div className="bg-slate-50 border border-slate-200 rounded p-3 mb-3">
                      <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{t("Officer's reply")}</p>
                      <p className="text-sm text-slate-700">{g.reply}</p>
                    </div>
                  )}

                  {g.status === "Awaiting Clarification" && (
                    <div className="flex gap-2">
                      <input
                        placeholder={t("Your reply")}
                        className="flex-1 border border-slate-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                        value={replyDraft[g.id] || ""}
                        onChange={(e) => setReplyDraft({ ...replyDraft, [g.id]: e.target.value })}
                      />
                      <button
                        onClick={() => handleReply(g.id)}
                        className="text-sm font-medium bg-blue-800 text-white px-3 py-1.5 rounded hover:bg-blue-900"
                      >
                        {t("Send reply")}
                      </button>
                    </div>
                  )}

                  {g.status === "Closed" && !g.satisfaction && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleSatisfaction(g.id, "Satisfied")}
                        className="text-sm font-medium bg-green-700 text-white px-3 py-1.5 rounded hover:bg-green-800"
                      >
                        {t("Satisfied")}
                      </button>
                      <button
                        onClick={() => handleSatisfaction(g.id, "Dissatisfied")}
                        className="text-sm font-medium border border-red-300 text-red-700 px-3 py-1.5 rounded hover:bg-red-50"
                      >
                        {t("Dissatisfied")}
                      </button>
                    </div>
                  )}

                  {g.status === "Closed" && g.satisfaction === "Dissatisfied" && g.reopened_count === 0 && (
                    <div className="flex gap-2 mt-2">
                      <input
                        placeholder={t("Reason to reopen")}
                        className="flex-1 border border-slate-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
                        value={reopenDraft[g.id] || ""}
                        onChange={(e) => setReopenDraft({ ...reopenDraft, [g.id]: e.target.value })}
                      />
                      <button
                        onClick={() => handleReopen(g.id)}
                        className="text-sm font-medium border border-orange-300 text-orange-700 px-3 py-1.5 rounded hover:bg-orange-50"
                      >
                        {t("Reopen")}
                      </button>
                    </div>
                  )}

                  {g.satisfaction && (
                    <p className="text-xs text-slate-400 mt-2">
                      {t("You rated this resolution:")} <span className="font-medium text-slate-600">{t(g.satisfaction)}</span>
                      {g.reopened_count > 0 && ` ${t("(reopened once)")}`}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
