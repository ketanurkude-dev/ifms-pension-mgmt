import { useEffect, useState } from "react";
import { get, post } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";
import { StatusChip } from "./StatusChip";

export default function Approver() {
  const { t } = useLanguage();
  const [queue, setQueue] = useState(null);
  const [remarksById, setRemarksById] = useState({});
  const [grievanceQueue, setGrievanceQueue] = useState(null);
  const [grievanceRemarksById, setGrievanceRemarksById] = useState({});
  const [certificateQueue, setCertificateQueue] = useState(null);
  const [certificateRemarksById, setCertificateRemarksById] = useState({});

  function load() {
    get("/approver/queue").then(setQueue);
    get("/grievances/queue").then(setGrievanceQueue);
    get("/life-certificate/queue").then(setCertificateQueue);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleReview(item, decision) {
    const review_remarks = remarksById[item.id] || "";
    if (decision === "Returned" && !review_remarks) {
      alert(t("Remarks are required to return an item."));
      return;
    }
    const path =
      item.item_type === "benefit_claim"
        ? `/approver/benefit-claims/${item.id}/review`
        : `/approver/bank-requests/${item.id}/review`;
    await post(path, { status: decision, review_remarks });
    load();
  }

  async function handleGrievanceAction(id, action) {
    const remarks = grievanceRemarksById[id] || "";
    if (!remarks) {
      alert(t("Remarks are required for this action."));
      return;
    }
    await post(`/grievances/${id}/${action}`, { remarks });
    setGrievanceRemarksById({ ...grievanceRemarksById, [id]: "" });
    load();
  }

  async function handleVerifyCertificate(id) {
    await post(`/life-certificate/${id}/verify`);
    load();
  }

  async function handleRejectCertificate(id) {
    const remarks = certificateRemarksById[id] || "";
    if (!remarks) {
      alert(t("Remarks are required to reject a certificate."));
      return;
    }
    await post(`/life-certificate/${id}/reject`, { remarks });
    setCertificateRemarksById({ ...certificateRemarksById, [id]: "" });
    load();
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="bg-white border border-slate-200 rounded p-6">
          <h1 className="font-semibold text-slate-800 mb-1">{t("Approver workbench")}</h1>
          <p className="text-sm text-slate-500 mb-5">
            {t("Bank account change and benefit claim requests awaiting your decision.")}
          </p>

          {!queue ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : queue.length === 0 ? (
            <p className="text-sm text-slate-500">{t("Nothing pending. Queue is clear.")}</p>
          ) : (
            <div className="space-y-4">
              {queue.map((item) => (
                <div key={item.id} className="border border-slate-200 rounded p-4">
                  <div className="mb-3">
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{item.pensioner_name}</p>
                    <h3 className="font-medium text-slate-800">{item.title}</h3>
                    <p className="text-xs text-slate-400 mt-1">{t("Raised")} {item.server_date.slice(0, 10)}</p>
                  </div>

                  <input
                    placeholder={t("Remarks (required to return)")}
                    className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    value={remarksById[item.id] || ""}
                    onChange={(e) => setRemarksById({ ...remarksById, [item.id]: e.target.value })}
                  />

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleReview(item, "Approved")}
                      className="text-sm font-medium bg-green-700 text-white px-3 py-1.5 rounded hover:bg-green-800"
                    >
                      {t("Approve")}
                    </button>
                    <button
                      onClick={() => handleReview(item, "Returned")}
                      className="text-sm font-medium border border-orange-300 text-orange-700 px-3 py-1.5 rounded hover:bg-orange-50"
                    >
                      {t("Return for clarification")}
                    </button>
                    <button
                      onClick={() => handleReview(item, "Rejected")}
                      className="text-sm font-medium border border-red-300 text-red-700 px-3 py-1.5 rounded hover:bg-red-50"
                    >
                      {t("Reject")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded p-6">
          <h2 className="font-semibold text-slate-800 mb-1">{t("Grievance queue")}</h2>
          <p className="text-sm text-slate-500 mb-5">{t("Open and awaiting-clarification grievances routed to you.")}</p>

          {!grievanceQueue ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : grievanceQueue.length === 0 ? (
            <p className="text-sm text-slate-500">{t("Nothing pending. Queue is clear.")}</p>
          ) : (
            <div className="space-y-4">
              {grievanceQueue.map((item) => (
                <div key={item.id} className="border border-slate-200 rounded p-4">
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">
                        {item.pensioner_name} &middot; {item.grievance_number}
                      </p>
                      <h3 className="font-medium text-slate-800">{t(item.category)}</h3>
                      <p className="text-xs text-slate-400 mt-1">{t("Due")} {item.due_date}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <StatusChip status={item.status} />
                      {item.is_breached && <p className="text-xs text-red-600 font-medium mt-1">{t("Breached")}</p>}
                    </div>
                  </div>

                  <input
                    placeholder={t("Remarks (required for any action)")}
                    className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    value={grievanceRemarksById[item.id] || ""}
                    onChange={(e) => setGrievanceRemarksById({ ...grievanceRemarksById, [item.id]: e.target.value })}
                  />

                  <div className="flex gap-2">
                    {item.status === "Open" && (
                      <button
                        onClick={() => handleGrievanceAction(item.id, "request-clarification")}
                        className="text-sm font-medium border border-orange-300 text-orange-700 px-3 py-1.5 rounded hover:bg-orange-50"
                      >
                        {t("Seek clarification")}
                      </button>
                    )}
                    <button
                      onClick={() => handleGrievanceAction(item.id, "interim-reply")}
                      className="text-sm font-medium border border-slate-300 text-slate-700 px-3 py-1.5 rounded hover:bg-slate-50"
                    >
                      {t("Interim reply")}
                    </button>
                    <button
                      onClick={() => handleGrievanceAction(item.id, "close")}
                      className="text-sm font-medium bg-green-700 text-white px-3 py-1.5 rounded hover:bg-green-800"
                    >
                      {t("Close with final reply")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded p-6">
          <h2 className="font-semibold text-slate-800 mb-1">{t("Life certificate queue")}</h2>
          <p className="text-sm text-slate-500 mb-5">{t("Physically submitted certificates awaiting your verification.")}</p>

          {!certificateQueue ? (
            <p className="text-sm text-slate-500">{t("Loading...")}</p>
          ) : certificateQueue.length === 0 ? (
            <p className="text-sm text-slate-500">{t("Nothing pending. Queue is clear.")}</p>
          ) : (
            <div className="space-y-4">
              {certificateQueue.map((item) => (
                <div key={item.id} className="border border-slate-200 rounded p-4">
                  <div className="mb-3">
                    <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{item.pensioner_name}</p>
                    <h3 className="font-medium text-slate-800">{t(item.mode)}</h3>
                    <p className="text-xs text-slate-500 mt-1">{t("Reference")}: {item.reference}</p>
                    <p className="text-xs text-slate-400 mt-1">{t("Submitted")} {item.submitted_on}</p>
                  </div>

                  <input
                    placeholder={t("Remarks (required to reject)")}
                    className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    value={certificateRemarksById[item.id] || ""}
                    onChange={(e) => setCertificateRemarksById({ ...certificateRemarksById, [item.id]: e.target.value })}
                  />

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleVerifyCertificate(item.id)}
                      className="text-sm font-medium bg-green-700 text-white px-3 py-1.5 rounded hover:bg-green-800"
                    >
                      {t("Verify")}
                    </button>
                    <button
                      onClick={() => handleRejectCertificate(item.id)}
                      className="text-sm font-medium border border-red-300 text-red-700 px-3 py-1.5 rounded hover:bg-red-50"
                    >
                      {t("Reject")}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
