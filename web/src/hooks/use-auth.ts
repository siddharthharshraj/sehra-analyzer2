"use client";

import { useState, useEffect, useCallback } from "react";
import { apiPost } from "@/lib/api-client";
import {
  getToken,
  setToken,
  getStoredUser,
  setStoredUser,
  logout as doLogout,
  isAuthenticated,
} from "@/lib/auth";
import type { UserInfo, TokenResponse } from "@/lib/types";

export function useAuth() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored && isAuthenticated()) {
      setUser(stored);
    }
    setLoading(false);
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const res = await apiPost<TokenResponse>("/auth/login", {
      username,
      password,
    });
    setToken(res.access_token);
    setStoredUser(res.user);
    setUser(res.user);
    return res.user;
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    doLogout();
  }, []);

  return { user, loading, login, logout, isAuthenticated: !!user };
}
