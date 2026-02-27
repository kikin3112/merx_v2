import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

const STORAGE_KEY = 'chandelier-auth';

/**
 * Read auth state directly from localStorage (zustand persist storage).
 * This avoids the circular dependency: client -> authStore -> endpoints -> client
 */
function getPersistedAuth(): { token: string | null; tenantId: string | null; refreshToken: string | null } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { token: null, tenantId: null, refreshToken: null };
    const parsed = JSON.parse(raw);
    const state = parsed?.state;
    return {
      token: state?.token ?? null,
      tenantId: state?.tenantId ?? null,
      refreshToken: state?.refreshToken ?? null,
    };
  } catch {
    return { token: null, tenantId: null, refreshToken: null };
  }
}

/**
 * Write updated tokens back to localStorage (zustand persist format).
 */
function updatePersistedTokens(accessToken: string, refreshToken: string) {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    parsed.state.token = accessToken;
    parsed.state.refreshToken = refreshToken;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(parsed));
  } catch {
    // ignore
  }
}

function clearPersistedAuth() {
  localStorage.removeItem(STORAGE_KEY);
}

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor: add auth token and tenant ID from localStorage
client.interceptors.request.use((config) => {
  const { token, tenantId } = getPersistedAuth();
  // Only inject stored token if request doesn't already carry its own Authorization
  // (e.g. clerk-exchange passes the Clerk JWT explicitly)
  if (token && !config.headers['Authorization']) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (tenantId) {
    config.headers['X-Tenant-ID'] = tenantId;
  }
  return config;
});

// Response interceptor: handle 401 with token refresh
let isRefreshing = false;
let refreshQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

function processQueue(error: unknown, token: string | null) {
  refreshQueue.forEach((p) => {
    if (token) p.resolve(token);
    else p.reject(error);
  });
  refreshQueue = [];
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      const { refreshToken, tenantId } = getPersistedAuth();

      if (!refreshToken) {
        clearPersistedAuth();
        window.location.href = '/login';
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue this request until the ongoing refresh completes
        return new Promise((resolve, reject) => {
          refreshQueue.push({
            resolve: (newToken: string) => {
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              resolve(client(originalRequest));
            },
            reject,
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Call refresh directly with a raw axios instance (no interceptors)
        const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
          refresh_token: refreshToken,
          tenant_id: tenantId || undefined,
        });

        const newToken = data.access_token;
        const newRefreshToken = data.refresh_token;

        // Update localStorage so the zustand store picks it up
        updatePersistedTokens(newToken, newRefreshToken);

        // Also update the zustand store in memory (lazy import to avoid circular dep)
        try {
          const { useAuthStore } = await import('../stores/authStore');
          useAuthStore.setState({ token: newToken, refreshToken: newRefreshToken });
        } catch {
          // If import fails, localStorage is already updated
        }

        processQueue(null, newToken);

        // Retry original request
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return client(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        clearPersistedAuth();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default client;
