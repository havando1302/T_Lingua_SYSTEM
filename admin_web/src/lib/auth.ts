import { useSyncExternalStore } from 'react';

export type Role = 'employee' | 'admin' | 'superadmin';
export interface AuthUser {
  id: number;
  username: string;
  role: Role;
  public_id?: string;
  is_active?: boolean;
  created_at?: string | null;
  mfa_enabled?: boolean;
}
export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}
export interface MfaChallenge {
  status: 'mfa_required' | 'mfa_setup_required';
  mfa_required: true;
  enrollment_required: boolean;
  issuer?: string | null;
  account_name?: string | null;
  secret?: string | null;
  provisioning_uri?: string | null;
}
export type LoginResult = LoginResponse | MfaChallenge;

export function isMfaChallenge(result: LoginResult): result is MfaChallenge {
  return 'status' in result && result.mfa_required === true;
}

let accessToken: string | null = null;
let currentUser: AuthUser | null = null;
let expiresAt = 0;
let expirationTimer: ReturnType<typeof setTimeout> | undefined;
let refreshSession: (() => Promise<boolean>) | undefined;
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
  if (accessToken && Date.now() >= expiresAt) return null;
  return accessToken;
}

export function sessionNeedsRefresh(bufferMs = 30_000) {
  return !accessToken || Date.now() >= expiresAt - bufferMs;
}

export function configureSessionRefresh(handler: () => Promise<boolean>) {
  refreshSession = handler;
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
  const refreshDelay = Math.max(
    1_000,
    session.expires_in * 1000 - Math.min(30_000, session.expires_in * 500),
  );
  expirationTimer = setTimeout(() => {
    if (!refreshSession) {
      clearSession();
      return;
    }
    void refreshSession().then((restored) => {
      if (!restored) clearSession();
    }, clearSession);
  }, Math.min(refreshDelay, 2_147_483_647));
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

export function homeFor(_user: AuthUser) {
  return '/';
}

export const roleLabels: Record<Role, string> = {
  employee: 'Nhân viên nghiệp vụ',
  admin: 'Quản trị viên',
  superadmin: 'Quản trị cấp cao',
};
