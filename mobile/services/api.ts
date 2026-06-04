import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'https://web-production-ba700.up.railway.app';
const TOKEN_KEY = 'mobile_auth_token';

export async function getToken(): Promise<string | null> {
  return AsyncStorage.getItem(TOKEN_KEY);
}

export async function setToken(token: string): Promise<void> {
  return AsyncStorage.setItem(TOKEN_KEY, token);
}

export async function clearToken(): Promise<void> {
  return AsyncStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> ?? {}),
  };
  if (token) headers['X-Mobile-Token'] = token;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  const data = await res.json();
  if (!res.ok || data.ok === false) {
    throw new Error(data.error ?? `HTTP ${res.status}`);
  }
  return data as T;
}

export const api = {
  auth: {
    login: async (username: string, password: string) => {
      const data = await request<any>('/api/mobile/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });
      if (data.token) await setToken(data.token);
      return data;
    },
    me: () => request<any>('/api/mobile/me'),
    logout: async () => {
      await request('/api/mobile/logout', { method: 'POST' });
      await clearToken();
    },
  },

  summary: (profileId: number, year?: number, month?: number) => {
    const p = new URLSearchParams({ profile_id: String(profileId) });
    if (year)  p.set('year',  String(year));
    if (month) p.set('month', String(month));
    return request<any>(`/api/summary?${p}`);
  },

  transactions: {
    list: (profileId: number, params?: Record<string, string>) => {
      const p = new URLSearchParams({ profile_id: String(profileId), ...params });
      return request<any>(`/api/transactions?${p}`);
    },
    create: (payload: Record<string, unknown>) =>
      request<any>('/api/transactions', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id: number, payload: Record<string, unknown>) =>
      request<any>(`/api/transactions/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    delete: (id: number) =>
      request<any>(`/api/transactions/${id}`, { method: 'DELETE' }),
  },

  cards:    { list: (pid: number) => request<any>(`/api/cards?profile_id=${pid}`) },
  accounts: { list: (pid: number) => request<any>(`/api/accounts?profile_id=${pid}`) },
  goals: {
    list:   (pid: number) => request<any>(`/api/goals?profile_id=${pid}`),
    create: (p: Record<string, unknown>) => request<any>('/api/goals', { method: 'POST', body: JSON.stringify(p) }),
    delete: (id: number) => request<any>(`/api/goals/${id}`, { method: 'DELETE' }),
  },
  budgets:  { save: (p: Record<string, unknown>) => request<any>('/api/budgets', { method: 'POST', body: JSON.stringify(p) }) },
  insights: (pid: number) => request<any>(`/api/insights?profile_id=${pid}`),
  today:    (pid: number) => request<any>(`/api/today?profile_id=${pid}`),
  categories: () => request<any>('/api/categories'),
};
