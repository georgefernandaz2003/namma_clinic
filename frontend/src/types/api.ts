/**
 * Core API Types matching Django REST Framework conventions
 * Authoritative Backend Contract: docs/FRONTEND_API_CONTRACT.md
 */

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiErrorResponse {
  detail?: string;
  error?: string;
  code?: string;
  messages?: Array<{
    token_class?: string;
    token_type?: string;
    message?: string;
  }>;
  details?: Record<string, unknown>;
  [field: string]: unknown;
}

export type QueryParams = Record<string, string | number | boolean | undefined | null>;
