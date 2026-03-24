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

/**
 * Decode the JWT payload (base64url) to extract user info.
 * Falls back to the user cookie if the token is missing or malformed.
 */
function decodeJwtPayload(token: string): UserInfo | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const decoded = JSON.parse(atob(payload));
    if (decoded.sub && decoded.name) {
      return {
        username: decoded.sub,
        name: decoded.name,
        role: decoded.role || "viewer",
      };
    }
    return null;
  } catch {
    return null;
  }
}

export function getStoredUser(): UserInfo | null {
  if (typeof window === "undefined") return null;
  // Try to decode user from JWT first
  const token = getToken();
  if (token) {
    const fromJwt = decodeJwtPayload(token);
    if (fromJwt) return fromJwt;
  }
  // Fallback: read from secure cookie
  const raw = Cookies.get(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserInfo;
  } catch {
    return null;
  }
}

export function setStoredUser(user: UserInfo): void {
  // Store in cookie instead of localStorage for security
  Cookies.set(USER_KEY, JSON.stringify(user), {
    expires: 1,
    sameSite: "lax",
  });
}

export function clearStoredUser(): void {
  Cookies.remove(USER_KEY);
}

export function logout(): void {
  removeToken();
  clearStoredUser();
  window.location.href = "/login";
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
