import { useEffect, useState } from "react";
import { get } from "../api/apiService";
import { useLanguage } from "../i18n/LanguageContext";
import AppLayout from "./AppLayout";

export default function Profile() {
  const { t } = useLanguage();
  const [pensioner, setPensioner] = useState(null);

  useEffect(() => {
    get("/dashboard/me").then(setPensioner);
  }, []);

  if (!pensioner) {
    return (
      <AppLayout>
        <p className="text-slate-500 text-sm">{t("Loading...")}</p>
      </AppLayout>
    );
  }

  const fields = [
    [t("PPO number"), pensioner.ppo_number],
    [t("Full name"), pensioner.name],
    [t("Basic pension"), `Rs. ${pensioner.basic_pension}`],
    [t("Date of birth"), pensioner.date_of_birth],
    [t("Retired from office"), pensioner.retired_from_office],
    [t("Mobile"), pensioner.mobile],
    [t("Email"), pensioner.email || "-"],
    [t("Bank name"), pensioner.bank_name],
    [t("Account number"), pensioner.bank_account_number],
    [t("IFSC"), pensioner.bank_ifsc],
  ];

  return (
    <AppLayout>
      <div className="bg-white border border-slate-200 rounded p-6">
        <h1 className="font-semibold text-slate-800 mb-1">{t("Profile")}</h1>
        <p className="text-sm text-slate-500 mb-5">{t("Bank details can only be changed via a request — see Bank details.")}</p>

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
