const BASE_URL = 'http://localhost:8000/api/v1';

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
}

export const getTokens = () => {
  const access = localStorage.getItem('access_token');
  const refresh = localStorage.getItem('refresh_token');
  return { access, refresh };
};

export const setTokens = (access: string, refresh: string) => {
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);
};

export const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

async function refreshToken(): Promise<string | null> {
  const { refresh } = getTokens();
  if (!refresh) return null;

  try {
    const res = await fetch(`${BASE_URL}/auth/refresh?refresh_token_in=${encodeURIComponent(refresh)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!res.ok) {
      clearTokens();
      return null;
    }

    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch (error) {
    clearTokens();
    return null;
  }
}

export async function request(endpoint: string, options: RequestOptions = {}): Promise<any> {
  let { access } = getTokens();
  
  const headers = new Headers(options.headers || {});
  if (access) {
    headers.set('Authorization', `Bearer ${access}`);
  }

  // Handle URL search parameters if any
  let url = `${BASE_URL}${endpoint}`;
  if (options.params) {
    const searchParams = new URLSearchParams(options.params);
    url += `?${searchParams.toString()}`;
  }

  const fetchOptions: RequestInit = {
    ...options,
    headers,
  };

  try {
    let response = await fetch(url, fetchOptions);

    // If unauthorized, attempt token refresh once
    if (response.status === 401) {
      const newAccess = await refreshToken();
      if (newAccess) {
        // Retry request with new token
        const newHeaders = new Headers(options.headers || {});
        newHeaders.set('Authorization', `Bearer ${newAccess}`);
        fetchOptions.headers = newHeaders;
        response = await fetch(url, fetchOptions);
      } else {
        // Redirect to login if token refresh fails
        window.dispatchEvent(new Event('auth_session_expired'));
        throw new Error('Session expired');
      }
    }

    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new Error(errData.detail || `HTTP error ${response.status}`);
    }

    // Response can be plain text for file downloads (markdown export) or JSON
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return await response.json();
    } else {
      return await response.text();
    }
  } catch (error) {
    throw error;
  }
}

// Named exports for API operations
export const authApi = {
  register: (body: any) => request('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }),
  login: (formData: URLSearchParams) => request('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me', { method: 'GET' }),
};

export const repositoryApi = {
  list: () => request('/repositories', { method: 'GET' }),
  upload: (formData: FormData) => request('/repositories/upload', {
    method: 'POST',
    body: formData,
  }),
  clone: (formData: FormData) => request('/repositories/clone', {
    method: 'POST',
    body: formData,
  }),
  delete: (id: string) => request(`/repositories/${id}`, { method: 'DELETE' }),
};

export const analysisApi = {
  create: (repositoryId: string) => request('/analyses', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_id: repositoryId }),
  }),
  getStatus: (id: string) => request(`/analyses/${id}`, { method: 'GET' }),
  listRepoAnalyses: (repoId: string) => request(`/analyses/repo/${repoId}`, { method: 'GET' }),
};

export const reportApi = {
  getByAnalysis: (analysisId: string) => request(`/reports/analysis/${analysisId}`, { method: 'GET' }),
  getByRepository: (repoId: string) => request(`/reports/repository/${repoId}`, { method: 'GET' }),
  search: (query: string) => request('/reports/search', {
    method: 'GET',
    params: { query },
  }),
  exportMarkdown: (reportId: string) => request(`/reports/${reportId}/export`, {
    method: 'GET',
  }),
};

export const dashboardApi = {
  getStats: () => request('/dashboard/stats', { method: 'GET' }),
};
