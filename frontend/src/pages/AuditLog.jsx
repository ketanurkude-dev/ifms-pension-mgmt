import { useState } from "react";
import { downloadFile, get } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";

export default function AuditLog() {
  const { t } = useLanguage();
  const [logs, setLogs] = useState([]);
  const [filters, setFilters] = useState({ entity_type: "", action: "", pensioner_id: "", result: "" });

  function buildParams() {
    const params = new URLSearchParams();
    if (filters.entity_type) params.set("entity_type", filters.entity_type);
    if (filters.action) params.set("action", filters.action);
    if (filters.pensioner_id) params.set("pensioner_id", filters.pensioner_id);
    if (filters.result) params.set("result", filters.result);
    return params;
  }

  function handleSearch() {
    get(`/audit/logs?${buildParams().toString()}`).then(setLogs);
  }

  const inputClass = "border border-slate-300 rounded-md px-3 py-1.5 text-sm";

  return (
    <AppLayout>
      <div className="bg-white border border-slate-200 rounded p-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="font-semibold text-slate-800">{t("Audit log")}</h1>
          <button onClick={() => downloadFile(`/audit/logs/export?${buildParams().toString()}`, "audit_log.csv")} className="text-xs text-blue-800 font-medium">
            Export CSV
          </button>
        </div>

        <div className="flex flex-wrap gap-2 mb-4">
          <input className={inputClass} placeholder="Entity type" value={filters.entity_type} onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })} />
          <input className={inputClass} placeholder="Action contains..." value={filters.action} onChange={(e) => setFilters({ ...filters, action: e.target.value })} />
          <input className={inputClass} placeholder="Pensioner ID" value={filters.pensioner_id} onChange={(e) => setFilters({ ...filters, pensioner_id: e.target.value })} />
          <select className={inputClass} value={filters.result} onChange={(e) => setFilters({ ...filters, result: e.target.value })}>
            <option value="">Any result</option>
            <option value="Success">Success</option>
            <option value="Failure">Failure</option>
          </select>
          <button onClick={handleSearch} className="bg-blue-800 text-white rounded-md px-4 py-1.5 text-sm font-medium hover:bg-blue-900">
            Search
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left uppercase tracking-wide text-slate-400 border-b border-slate-200">
                <th className="py-2 pr-3">Time</th>
                <th className="py-2 pr-3">Actor</th>
                <th className="py-2 pr-3">Role</th>
                <th className="py-2 pr-3">Action</th>
                <th className="py-2 pr-3">Entity</th>
                <th className="py-2 pr-3">Result</th>
                <th className="py-2 pr-3">Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className="border-b border-slate-100">
                  <td className="py-2 pr-3 text-slate-500">{log.server_date}</td>
                  <td className="py-2 pr-3">{log.actor_id || "-"}</td>
                  <td className="py-2 pr-3">{log.actor_role || "-"}</td>
                  <td className="py-2 pr-3">{log.action}</td>
                  <td className="py-2 pr-3">{log.entity_type}{log.entity_id ? ` #${log.entity_id}` : ""}</td>
                  <td className="py-2 pr-3">
                    <span className={log.result === "Success" ? "text-green-700" : "text-red-700"}>{log.result}</span>
                  </td>
                  <td className="py-2 pr-3 text-slate-500">{log.details || log.after_value || "-"}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={7} className="py-4 text-center text-slate-400">Run a search to see results</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AppLayout>
  );
}
