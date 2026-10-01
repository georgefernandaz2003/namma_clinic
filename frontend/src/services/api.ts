/**
 * Backward-compatible bridge to centralized API client.
 * Refactored in Phase 21 to use src/api/client.ts with automated token refresh,
 * structured error parsing, and configurable base URL.
 */
import apiClient, { API_BASE_URL, parseApiError } from '../api/client';

export { apiClient, API_BASE_URL, parseApiError };
export default apiClient;
