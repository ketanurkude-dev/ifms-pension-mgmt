import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { get } from "../api/apiService";
import AppLayout from "./AppLayout";

export default function Dashboard() {
  const navigate = useNavigate();
  const [pensioner, setPensioner] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    get("/dashboard/me")
      .then(setPensioner)
      .catch(() => {
        setError("Session expired. Please log in again.");
        localStorage.removeItem("access_token");
        setTimeout(() => navigate("/login"), 1500);
      });
  }, [navigate]);

  if (error) {
    return <div className="min-h-screen flex items-center justify-center text-slate-600">{error}</div>;
  }

  if (!pensioner) {
    return <div className="min-h-screen flex items-center justify-center text-slate-600">Loading...</div>;
  }

  const fields = [
    ["PPO number", pensioner.ppo_number],
    ["Retired from", pensioner.retired_from_office],
    ["Date of birth", pensioner.date_of_birth],
    ["Mobile", pensioner.mobile],
    ["Email", pensioner.email || "-"],
    ["Bank", pensioner.bank_name],
    ["Account number", pensioner.bank_account_number],
    ["IFSC", pensioner.bank_ifsc],
  ];

  return (
    <AppLayout>
      <div className="bg-white border border-slate-200 rounded p-6">
        <h1 className="text-xl font-semibold text-slate-800 mb-1">{pensioner.name}</h1>
        <p className="text-sm text-slate-500 mb-6">Welcome to your pensioner dashboard</p>

        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {fields.map(([label, value]) => (
            <div key={label}>
              <dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt>
              <dd className="text-sm text-slate-800 mt-0.5">{value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </AppLayout>
  );
}
