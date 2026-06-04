import AsyncStorage from '@react-native-async-storage/async-storage';

export const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'https://web-production-ba700.up.railway.app';
const TOKEN_KEY = 'mobile_auth_token';

export async function getToken()           { return AsyncStorage.getItem(TOKEN_KEY); }
export async function saveToken(t: string) { return AsyncStorage.setItem(TOKEN_KEY, t); }
export async function clearToken()         { return AsyncStorage.removeItem(TOKEN_KEY); }

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const token = await getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string> ?? {}),
  };
  if (token) headers['X-Mobile-Token'] = token;

  const res  = await fetch(`${BASE_URL}${path}`, { ...opts, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok || data?.ok === false) {
    throw new Error(data?.error ?? `HTTP ${res.status}`);
  }
  return data as T;
}

// ─── Auth ───────────────────────────────────────────────────────────────────
export const auth = {
  login: async (username: string, password: string) => {
    const d = await req<any>('/api/mobile/login', {
      method: 'POST', body: JSON.stringify({ username, password }),
    });
    if (d.token) await saveToken(d.token);
    return d;
  },
  register: (username: string, email: string, password: string, profileType = 'sahis') =>
    req<any>('/api/mobile/register', {
      method: 'POST', body: JSON.stringify({ username, email, password, profile_type: profileType }),
    }),
  me:     () => req<any>('/api/mobile/me'),
  logout: async () => {
    try { await req('/api/mobile/logout', { method: 'POST' }); } catch {}
    await clearToken();
  },
};

// ─── Özet ───────────────────────────────────────────────────────────────────
export const summary = {
  get: (period = 'month', year?: number, month?: number) => {
    const p = new URLSearchParams({ period });
    if (year)  p.set('year',  String(year));
    if (month) p.set('month', String(month));
    return req<any>(`/api/summary?${p}`);
  },
  today: () => req<any>('/api/today'),
};

// ─── İşlemler ───────────────────────────────────────────────────────────────
export const transactions = {
  list: (params?: Record<string, string>) =>
    req<any[]>(`/api/transactions?${new URLSearchParams(params ?? {})}`),
  create: (d: Record<string, unknown>) =>
    req<any>('/api/transactions', { method: 'POST', body: JSON.stringify(d) }),
  update: (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/transactions/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
  delete: (id: number) =>
    req<any>(`/api/transactions/${id}`, { method: 'DELETE' }),
};

// ─── Kredi Kartları ─────────────────────────────────────────────────────────
export const cards = {
  list:   ()                               => req<any[]>('/api/cards'),
  create: (d: Record<string, unknown>)     => req<any>('/api/cards',     { method: 'POST', body: JSON.stringify(d) }),
  update: (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/cards/${id}`,   { method: 'PUT',  body: JSON.stringify(d) }),
  delete: (id: number)                     => req<any>(`/api/cards/${id}`, { method: 'DELETE' }),
  pay:    (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/cards/${id}/pay`, { method: 'POST', body: JSON.stringify(d) }),
};

// ─── Hesaplar ────────────────────────────────────────────────────────────────
export const accounts = {
  list:   ()                               => req<any[]>('/api/accounts'),
  create: (d: Record<string, unknown>)     => req<any>('/api/accounts',   { method: 'POST', body: JSON.stringify(d) }),
  update: (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/accounts/${id}`, { method: 'PUT',  body: JSON.stringify(d) }),
  delete: (id: number)                     => req<any>(`/api/accounts/${id}`, { method: 'DELETE' }),
};

// ─── Yatırımlar ──────────────────────────────────────────────────────────────
export const investments = {
  list:   () => req<any[]>('/api/investments'),
  create: (d: Record<string, unknown>) =>
    req<any>('/api/investments', { method: 'POST', body: JSON.stringify(d) }),
  delete: (id: number) => req<any>(`/api/investments/${id}`, { method: 'DELETE' }),
};

// ─── Tekrarlayan ─────────────────────────────────────────────────────────────
export const recurring = {
  list:   () => req<any[]>('/api/recurring'),
  create: (d: Record<string, unknown>) =>
    req<any>('/api/recurring', { method: 'POST', body: JSON.stringify(d) }),
  delete: (id: number) => req<any>(`/api/recurring/${id}`, { method: 'DELETE' }),
  apply:  () => req<any>('/api/recurring/apply', { method: 'POST' }),
};

// ─── Hedefler & Bütçe ────────────────────────────────────────────────────────
export const goals = {
  list:   () => req<any[]>('/api/goals'),
  create: (d: Record<string, unknown>) =>
    req<any>('/api/goals', { method: 'POST', body: JSON.stringify(d) }),
  delete: (id: number) => req<any>(`/api/goals/${id}`, { method: 'DELETE' }),
};
export const budgets = {
  save: (d: Record<string, unknown>) =>
    req<any>('/api/budgets', { method: 'POST', body: JSON.stringify(d) }),
};

// ─── Profiller ───────────────────────────────────────────────────────────────
export const profiles = {
  list:   () => req<any[]>('/api/profiles'),
  switch: (id: number) =>
    req<any>(`/api/profiles/${id}/switch`, { method: 'POST' }),
};

// ─── Diğer ───────────────────────────────────────────────────────────────────
export const misc = {
  categories: () => req<any>('/api/categories'),
  reminders:  () => req<any>('/api/reminders'),
  insights:   () => req<any>('/api/insights'),
  notifications: () => req<any>('/api/notifications'),
  rates:      () => req<any>('/api/rates'),
};
