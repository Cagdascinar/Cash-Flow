export const C = {
  bg:      '#0b0e11',
  card:    '#1e2026',
  input:   '#2b2f36',
  border:  '#2b2f36',
  green:   '#0ecb81',
  red:     '#f6465d',
  yellow:  '#f0b90b',
  blue:    '#007aff',
  txt:     '#eaecef',
  txt2:    '#848e9c',
  muted:   '#4b5563',
  tab:     '#131720',
  white:   '#ffffff',
  hero:    '#0d1f3c',
};

// Para formatla
export function money(n: number, decimals = 0) {
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency', currency: 'TRY',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(n ?? 0);
}

// Kısa para
export function moneyShort(n: number) {
  if (!n) return '₺0';
  const abs = Math.abs(n);
  const sign = n < 0 ? '-' : '';
  if (abs >= 1e6) return `${sign}₺${(abs / 1e6).toFixed(1)}M`;
  if (abs >= 1e3) return `${sign}₺${(abs / 1e3).toFixed(1)}B`;
  return `${sign}₺${Math.round(abs)}`;
}

// Tarih
export function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
}
