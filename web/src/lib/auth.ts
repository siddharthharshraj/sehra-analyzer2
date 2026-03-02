import Cookies from "js-cookie";
import type { UserInfo } from "./types";

const TOKEN_KEY = "sehra_token";
const USER_KEY = "sehra_user";

export function getToken(): string | undefined {
  return Cookies.get(TOKEN_KEY);
}

export function setToken(token: string): void {
  Cookies.set(TOKEN_KEY, token, { expires: 1, sameSite: "lax" });
}

export function removeToken(): void {
  Cookies.remove(TOKEN_KEY);
}

export function getStoredUser(): UserInfo | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserInfo;
  } catch {
    return null;
  }
}

export function setStoredUser(user: UserInfo): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearStoredUser(): void {
  localStorage.removeItem(USER_KEY);
}

export function logout(): void {
  removeToken();
  clearStoredUser();
  window.location.href = "/login";
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
