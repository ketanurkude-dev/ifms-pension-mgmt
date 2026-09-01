import { useEffect, useState } from "react";
import { get } from "./apiService";

// Small shared hook so any page/layout can know who is logged in and
// their role, without re-fetching it in more than one place.
export function useCurrentPensioner() {
  const [pensioner, setPensioner] = useState(null);

  useEffect(() => {
    get("/dashboard/me").then(setPensioner).catch(() => setPensioner(null));
  }, []);

  return pensioner;
}
