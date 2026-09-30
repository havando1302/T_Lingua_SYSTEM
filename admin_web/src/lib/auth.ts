import { useSyncExternalStore } from 'react';

export type Role = 'employee' | 'admin' | 'superadmin';
export interface AuthUser {
  id: number;
  username: string;
  role: Role;
  public_id?: string;
  is_active?: boolean;
}
export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

let accessToken: string | null = null;
let currentUser: AuthUser | null = null;
let expiresAt = 0;
let expirationTimer: ReturnType<typeof setTimeout> | undefined;
const listeners = new Set<() => void>();

// Old releases persisted credentials. A page load always starts signed out.
for (const storageName of ['localStorage', 'sessionStorage'] as const) {
  try {
    window[storageName].removeItem('token');
    window[storageName].removeItem('access_token');
  } catch {
    // Storage may be unavailable; authentication never depends on it.
  }
}

function emitChange() {
  listeners.forEach((listener) => listener());
}

export function clearSession() {
  accessToken = null;
  currentUser = null;
  expiresAt = 0;
  clearTimeout(expirationTimer);
  emitChange();
}

export function getAccessToken() {
  if (accessToken && Date.now() >= expiresAt) clearSession();
  return accessToken;
}

export function isAuthUser(user: unknown): user is AuthUser {
  if (!user || typeof user !== 'object') return false;
  const candidate = user as Partial<AuthUser>;
  return typeof candidate.id === 'number' && typeof candidate.username === 'string'
    && ['employee', 'admin', 'superadmin'].includes(candidate.role ?? '')
    && candidate.is_active !== false;
}

export function setSession(session: LoginResponse) {
  if (!session.access_token || session.token_type?.toLowerCase() !== 'bearer'
      || !Number.isFinite(session.expires_in) || session.expires_in <= 0
      || !isAuthUser(session.user)) {
    throw new Error('Phản hồi đăng nhập không hợp lệ.');
  }
  clearTimeout(expirationTimer);
  accessToken = session.access_token;
  currentUser = session.user;
  expiresAt = Date.now() + session.expires_in * 1000;
  expirationTimer = setTimeout(clearSession, Math.min(session.expires_in * 1000, 2_147_483_647));
  emitChange();
}

export function updateSessionUser(user: unknown) {
  if (!getAccessToken() || !isAuthUser(user)) {
    clearSession();
    throw new Error('Phiên đăng nhập không còn hợp lệ.');
  }
  currentUser = user;
  emitChange();
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

export function useAuthUser() {
  return useSyncExternalStore(subscribe, () => currentUser, () => null);
}

export function homeFor(user: AuthUser) {
  return user.role === 'employee' ? '/account' : '/';
}
