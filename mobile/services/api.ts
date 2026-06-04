import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'https://your-railway-url.up.railway.app';

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    credentials: 'include',
    ...options,
  });

  const data = await res.json();
  if (!res.ok || data.ok === false) {
    throw new Error(data.error ?? `HTTP ${res.status}`);
  }
  return data as T;
}

// Auth
export const api = {
  auth: {
    login: (username: string, password: string) =>
      request('/api/mobile/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
    register: (username: string, email: string, password: string) =>
      request('/register', {
        method: 'POST',
        body: JSON.stringify({ username, email, password }),
      }),
    me: () => request('/api/mobile/me'),
    logout: () => request('/api/mobile/logout', { method: 'POST' }),
  },

  summary: (profileId: number, year?: number, month?: number) => {
    const params = new URLSearchParams({ profile_id: String(profileId) });
    if (year) params.set('year', String(year));
    if (month) params.set('month', String(month));
    return request(`/api/summary?${params}`);
  },

  transactions: {
    list: (profileId: number, params?: Record<string, string>) => {
      const p = new URLSearchParams({ profile_id: String(profileId), ...params });
      return request(`/api/transactions?${p}`);
    },
    create: (payload: Record<string, unknown>) =>
      request('/api/transactions', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id: number, payload: Record<string, unknown>) =>
      request(`/api/transactions/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    delete: (id: number) =>
      request(`/api/transactions/${id}`, { method: 'DELETE' }),
  },

  cards: {
    list: (profileId: number) =>
      request(`/api/cards?profile_id=${profileId}`),
  },

  accounts: {
    list: (profileId: number) =>
      request(`/api/accounts?profile_id=${profileId}`),
  },

  budgets: {
    save: (payload: Record<string, unknown>) =>
      request('/api/budgets', { method: 'POST', body: JSON.stringify(payload) }),
  },

  goals: {
    list: (profileId: number) => request(`/api/goals?profile_id=${profileId}`),
    create: (payload: Record<string, unknown>) =>
      request('/api/goals', { method: 'POST', body: JSON.stringify(payload) }),
    delete: (id: number) => request(`/api/goals/${id}`, { method: 'DELETE' }),
  },

  insights: (profileId: number) =>
    request(`/api/insights?profile_id=${profileId}`),

  categories: () => request('/api/categories'),

  today: (profileId: number) =>
    request(`/api/today?profile_id=${profileId}`),
};
