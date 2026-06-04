// Web uygulamasıyla birebir eşleştirilmiş renk sistemi
export const Colors = {
  // Arka planlar
  bg:      '#0b0e11',   // --bg
  bgCard:  '#1e2026',   // --bg2
  bgInput: '#2b2f36',   // --bg3
  bgAlt:   '#363c45',   // --bg4

  // Sınırlar
  border:  '#2b2f36',   // --border
  border2: '#363c45',   // --border2

  // Ana renkler
  green:   '#0ecb81',   // --g  (gelir)
  red:     '#f6465d',   // --r  (gider)
  yellow:  '#f0b90b',   // --y  (uyarı / kart borcu)
  blue:    '#007aff',   // iOS mavi (butonlar, linkler)
  purple:  '#af52de',   // --p

  // Yazı
  textPrimary:   '#eaecef',  // --txt
  textSecondary: '#848e9c',  // --txt2
  textMuted:     '#4b5563',

  // Hero kart degradesi
  heroBg: ['#050e22', '#0d1f3c', '#1a3a6b', '#0f2244'] as const,

  // Tab bar
  tabBar: '#131720',

  white: '#ffffff',

  // Kısayollar
  primary: '#007aff',  // iOS blue = web'deki buton rengi
};
