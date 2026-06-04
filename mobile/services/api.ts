import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'https://web-production-ba700.up.railway.app';
const TOKEN_KEY = 'mobile_auth_token';

export async function getToken() { return AsyncStorage.getItem(TOKEN_KEY); }
export async function setToken(t: string) { return AsyncStorage.setItem(TOKEN_KEY, t); }
export async function clearToken() { return AsyncStorage.removeItem(TOKEN_KEY); }

async function req<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> ?? {}),
  };
  if (token) headers['X-Mobile-Token'] = token;
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  const data = await res.json();
  if (!res.ok || data.ok === false) throw new Error(data.error ?? `HTTP ${res.status}`);
  return data as T;
}

export const api = {
  auth: {
    login: async (username: string, password: string) => {
      const data = await req<any>('/api/mobile/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });
      if (data.token) await setToken(data.token);
      return data;
    },
    me:     () => req<any>('/api/mobile/me'),
    logout: async () => {
      try { await req('/api/mobile/logout', { method: 'POST' }); } catch {}
      await clearToken();
    },
  },

  // Server profile_id'yi session'dan alıyor, query param opsiyonel
  summary: (year?: number, month?: number, period = 'month') => {
    const p = new URLSearchParams({ period });
    if (year)  p.set('year',  String(year));
    if (month) p.set('month', String(month));
    return req<any>(`/api/summary?${p}`);
  },

  transactions: {
    list: (params?: Record<string, string>) => {
      const p = new URLSearchParams(params ?? {});
      return req<any[]>(`/api/transactions?${p}`);
    },
    create: (payload: Record<string, unknown>) =>
      req<any>('/api/transactions', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id: number, payload: Record<string, unknown>) =>
      req<any>(`/api/transactions/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    delete: (id: number) =>
      req<any>(`/api/transactions/${id}`, { method: 'DELETE' }),
  },

  cards:    { list: () => req<any>('/api/cards') },
  accounts: { list: () => req<any>('/api/accounts') },
  investments: { list: () => req<any>('/api/investments') },
  recurring:   { list: () => req<any>('/api/recurring') },
  suppliers:   { list: () => req<any>('/api/suppliers') },
  assets:      { list: () => req<any>('/api/assets') },

  goals: {
    list:   () => req<any>('/api/goals'),
    create: (p: Record<string, unknown>) => req<any>('/api/goals', { method: 'POST', body: JSON.stringify(p) }),
    delete: (id: number) => req<any>(`/api/goals/${id}`, { method: 'DELETE' }),
  },
  budgets: {
    save: (p: Record<string, unknown>) => req<any>('/api/budgets', { method: 'POST', body: JSON.stringify(p) }),
  },
  today:      () => req<any>('/api/today'),
  insights:   () => req<any>('/api/insights'),
  reminders:  () => req<any>('/api/reminders'),
  categories: () => req<any>('/api/categories'),
  profiles:   () => req<any>('/api/profiles'),
};
