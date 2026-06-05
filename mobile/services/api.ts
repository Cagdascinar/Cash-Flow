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
  list:             ()                               => req<any[]>('/api/cards'),
  create:           (d: Record<string, unknown>)     => req<any>('/api/cards',     { method: 'POST', body: JSON.stringify(d) }),
  update:           (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/cards/${id}`,   { method: 'PUT',  body: JSON.stringify(d) }),
  delete:           (id: number)                     => req<any>(`/api/cards/${id}`, { method: 'DELETE' }),
  pay:              (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/cards/${id}/pay`, { method: 'POST', body: JSON.stringify(d) }),
  dailyReport:      ()                               => req<any>('/api/cards/daily-report'),
  addDailyBalance:  (id: number, balance: number)    =>
    req<any>('/api/cards/daily-balance', { method: 'POST', body: JSON.stringify({ card_id: id, balance }) }),
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
  list:       () => req<any[]>('/api/investments'),
  create:     (d: Record<string, unknown>) =>
    req<any>('/api/investments', { method: 'POST', body: JSON.stringify(d) }),
  delete:     (id: number) => req<any>(`/api/investments/${id}`, { method: 'DELETE' }),
  sell:       (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/investments/${id}/sell`, { method: 'POST', body: JSON.stringify(d) }),
  bookIncome: (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/investments/${id}/book-income`, { method: 'POST', body: JSON.stringify(d) }),
  value: () => req<any>('/api/investments/value'),
  tefas: (kod: string) => req<any>(`/api/tefas/${kod}`),
};

// ─── Tekrarlayan ─────────────────────────────────────────────────────────────
export const recurring = {
  list:   () => req<any[]>('/api/recurring'),
  create: (d: Record<string, unknown>) =>
    req<any>('/api/recurring', { method: 'POST', body: JSON.stringify(d) }),
  update: (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/recurring/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
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
  create: (d: Record<string, unknown>) =>
    req<any>('/api/profiles', { method: 'POST', body: JSON.stringify(d) }),
  delete: (id: number) => req<any>(`/api/profiles/${id}`, { method: 'DELETE' }),
  switch: (id: number) =>
    req<any>(`/api/profiles/${id}/switch`, { method: 'POST' }),
};

// ─── Tedarikçiler ────────────────────────────────────────────────────────────
export const suppliers = {
  list:   () => req<any[]>('/api/suppliers'),
  create: (d: Record<string, unknown>) =>
    req<any>('/api/suppliers', { method: 'POST', body: JSON.stringify(d) }),
  update: (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/suppliers/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
  delete: (id: number) => req<any>(`/api/suppliers/${id}`, { method: 'DELETE' }),
};

// ─── Varlıklar ───────────────────────────────────────────────────────────────
export const assets = {
  list:   () => req<any[]>('/api/assets'),
  create: (d: Record<string, unknown>) =>
    req<any>('/api/assets', { method: 'POST', body: JSON.stringify(d) }),
  update: (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/assets/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
  delete:         (id: number) => req<any>(`/api/assets/${id}`, { method: 'DELETE' }),
  maintenance:    (id: number) => req<any[]>(`/api/assets/${id}/maintenance`),
  addMaintenance: (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/assets/${id}/maintenance`, { method: 'POST', body: JSON.stringify(d) }),
  delMaintenance: (mid: number) =>
    req<any>(`/api/assets/maintenance/${mid}`, { method: 'DELETE' }),
};

// ─── Hesap Yönetimi ──────────────────────────────────────────────────────────
export const me = {
  update:         (d: Record<string, unknown>) =>
    req<any>('/api/me/update', { method: 'POST', body: JSON.stringify(d) }),
  changePassword: (d: Record<string, unknown>) =>
    req<any>('/api/me/password', { method: 'POST', body: JSON.stringify(d) }),
  delete:         () => req<any>('/api/me/delete', { method: 'POST' }),
};

// ─── Diğer ───────────────────────────────────────────────────────────────────
export const misc = {
  categories:     () => req<any>('/api/categories'),
  reminders:      () => req<any>('/api/reminders'),
  insights:       () => req<any>('/api/insights'),
  notifications:  () => req<any>('/api/notifications'),
  rates:          () => req<any>('/api/rates'),
  transfer:       (d: Record<string, unknown>) =>
    req<any>('/api/transfers', { method: 'POST', body: JSON.stringify(d) }),
  today:          () => req<any>('/api/today'),
  telegramStatus: () => req<any>('/api/telegram/status'),
  telegramLinkCode: () => req<any>('/api/telegram/link-code', { method: 'POST' }),
  telegramUnlink: () => req<any>('/api/telegram/unlink', { method: 'DELETE' }),
  todos:          (date?: string) => req<any>(`/api/todos${date ? `?date=${date}` : ''}`),
  addTodo:        (d: Record<string, unknown>) =>
    req<any>('/api/todos', { method: 'POST', body: JSON.stringify(d) }),
  updateTodo:     (id: number, d: Record<string, unknown>) =>
    req<any>(`/api/todos/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
  deleteTodo:     (id: number) =>
    req<any>(`/api/todos/${id}`, { method: 'DELETE' }),
  supplierInvoices: (status = 'bekleyen') =>
    req<any>(`/api/supplier-invoices?status=${status}`),
  addSupplierInvoice: (d: Record<string, unknown>) =>
    req<any>('/api/supplier-invoices', { method: 'POST', body: JSON.stringify(d) }),
  paySupplierInvoice: (id: number) =>
    req<any>(`/api/supplier-invoices/${id}/pay`, { method: 'POST' }),
  deleteSupplierInvoice: (id: number) =>
    req<any>(`/api/supplier-invoices/${id}`, { method: 'DELETE' }),
  supplierInvoiceAging: () => req<any>('/api/supplier-invoices/aging'),
  exportExcel: () => `${BASE_URL}/api/export/excel`,
  exportPdf:   () => `${BASE_URL}/api/export/pdf`,
  motivation:  () => req<any>('/api/motivation'),
};
