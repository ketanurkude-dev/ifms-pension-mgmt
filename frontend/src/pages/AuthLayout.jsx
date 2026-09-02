import { useLanguage } from "../i18n/LanguageContext";

// Shared two-column layout for the login, OTP and register screens:
// a branded left panel, and the form on the right.
export default function AuthLayout({ title, subtitle, children }) {
  const { language, setLanguage, t } = useLanguage();

  return (
    <div className="min-h-screen flex bg-slate-50">
      <div className="hidden lg:flex lg:w-1/2 relative flex-col justify-between bg-blue-900 p-12 text-white border-r border-blue-950">
        <div className="absolute top-0 left-0 w-full h-1.5 bg-orange-500" />

        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded bg-white/10 border border-white/20 flex items-center justify-center text-sm font-semibold">
              PP
            </div>
            <span className="text-base font-semibold tracking-wide">{t("Pensioner Portal")}</span>
          </div>
          <p className="text-blue-100/70 text-sm ml-[48px]">{t("Integrated Financial Management System")}</p>
        </div>

        <div className="max-w-sm">
          <h2 className="text-2xl font-semibold leading-snug mb-4">
            {t("One account for your pension, disbursements and requests")}
          </h2>
          <p className="text-blue-100/80 text-sm leading-relaxed">
            {t(
              "View your pension slip, track disbursement history, and raise requests such as a bank account change — then follow them through approval."
            )}
          </p>
        </div>

        <p className="text-xs text-blue-100/50">
          &copy; {new Date().getFullYear()} {t("Pensioner Portal")}. {t("For authorised use only.")}
        </p>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-10">
        <div className="w-full max-w-md">
          <div className="flex items-center justify-between mb-8">
            <div className="lg:hidden flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-blue-800 text-white flex items-center justify-center text-sm font-semibold">
                PP
              </div>
              <span className="font-semibold text-slate-800">{t("Pensioner Portal")}</span>
            </div>
            <div className="flex border border-slate-300 rounded overflow-hidden text-xs font-medium ml-auto">
              <button
                onClick={() => setLanguage("en", false)}
                className={`px-2.5 py-1 ${language === "en" ? "bg-blue-800 text-white" : "text-slate-600 hover:bg-slate-100"}`}
              >
                EN
              </button>
              <button
                onClick={() => setLanguage("hi", false)}
                className={`px-2.5 py-1 ${language === "hi" ? "bg-blue-800 text-white" : "text-slate-600 hover:bg-slate-100"}`}
              >
                हिं
              </button>
            </div>
          </div>

          <h1 className="text-2xl font-semibold text-slate-800 mb-1">{title}</h1>
          {subtitle && <p className="text-sm text-slate-500 mb-8">{subtitle}</p>}

          {children}

          <div className="flex items-center justify-center gap-2 mt-10 text-xs text-slate-400">
            <span>{t("Developed by")}</span>
            <img src="/virtualgalaxy-logo.webp" alt="Virtual Galaxy" className="h-5" />
          </div>
        </div>
      </div>
    </div>
  );
}
