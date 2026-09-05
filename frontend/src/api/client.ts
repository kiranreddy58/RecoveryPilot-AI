// Empty string uses Vite proxy (/api → http://localhost:8000/api)
// Set VITE_API_BASE_URL to override (e.g. for production)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
export const API_V1 = `${API_BASE_URL}/api/v1`;

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export interface ApiError {
  error: { code: string; message: string };
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  meta?: Record<string, any>;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err?.detail || err?.error || `HTTP ${response.status}`);
  }
  const json: ApiResponse<T> = await response.json();
  if (json.success === false) throw new Error(json.error || 'Request failed');
  return json.data !== undefined ? json.data : (json as any);
}

export const api = {
  get: <T>(path: string) => request<T>(`${API_V1}${path}`),
  post: <T>(path: string, body?: any) =>
    request<T>(`${API_V1}${path}`, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
};

class ApiClient {
  async getHealth(): Promise<HealthResponse> {
    const response = await fetch(`/api/v1/health`);
    if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
    return response.json();
  }
}

export const apiClient = new ApiClient();
