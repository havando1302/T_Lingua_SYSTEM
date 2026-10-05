import axios from 'axios';
import {
  clearSession,
  configureSessionRefresh,
  getAccessToken,
  sessionNeedsRefresh,
  setSession,
  type LoginResponse,
} from './auth';

declare module 'axios' {
  interface AxiosRequestConfig {
    suppressGlobalError?: boolean;
  }
}

// Requests whose page already renders an inline error should not also create
// the global alert banner.
export const locallyHandledRequest = { suppressGlobalError: true } as const;

function resolveBackendOrigin(): string {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim();
  const fallback = import.meta.env.DEV ? 'http://localhost:8000' : window.location.origin;
  const url = new URL(configured || fallback, window.location.origin);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password
      || url.search || url.hash || url.pathname !== '/') {
    throw new Error('Địa chỉ máy chủ phải là một origin HTTP(S), không kèm đường dẫn hoặc thông tin đăng nhập.');
  }
  const loopback = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if ((import.meta.env.PROD && !loopback && url.protocol !== 'https:')
      || (window.location.protocol === 'https:' && url.protocol !== 'https:')) {
    throw new Error('Máy chủ quản trị phải sử dụng HTTPS.');
  }
  return url.origin;
}

let backendOrigin = window.location.origin;
export let apiConfigurationError = '';
try {
  backendOrigin = resolveBackendOrigin();
} catch (error) {
  apiConfigurationError = error instanceof Error ? error.message : 'Cấu hình máy chủ không hợp lệ.';
}

export function apiErrorMessage(error: unknown, fallback = 'Không thể hoàn tất yêu cầu. Vui lòng thử lại.') {
  if (axios.isCancel(error) || (axios.isAxiosError(error) && (error.code === 'ERR_CANCELED' || error.name === 'CanceledError'))) {
    return '';
  }
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) {
      const detail = error.response?.data?.detail;
      if (detail === 'Invalid or expired credentials') {
        return 'Thông tin đăng nhập hoặc mã xác thực không hợp lệ.';
      }
      return typeof detail === 'string' && detail ? detail : 'Phiên đăng nhập đã hết hạn hoặc thông tin đăng nhập không đúng.';
    }
    if (error.response?.status === 403) {
      const detail = error.response?.data?.detail;
      return typeof detail === 'string' && detail ? detail : 'Tài khoản của bạn không có quyền thực hiện thao tác này.';
    }
    if (error.response?.status === 429) return 'Bạn thao tác quá nhanh. Vui lòng thử lại sau ít phút.';
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      const fieldNames: Record<string, string> = {
        username: 'Tên đăng nhập', password: 'Mật khẩu', name: 'Tên mã API',
        role: 'Chức vụ', is_active: 'Trạng thái tài khoản', body: 'Dữ liệu',
        search: 'Tìm kiếm', corrected_text: 'Bản dịch đã sửa', source_text: 'Văn bản gốc',
        translated_text: 'Bản dịch', expires_in_days: 'Thời hạn', scopes: 'Quyền truy cập', value: 'Giá trị',
      };
      const messages = detail.slice(0, 5).map((issue: { loc?: unknown[]; msg?: unknown; type?: string; ctx?: Record<string, unknown> }) => {
        const field = String(issue.loc?.at(-1) ?? 'Dữ liệu');
        let message = typeof issue.msg === 'string' ? issue.msg.replace(/^Value error, /, '') : 'Giá trị không hợp lệ';
        if (issue.type === 'missing') message = 'Vui lòng nhập trường bắt buộc';
        if (issue.type === 'string_too_long') message = `Tối đa ${issue.ctx?.max_length} ký tự`;
        if (issue.type === 'string_too_short') message = `Ít nhất ${issue.ctx?.min_length} ký tự`;
        if (issue.type === 'greater_than_equal') message = `Giá trị tối thiểu là ${issue.ctx?.ge}`;
        if (issue.type === 'less_than_equal') message = `Giá trị tối đa là ${issue.ctx?.le}`;
        if (issue.type === 'int_parsing' || issue.type === 'int_from_float') message = 'Vui lòng nhập số nguyên';
        if (issue.type === 'literal_error') message = 'Giá trị không thuộc lựa chọn cho phép';
        if (issue.type === 'bool_parsing') message = 'Giá trị trạng thái không hợp lệ';
        if (issue.type === 'extra_forbidden') message = 'Trường dữ liệu không được hỗ trợ';
        if (message.includes('72 UTF-8 bytes')) message = 'Tối đa 72 byte UTF-8; ký tự có dấu có thể chiếm nhiều byte';
        if (message.includes('Username must')) message = 'Ít nhất 3 ký tự, không chứa khoảng trắng';
        return `${fieldNames[field] ?? field}: ${message}`;
      });
      if (messages.length) return messages.join('. ');
    }
    if (!error.response) return 'Không kết nối được máy chủ. Kiểm tra kết nối mạng rồi thử lại.';
    return fallback;
  }
  return error instanceof Error ? error.message : fallback;
}

function createClient(path: string) {
  const client = axios.create({ baseURL: `${backendOrigin}${path}`, timeout: 15000, withCredentials: true });
  client.interceptors.request.use(async (config) => {
    if (apiConfigurationError) throw new Error(apiConfigurationError);
    const target = new URL(client.getUri(config), window.location.origin);
    if (target.origin !== backendOrigin) throw new Error('Không được gửi yêu cầu tới máy chủ khác.');
    if (!target.pathname.endsWith('/login') && sessionNeedsRefresh()) await refreshSession();
    const token = getAccessToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    else delete config.headers.Authorization;
    return config;
  });
  client.interceptors.response.use((response) => response, (error: unknown) => {
    if (axios.isCancel(error) || (axios.isAxiosError(error) && (error.code === 'ERR_CANCELED' || error.name === 'CanceledError'))) {
      return Promise.reject(error);
    }
    if (axios.isAxiosError(error)) {
      const sentAuthorization = error.config?.headers?.Authorization;
      const token = getAccessToken();
      if (error.response?.status === 401 && token && sentAuthorization === `Bearer ${token}`) clearSession();
      if (!error.config?.url?.endsWith('/login') && !error.config?.suppressGlobalError) {
        const message = apiErrorMessage(error);
        if (message) {
          window.dispatchEvent(new CustomEvent('admin:api-error', { detail: message }));
        }
      }
    }
    return Promise.reject(error);
  });
  return client;
}

const api = createClient('/admin');
const sessionApi = createClient('/api/session');

let pendingRefresh: Promise<boolean> | null = null;

export function refreshSession(): Promise<boolean> {
  if (pendingRefresh) return pendingRefresh;
  pendingRefresh = axios.post<LoginResponse>(
    `${backendOrigin}/api/session/refresh`,
    undefined,
    { timeout: 15000, withCredentials: true },
  ).then((response) => {
    setSession(response.data);
    return true;
  }).catch((error: unknown) => {
    const transientFailure = axios.isAxiosError(error)
      && (!error.response || error.response.status >= 500);
    if (!transientFailure) clearSession();
    return transientFailure;
  }).finally(() => {
    pendingRefresh = null;
  });
  return pendingRefresh;
}

configureSessionRefresh(refreshSession);

export async function logout() {
  try {
    await sessionApi.post('/logout');
  } finally {
    clearSession();
  }
}

export default api;
