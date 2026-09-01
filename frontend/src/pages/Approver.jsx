import { useEffect, useState } from "react";
import { get, post } from "../api/apiService";
import AppLayout from "./AppLayout";

export default function Approver() {
  const [queue, setQueue] = useState(null);
  const [remarksById, setRemarksById] = useState({});

  function load() {
    get("/approver/queue").then(setQueue);
  }

  useEffect(() => {
    load();
  }, []);

  async function handleReview(id, decision) {
    const review_remarks = remarksById[id] || "";
    if (decision === "Returned" && !review_remarks) {
      alert("Remarks are required to return an item.");
      return;
    }
    await post(`/approver/bank-requests/${id}/review`, { status: decision, review_remarks });
    load();
  }

  return (
    <AppLayout>
      <div className="bg-white border border-slate-200 rounded p-6">
        <h1 className="font-semibold text-slate-800 mb-1">Approver workbench</h1>
        <p className="text-sm text-slate-500 mb-5">Bank account change requests awaiting your decision.</p>

        {!queue ? (
          <p className="text-sm text-slate-500">Loading...</p>
        ) : queue.length === 0 ? (
          <p className="text-sm text-slate-500">Nothing pending. Queue is clear.</p>
        ) : (
          <div className="space-y-4">
            {queue.map((item) => (
              <div key={item.id} className="border border-slate-200 rounded p-4">
                <div className="mb-3">
                  <p className="text-xs uppercase tracking-wide text-slate-400 mb-1">{item.pensioner_name}</p>
                  <h3 className="font-medium text-slate-800">{item.title}</h3>
                  <p className="text-xs text-slate-400 mt-1">Raised {item.server_date.slice(0, 10)}</p>
                </div>

                <input
                  placeholder="Remarks (required to return)"
                  className="w-full border border-slate-300 rounded px-3 py-1.5 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-blue-600"
                  value={remarksById[item.id] || ""}
                  onChange={(e) => setRemarksById({ ...remarksById, [item.id]: e.target.value })}
                />

                <div className="flex gap-2">
                  <button
                    onClick={() => handleReview(item.id, "Approved")}
                    className="text-sm font-medium bg-green-700 text-white px-3 py-1.5 rounded hover:bg-green-800"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleReview(item.id, "Returned")}
                    className="text-sm font-medium border border-orange-300 text-orange-700 px-3 py-1.5 rounded hover:bg-orange-50"
                  >
                    Return for clarification
                  </button>
                  <button
                    onClick={() => handleReview(item.id, "Rejected")}
                    className="text-sm font-medium border border-red-300 text-red-700 px-3 py-1.5 rounded hover:bg-red-50"
                  >
                    Reject
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
