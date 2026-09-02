import React, { useEffect, useState } from "react";
import { get, post } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";
import { StatusChip } from "./StatusChip";

function translateAction(t, action) {
  if (action.startsWith("Satisfaction recorded: ")) {
    const value = action.slice("Satisfaction recorded: ".length);
    return `${t("Satisfaction recorded")}: ${t(value)}`;
  }
  return t(action);
}

export default function MyRequests() {
  const { t } = useLanguage();
  const [requests, setRequests] = useState(null);
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [expandedKey, setExpandedKey] = useState(null);

  function load() {
    const params = {};
    if (typeFilter) params.request_type = typeFilter;
    if (statusFilter) params.status = statusFilter;
    get("/requests", { params }).then(setRequests);
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeFilter, statusFilter]);

  async function handleEscalate(item) {
    const paths = {
      Grievance: `/grievances/${item.request_id}/escalate`,
      "Benefit claim": `/arrears-benefits/claims/${item.request_id}/escalate`,
      "Bank account change": `/bank-requests/${item.request_id}/escalate`,
    };
    await post(paths[item.request_type]);
    load();
  }

  function toggleExpand(key) {
    setExpandedKey(expandedKey === key ? null : key);
  }

  return (
    <AppLayout>
      <div className="bg-white border border-slate-200 rounded p-6">
        <h1 className="font-semibold text-slate-800 mb-1">{t("My requests")}</h1>
        <p className="text-sm text-slate-500 mb-5">
          {t("Every request you have raised, tracked in one place until disposal.")}
        </p>

        <div className="flex gap-3 mb-5">
          <select
            className="border border-slate-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="">{t("All types")}</option>
            <option value="Bank account change">{t("Bank account change")}</option>
            <option value="Benefit claim">{t("Benefit claim")}</option>
            <option value="Grievance">{t("Grievance")}</option>
          </select>
          <select
            className="border border-slate-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-600"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">{t("All statuses")}</option>
            <option value="Submitted">{t("Submitted")}</option>
            <option value="Approved">{t("Approved")}</option>
            <option value="Rejected">{t("Rejected")}</option>
            <option value="Returned">{t("Returned")}</option>
            <option value="Withdrawn">{t("Withdrawn")}</option>
            <option value="Open">{t("Open")}</option>
            <option value="Awaiting Clarification">{t("Awaiting Clarification")}</option>
            <option value="Closed">{t("Closed")}</option>
          </select>
        </div>

        {!requests ? (
          <p className="text-sm text-slate-500">{t("Loading...")}</p>
        ) : requests.length === 0 ? (
          <p className="text-sm text-slate-500">{t("No requests match this filter.")}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-400 border-b border-slate-200">
                  <th className="py-2 pr-4">{t("Request")}</th>
                  <th className="py-2 pr-4">{t("Type")}</th>
                  <th className="py-2 pr-4">{t("Status")}</th>
                  <th className="py-2 pr-4">{t("Submitted")}</th>
                  <th className="py-2 pr-4">{t("Due")}</th>
                  <th className="py-2 pr-4">{t("Disposed")}</th>
                  <th className="py-2"></th>
                </tr>
              </thead>
              <tbody>
                {requests.map((item) => {
                  const key = `${item.request_type}-${item.request_id}`;
                  return (
                    <React.Fragment key={key}>
                      <tr className="border-b border-slate-100 align-top">
                        <td className="py-2 pr-4">
                          <button
                            onClick={() => toggleExpand(key)}
                            className="font-medium text-blue-800 hover:text-blue-900 text-left"
                          >
                            {item.request_number}
                          </button>
                          <p className="text-xs text-slate-500">{item.title}</p>
                        </td>
                        <td className="py-2 pr-4 text-slate-600">{t(item.request_type)}</td>
                        <td className="py-2 pr-4">
                          <StatusChip status={item.status} />
                          {item.is_breached && (
                            <p className="text-xs text-red-600 font-medium mt-1">{t("Breached")}</p>
                          )}
                          {item.escalated && <p className="text-xs text-orange-600 mt-1">{t("Escalated")}</p>}
                        </td>
                        <td className="py-2 pr-4 text-slate-500">{item.submitted_on.slice(0, 10)}</td>
                        <td className="py-2 pr-4 text-slate-500">{item.due_date}</td>
                        <td className="py-2 pr-4 text-slate-500">
                          {item.disposed_on ? item.disposed_on.slice(0, 10) : "-"}
                        </td>
                        <td className="py-2">
                          {item.is_breached && !item.escalated && (
                            <button
                              onClick={() => handleEscalate(item)}
                              className="text-sm text-orange-700 font-medium hover:text-orange-800"
                            >
                              {t("Escalate")}
                            </button>
                          )}
                        </td>
                      </tr>
                      {expandedKey === key && (
                        <tr className="border-b border-slate-100 bg-slate-50">
                          <td colSpan={7} className="py-3 px-4">
                            <p className="text-xs uppercase tracking-wide text-slate-400 mb-2">
                              {t("Action history")}
                            </p>
                            <ul className="space-y-1.5">
                              {item.events.map((ev, i) => (
                                <li key={i} className="text-sm text-slate-600">
                                  <span className="font-medium text-slate-700">{translateAction(t, ev.action)}</span>{" "}
                                  <span className="text-xs text-slate-400">
                                    {ev.server_date.slice(0, 16).replace("T", " ")}
                                  </span>
                                  {ev.remarks && <span className="block text-xs text-slate-500">{ev.remarks}</span>}
                                </li>
                              ))}
                            </ul>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
