import { createContext, useContext, useState } from "react";
import { put } from "../api/apiService";
import { hi } from "./hi";

const LanguageContext = createContext(null);

// Per FR-PP-127: switchable from any screen, retained across sessions.
// localStorage gives instant same-browser persistence. syncWithAccount()
// (called once the pensioner record is known, post-login) reconciles the
// account's saved preference with whatever is active locally:
//  - if the user never explicitly chose a language on this browser, adopt
//    the account's saved preference (it follows the pensioner across
//    devices).
//  - if the user DID explicitly choose one already (including at the
//    pre-login language toggle, which can't call the API yet), that choice
//    wins and gets pushed to the account instead of being overwritten --
//    otherwise picking Hindi at the login screen would flip back to
//    English the moment the account's stored default loads.
export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => localStorage.getItem("language") || "en");

  function setLanguage(next, persist = true) {
    setLanguageState(next);
    localStorage.setItem("language", next);
    localStorage.setItem("language_explicit", "1");
    if (persist) {
      put("/dashboard/language", { language: next }).catch(() => {});
    }
  }

  function syncWithAccount(accountLanguage) {
    if (!accountLanguage) return;
    const explicit = localStorage.getItem("language_explicit") === "1";
    if (explicit) {
      if (accountLanguage !== language) {
        put("/dashboard/language", { language }).catch(() => {});
      }
      return;
    }
    if (accountLanguage !== language) {
      setLanguageState(accountLanguage);
      localStorage.setItem("language", accountLanguage);
    }
  }

  function t(key) {
    if (language === "hi") {
      return hi[key] || key;
    }
    return key;
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage, syncWithAccount, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within a LanguageProvider");
  return ctx;
}
