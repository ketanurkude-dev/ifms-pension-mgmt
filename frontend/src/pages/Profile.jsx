import { useEffect, useState } from "react";
import { get } from "../api/apiService";
import AppLayout from "./AppLayout";

export default function Profile() {
  const [pensioner, setPensioner] = useState(null);

  useEffect(() => {
    get("/dashboard/me").then(setPensioner);
  }, []);

  if (!pensioner) {
    return (
      <AppLayout>
        <p className="text-slate-500 text-sm">Loading...</p>
      </AppLayout>
    );
  }

  const fields = [
    ["PPO number", pensioner.ppo_number],
    ["Full name", pensioner.name],
    ["Date of birth", pensioner.date_of_birth],
    ["Retired from office", pensioner.retired_from_office],
    ["Mobile", pensioner.mobile],
    ["Email", pensioner.email || "-"],
    ["Bank name", pensioner.bank_name],
    ["Account number", pensioner.bank_account_number],
    ["IFSC", pensioner.bank_ifsc],
  ];

  return (
    <AppLayout>
      <div className="bg-white border border-slate-200 rounded p-6">
        <h1 className="font-semibold text-slate-800 mb-1">Profile</h1>
        <p className="text-sm text-slate-500 mb-5">
          Bank details can only be changed via a request &mdash; see Bank details.
        </p>

        <dl className="divide-y divide-slate-100">
          {fields.map(([label, value]) => (
            <div key={label} className="flex items-center justify-between py-2.5 text-sm">
              <dt className="text-slate-500">{label}</dt>
              <dd className="text-slate-800 font-medium">{value}</dd>
            </div>
          ))}
        </dl>
      </div>
    </AppLayout>
  );
}
