import { useEffect, useState } from "react";
import { useCurrentPensioner } from "../api/useCurrentPensioner";
import { get, post } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";
import { StatusChip } from "./StatusChip";

const emptyAnnouncement = {
  title: "",
  body: "",
  category: "",
  target_audience: "All pensioners",
  valid_from: "",
  valid_to: "",
  has_attachment: false,
};
const emptyFaq = { question: "", answer: "", category: "", display_order: 1 };

export default function Announcements() {
  const { t } = useLanguage();
  const pensioner = useCurrentPensioner();
  const isOfficer = pensioner && pensioner.role === "pension_officer";

  const [announcements, setAnnouncements] = useState(null);
  const [faqs, setFaqs] = useState(null);
  const [categories, setCategories] = useState([]);
  const [adminAnnouncements, setAdminAnnouncements] = useState(null);
  const [adminFaqs, setAdminFaqs] = useState(null);
  const [announcementForm, setAnnouncementForm] = useState(emptyAnnouncement);
  const [faqForm, setFaqForm] = useState(emptyFaq);

  function load() {
    get("/announcements").then(setAnnouncements);
    get("/announcements/faqs").then(setFaqs);
    get("/announcements/categories").then(setCategories);
    if (isOfficer) {
      get("/announcements/admin").then(setAdminAnnouncements);
      get("/announcements/faqs/admin").then(setAdminFaqs);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOfficer]);

  async function handleCreateAnnouncement(e) {
    e.preventDefault();
    await post("/announcements/admin", announcementForm);
    setAnnouncementForm(emptyAnnouncement);
    load();
  }

  async function handlePublish(id) {
    await post(`/announcements/admin/${id}/publish`);
    load();
  }

  async function handleWithdraw(id) {
    await post(`/announcements/admin/${id}/withdraw`);
    load();
  }

  async function handleCreateFaq(e) {
    e.preventDefault();
    await post("/announcements/faqs/admin", faqForm);
    setFaqForm(emptyFaq);
    load();
  }

  async function handleToggleFaq(id) {
    await post(`/announcements/faqs/admin/${id}/toggle`);
    load();
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="bg-white border border-slate-200 rounded p-6">
          <h1 className="font-semibold text-slate-800 mb-1">{t("Announcements")}</h1>
          <p className="text-sm text-slate-500 mb-5">{t("Notices from the pension department, current as of today.")}</p>

          {!announcements ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : announcements.length === 0 ? (
            <p className="text-sm text-slate-500">{t("No announcements are currently active.")}</p>
          ) : (
            <div className="space-y-4">
              {announcements.map((a) => (
                <div key={a.id} className="border border-slate-200 rounded p-4">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <h3 className="font-medium text-slate-800">{a.title}</h3>
                    <span className="text-xs shrink-0 border border-slate-200 rounded px-2 py-0.5 text-slate-500">
                      {t(a.category)}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mb-2">{a.body}</p>
                  <p className="text-xs text-slate-400">
                    {t("Valid")} {a.valid_from} {t("to")} {a.valid_to}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded p-6">
          <h2 className="font-semibold text-slate-800 mb-1">{t("FAQ")}</h2>
          <p className="text-sm text-slate-500 mb-5">{t("Frequently asked questions.")}</p>

          {!faqs ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : faqs.length === 0 ? (
            <p className="text-sm text-slate-500">{t("No FAQs published yet.")}</p>
          ) : (
            <div className="space-y-3">
              {faqs.map((f) => (
                <details key={f.id} className="border border-slate-200 rounded p-3">
                  <summary className="text-sm font-medium text-slate-700 cursor-pointer">{f.question}</summary>
                  <p className="text-sm text-slate-600 mt-2">{f.answer}</p>
                </details>
              ))}
            </div>
          )}
        </div>

        {isOfficer && (
          <div className="bg-white border border-orange-200 rounded p-6">
            <h2 className="font-semibold text-slate-800 mb-1">{t("Content administration")}</h2>
            <p className="text-sm text-slate-500 mb-5">{t("Maintain announcements and FAQs. Officer access only.")}</p>

            <h3 className="text-sm font-semibold text-slate-700 mb-3">{t("New announcement")}</h3>
            <form onSubmit={handleCreateAnnouncement} className="grid sm:grid-cols-2 gap-4 max-w-2xl mb-6">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Title")}</label>
                <input
                  className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  value={announcementForm.title}
                  onChange={(e) => setAnnouncementForm({ ...announcementForm, title: e.target.value })}
                  required
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Body")}</label>
                <textarea
                  rows={2}
                  className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  value={announcementForm.body}
                  onChange={(e) => setAnnouncementForm({ ...announcementForm, body: e.target.value })}
                  required
                  minLength={10}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Category")}</label>
                <select
                  className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  value={announcementForm.category}
                  onChange={(e) => setAnnouncementForm({ ...announcementForm, category: e.target.value })}
                  required
                >
                  <option value="" disabled>
                    {t("Select")}
                  </option>
                  {categories.map((c) => (
                    <option key={c} value={c}>
                      {t(c)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Target audience")}</label>
                <input
                  className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  value={announcementForm.target_audience}
                  onChange={(e) => setAnnouncementForm({ ...announcementForm, target_audience: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Valid from")}</label>
                <input
                  type="date"
                  className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  value={announcementForm.valid_from}
                  onChange={(e) => setAnnouncementForm({ ...announcementForm, valid_from: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Valid to")}</label>
                <input
                  type="date"
                  className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  value={announcementForm.valid_to}
                  onChange={(e) => setAnnouncementForm({ ...announcementForm, valid_to: e.target.value })}
                  required
                />
              </div>
              <div className="sm:col-span-2">
                <button
                  type="submit"
                  className="bg-blue-800 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-900"
                >
                  {t("Save as draft")}
                </button>
              </div>
            </form>

            {adminAnnouncements && adminAnnouncements.length > 0 && (
              <div className="overflow-x-auto mb-6">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                      <th className="py-2 pr-4">{t("Title")}</th>
                      <th className="py-2 pr-4">{t("Category")}</th>
                      <th className="py-2 pr-4">{t("Validity")}</th>
                      <th className="py-2 pr-4">{t("Status")}</th>
                      <th className="py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminAnnouncements.map((a) => (
                      <tr key={a.id} className="border-b border-slate-100 align-top">
                        <td className="py-2 pr-4 font-medium text-slate-700">{a.title}</td>
                        <td className="py-2 pr-4 text-slate-500">{t(a.category)}</td>
                        <td className="py-2 pr-4 text-slate-500">
                          {a.valid_from} {t("to")} {a.valid_to}
                        </td>
                        <td className="py-2 pr-4">
                          <StatusChip status={a.status} />
                        </td>
                        <td className="py-2">
                          {a.status === "Draft" && (
                            <button
                              onClick={() => handlePublish(a.id)}
                              className="text-sm text-green-700 font-medium hover:text-green-800"
                            >
                              {t("Publish")}
                            </button>
                          )}
                          {a.status === "Published" && (
                            <button
                              onClick={() => handleWithdraw(a.id)}
                              className="text-sm text-red-700 font-medium hover:text-red-800"
                            >
                              {t("Withdraw")}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <h3 className="text-sm font-semibold text-slate-700 mb-3">{t("New FAQ")}</h3>
            <form onSubmit={handleCreateFaq} className="grid sm:grid-cols-2 gap-4 max-w-2xl mb-6">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Question")}</label>
                <input
                  className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  value={faqForm.question}
                  onChange={(e) => setFaqForm({ ...faqForm, question: e.target.value })}
                  required
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Answer")}</label>
                <textarea
                  rows={2}
                  className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  value={faqForm.answer}
                  onChange={(e) => setFaqForm({ ...faqForm, answer: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">{t("Category")}</label>
                <input
                  className="w-full border border-slate-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  value={faqForm.category}
                  onChange={(e) => setFaqForm({ ...faqForm, category: e.target.value })}
                  required
                />
              </div>
              <div className="sm:col-span-2">
                <button
                  type="submit"
                  className="bg-blue-800 text-white px-4 py-2 rounded text-sm font-medium hover:bg-blue-900"
                >
                  {t("Add FAQ")}
                </button>
              </div>
            </form>

            {adminFaqs && adminFaqs.length > 0 && (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                      <th className="py-2 pr-4">{t("Question")}</th>
                      <th className="py-2 pr-4">{t("Category")}</th>
                      <th className="py-2 pr-4">{t("Status")}</th>
                      <th className="py-2"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {adminFaqs.map((f) => (
                      <tr key={f.id} className="border-b border-slate-100 align-top">
                        <td className="py-2 pr-4 text-slate-700">{f.question}</td>
                        <td className="py-2 pr-4 text-slate-500">{f.category}</td>
                        <td className="py-2 pr-4">
                          <StatusChip status={f.status} />
                        </td>
                        <td className="py-2">
                          <button
                            onClick={() => handleToggleFaq(f.id)}
                            className="text-sm text-blue-800 font-medium hover:text-blue-900"
                          >
                            {f.status === "Active" ? t("Deactivate") : t("Activate")}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
