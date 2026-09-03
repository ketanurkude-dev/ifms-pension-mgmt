import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useCurrentPensioner } from "../api/useCurrentPensioner";
import { useLanguage } from "../i18n/LanguageContext";
import {
  AnnouncementIcon,
  ApproverIcon,
  ArrearsIcon,
  AuditIcon,
  BankIcon,
  DashboardIcon,
  GrievanceIcon,
  HistoryIcon,
  LifeCertificateIcon,
  ProfileIcon,
  ReportIcon,
  RequestsIcon,
  SlipIcon,
  TaxIcon,
} from "./Icons";

const navItems = [
  { to: "/dashboard", label: "Dashboard", Icon: DashboardIcon },
  { to: "/profile", label: "Profile", Icon: ProfileIcon },
  { to: "/pension-slip", label: "Pension slip", Icon: SlipIcon },
  { to: "/disbursements", label: "Disbursement history", Icon: HistoryIcon },
  { to: "/arrears-benefits", label: "Arrears & benefits", Icon: ArrearsIcon },
  { to: "/tax", label: "Tax", Icon: TaxIcon },
  { to: "/bank-requests", label: "Bank details", Icon: BankIcon },
  { to: "/life-certificate", label: "Life certificate", Icon: LifeCertificateIcon },
  { to: "/grievances", label: "Grievances", Icon: GrievanceIcon },
  { to: "/my-requests", label: "My requests", Icon: RequestsIcon },
  { to: "/announcements", label: "Announcements", Icon: AnnouncementIcon },
  { to: "/reports", label: "Reports", Icon: ReportIcon },
];

// Shared header + left sidebar nav for every page after login.
export default function AppLayout({ children }) {
  const navigate = useNavigate();
  const pensioner = useCurrentPensioner();
  const isApprover = pensioner && pensioner.role === "pension_officer";
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const { language, setLanguage, syncWithAccount, t } = useLanguage();

  // Once we know the pensioner's saved preference, adopt it (per FR-PP-127
  // the choice follows the account, not just the browser).
  useEffect(() => {
    if (pensioner?.preferred_language) {
      syncWithAccount(pensioner.preferred_language);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pensioner?.preferred_language]);

  function handleLogout() {
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  const linkClass = ({ isActive }) =>
    `flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-md ${
      isActive ? "bg-blue-800 text-white" : "text-slate-600 hover:bg-slate-100"
    }`;

  const approverLinkClass = ({ isActive }) =>
    `flex items-center gap-3 px-4 py-2.5 text-sm font-medium rounded-md ${
      isActive ? "bg-orange-600 text-white" : "text-orange-700 hover:bg-orange-50"
    }`;

  return (
    <div className="h-screen flex flex-col bg-slate-100">
      <header className="bg-blue-900 text-white shrink-0">
        <div className="px-4 sm:px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setSidebarVisible(!sidebarVisible)}
              className="mr-1 p-1.5 rounded hover:bg-white/10"
              aria-label={t("Toggle sidebar")}
              title={t("Toggle sidebar")}
            >
              <div className="w-5 h-0.5 bg-white mb-1" />
              <div className="w-5 h-0.5 bg-white mb-1" />
              <div className="w-5 h-0.5 bg-white" />
            </button>
            <div className="w-7 h-7 rounded bg-white/10 border border-white/20 flex items-center justify-center text-xs font-semibold">
              PP
            </div>
            <span className="font-semibold text-sm">{t("Pensioner Portal")}</span>
            {pensioner && (
              <>
                <span className="text-sm text-white/90 ml-3 hidden sm:inline">{pensioner.name}</span>
                <span className="text-xs text-blue-100/70 border border-white/20 rounded px-2 py-0.5 ml-2">
                  {t(pensioner.role)}
                </span>
              </>
            )}
          </div>
          <div className="flex items-center gap-2">
            <div className="flex border border-white/30 rounded overflow-hidden text-xs font-medium">
              <button
                onClick={() => setLanguage("en")}
                className={`px-2.5 py-1 ${language === "en" ? "bg-white text-blue-900" : "hover:bg-white/10"}`}
              >
                EN
              </button>
              <button
                onClick={() => setLanguage("hi")}
                className={`px-2.5 py-1 ${language === "hi" ? "bg-white text-blue-900" : "hover:bg-white/10"}`}
              >
                हिं
              </button>
            </div>
            <button
              onClick={handleLogout}
              className="text-sm border border-white/30 hover:bg-white/10 px-3 py-1.5 rounded"
            >
              {t("Logout")}
            </button>
          </div>
        </div>
        <div className="h-1 bg-orange-500" />
      </header>

      <div className="flex flex-1 min-h-0">
        {sidebarVisible && (
          <aside className="w-56 shrink-0 bg-white border-r border-slate-200 h-full overflow-y-auto p-3">
            <nav className="space-y-1">
              {navItems.map(({ to, label, Icon }) => (
                <NavLink key={to} to={to} className={linkClass}>
                  <Icon style={{ width: 18, height: 18 }} className="shrink-0" />
                  {t(label)}
                </NavLink>
              ))}
              {isApprover && (
                <>
                  <NavLink to="/approver" className={approverLinkClass}>
                    <ApproverIcon style={{ width: 18, height: 18 }} className="shrink-0" />
                    {t("Approver")}
                  </NavLink>
                  <NavLink to="/audit-log" className={approverLinkClass}>
                    <AuditIcon style={{ width: 18, height: 18 }} className="shrink-0" />
                    {t("Audit log")}
                  </NavLink>
                </>
              )}
            </nav>
          </aside>
        )}

        <main className="flex-1 min-w-0 h-full overflow-y-auto px-4 sm:px-6 py-6">
          <div className="max-w-5xl mx-auto">{children}</div>
        </main>
      </div>

      <footer className="shrink-0 bg-white border-t border-slate-200 px-4 sm:px-6 py-2 flex items-center justify-end gap-2 text-xs text-slate-400">
        <span>{t("Developed by")}</span>
        <img src="/virtualgalaxy-logo.webp" alt="Virtual Galaxy" className="h-5" />
      </footer>
    </div>
  );
}
