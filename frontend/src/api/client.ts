import axios, { AxiosError } from 'axios';
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type { ApiErrorResponse } from '../types/api';

/**
 * Authoritative API Client for Namma Clinic.
 * Contract reference: docs/FRONTEND_API_CONTRACT.md
 */

export const getApiBaseUrl = (): string => {
  const envUrl = (import.meta as any).env?.VITE_API_BASE_URL;
  if (envUrl) {
    return envUrl.endsWith('/') ? envUrl : `${envUrl}/`;
  }
  return 'http://localhost:8000/api/';
};

export const API_BASE_URL = getApiBaseUrl();

// Flag and waiting subscriber queue for 401 token refresh deduplication
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else if (token) {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
});

// Request Interceptor: Attach JWT Bearer Access Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Transparent Refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorResponse>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (!error.response || !originalRequest) {
      return Promise.reject(error);
    }

    const status = error.response.status;
    const url = originalRequest.url || '';

    // Do NOT intercept auth endpoints (login, refresh failure should fail directly)
    const isAuthEndpoint = url.includes('auth/token/') || url.includes('auth/token/refresh/');

    if (status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      const refreshToken = localStorage.getItem('refresh_token');

      if (!refreshToken) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return Promise.reject(error);
      }

      if (isRefreshing) {
        // Queue concurrent requests
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Direct call to refresh endpoint without using the interceptor instance
        const response = await axios.post<{ access: string }>(
          `${API_BASE_URL}auth/token/refresh/`,
          { refresh: refreshToken },
          {
            headers: { 'Content-Type': 'application/json' },
            timeout: 10000,
          }
        );

        const newAccessToken = response.data.access;
        localStorage.setItem('access_token', newAccessToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        }

        processQueue(null, newAccessToken);
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

/**
 * Standard DRF error extractor
 * Parses standard DRF error shapes, validation dictionaries, and custom domain errors.
 */
export const parseApiError = (error: unknown): string => {
  if (!error) return 'An unexpected error occurred.';
  if (typeof error === 'string') return error;

  const axiosErr = error as AxiosError<ApiErrorResponse>;
  if (!axiosErr.response) {
    if (axiosErr.message === 'Network Error') {
      return 'Unable to connect to local Django server. Please ensure the backend is running.';
    }
    if (axiosErr.code === 'ECONNABORTED') {
      return 'Request timed out after 15 seconds. Please try again.';
    }
    return axiosErr.message || 'Unknown network error.';
  }

  const data = axiosErr.response.data;
  if (!data) return `HTTP ${axiosErr.response.status}: ${axiosErr.response.statusText}`;

  // 1. Direct detail field
  if (typeof data.detail === 'string') {
    return data.detail;
  }

  // 2. Custom domain error string
  if (typeof data.error === 'string') {
    return data.error;
  }

  // 3. JWT token error messages array
  if (Array.isArray(data.messages) && data.messages.length > 0) {
    const firstMsg = data.messages[0];
    if (firstMsg && typeof firstMsg.message === 'string') {
      return firstMsg.message;
    }
  }

  // 4. Non field errors array
  if (Array.isArray((data as any).non_field_errors) && (data as any).non_field_errors.length > 0) {
    return String((data as any).non_field_errors[0]);
  }

  // 5. DRF Field Validation errors dictionary (e.g. { username: ['This field is required.'] })
  if (typeof data === 'object') {
    const entries = Object.entries(data);
    for (const [field, val] of entries) {
      if (field === 'code' || field === 'details') continue;
      if (Array.isArray(val) && val.length > 0) {
        const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
        return `${fieldName}: ${val[0]}`;
      }
      if (typeof val === 'string') {
        const fieldName = field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
        return `${fieldName}: ${val}`;
      }
    }
  }

  return `Request failed with HTTP status ${axiosErr.response.status}.`;
};

export default apiClient;
