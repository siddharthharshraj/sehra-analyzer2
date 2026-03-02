"use client";

import { useState, useEffect, useCallback } from "react";
import Cookies from "js-cookie";

const COOKIE_KEY = "sidebar_collapsed";

export function useSidebarCollapsed() {
  const [collapsed, setCollapsed] = useState(false);

  // Read cookie on mount (client only)
  useEffect(() => {
    const stored = Cookies.get(COOKIE_KEY);
    if (stored === "true") {
      setCollapsed(true);
    }
  }, []);

  const toggle = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      Cookies.set(COOKIE_KEY, String(next), { expires: 365, sameSite: "lax" });
      return next;
    });
  }, []);

  return { collapsed, toggle };
}
