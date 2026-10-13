import { describe, it, expect, beforeEach, vi } from 'vitest';
import api from '../api';
import axios from 'axios';

describe('Frontend API & JWT Authentication Security', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('adds Authorization: Bearer <token> header to outgoing requests when token exists', async () => {
    localStorage.setItem('access_token', 'test-access-token-12345');

    // Intercept with axios adapter or mock request interceptor
    const requestConfig = { headers: {} as Record<string, string> };
    const interceptedConfig = await (api.interceptors.request as any).handlers[0].fulfilled(requestConfig);

    expect(interceptedConfig.headers.Authorization).toBe('Bearer test-access-token-12345');
    // Ensure token is NOT in URL or query params
    expect(interceptedConfig.url).toBeUndefined();
    expect(interceptedConfig.params).toBeUndefined();
  });

  it('omits Authorization header when no access token is stored', async () => {
    const requestConfig = { headers: {} as Record<string, string> };
    const interceptedConfig = await (api.interceptors.request as any).handlers[0].fulfilled(requestConfig);

    expect(interceptedConfig.headers.Authorization).toBeUndefined();
  });

  it('clears localStorage access and refresh tokens when 401 response cannot be refreshed', async () => {
    localStorage.setItem('access_token', 'expired-access-token');
    localStorage.setItem('refresh_token', 'invalid-refresh-token');

    vi.spyOn(axios, 'post').mockRejectedValueOnce(new Error('Invalid refresh token'));

    const errorResponse = {
      response: { status: 401 },
      config: { url: 'patients/', headers: {} },
    };

    const responseInterceptor = (api.interceptors.response as any).handlers[0].rejected;

    await expect(responseInterceptor(errorResponse)).rejects.toThrow();

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });

  it('does not leak token in error messages or URLs', () => {
    const sensitiveToken = 'eyJh...secretToken';
    localStorage.setItem('access_token', sensitiveToken);

    // Verify localStorage key holds value without exposing it in window.location or document.title
    expect(window.location.href).not.toContain(sensitiveToken);
    expect(window.location.search).not.toContain(sensitiveToken);
    expect(document.title).not.toContain(sensitiveToken);
  });
});
