import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';

const VERSIONS = [
  {
    ver: 'v2.6', date: '2026-06', badge: 'Yeni',
    items: [
      '🗂️ Kategoriler: Özel kategori ekleme ve yönetimi',
      '🏷️ Etiketler: İşlem filtreleme ve etiket bulutu',
      '📅 Planlanmış İşlemler: Gelecek tarihli hatırlatıcılar',
      '💰 Para Kaynakları: Aylık gelir takibi',
      '🔐 Güvenlik: Yedek indirme kullanıcıya özel hale getirildi',
      '🛡️ Mobil token yalnızca header ile iletiliyor',
    ],
  },
  {
    ver: 'v2.5', date: '2026-05', badge: null,
    items: [
      '📋 İşlem Şablonları: Sık işlemleri tek tıkla uygula',
      '📁 Projeler: Proje bazlı harcama takibi',
      '🤖 Telegram botu entegrasyonu',
      '🧠 AI analiz sayfası',
      '🔔 Bildirim merkezi',
    ],
  },
  {
    ver: 'v2.4', date: '2026-04', badge: null,
    items: [
      '🏗️ Varlık yönetimi (demirbaş, araç)',
      '🏢 Tedarikçi ve fatura takibi',
      '📊 Kart bakiye raporu',
      '🔄 Hesaplar arası transfer',
    ],
  },
  {
    ver: 'v2.3', date: '2026-03', badge: null,
    items: [
      '📈 Yatırım portföyü (TEFAS, hisse, altın)',
      '💱 Canlı döviz kurları',
      '👥 Çoklu profil desteği',
      '✅ Yapılacaklar listesi',
    ],
  },
  {
    ver: 'v2.2', date: '2026-02', badge: null,
    items: [
      '🔄 Tekrarlayan gelir/gider',
      '🎯 Hedef ve bütçe takibi',
      '📤 Excel/PDF dışa aktarma',
      '🌙 Karanlık tema',
    ],
  },
  {
    ver: 'v2.0', date: '2026-01', badge: null,
    items: [
      '💳 Kredi kartı yönetimi',
      '🏦 Çoklu banka hesabı',
      '📊 Aylık/yıllık raporlar',
      '📱 Mobil uygulama ilk sürümü',
    ],
  },
];

export default function ChangelogScreen() {
  const router = useRouter();
  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Değişiklik Günlüğü</Text>
      </View>
      <ScrollView showsVerticalScrollIndicator={false}>
        {VERSIONS.map((v, i) => (
          <View key={v.ver} style={[s.card, i === 0 && s.cardFirst]}>
            <View style={s.cardHeader}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Text style={s.ver}>{v.ver}</Text>
                {v.badge && <View style={s.badge}><Text style={s.badgeTxt}>{v.badge}</Text></View>}
              </View>
              <Text style={s.date}>{v.date}</Text>
            </View>
            {v.items.map((item, j) => (
              <View key={j} style={s.item}>
                <Text style={s.itemTxt}>{item}</Text>
              </View>
            ))}
          </View>
        ))}
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:         { flex: 1, backgroundColor: C.bg },
  header:     { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8, gap: 12 },
  back:       { fontSize: 24, color: C.txt },
  title:      { fontSize: 20, fontWeight: '800', color: C.txt },
  card:       { marginHorizontal: 16, marginBottom: 12, backgroundColor: C.card, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: C.border },
  cardFirst:  { borderColor: C.blue, backgroundColor: 'rgba(0,122,255,0.05)' },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  ver:        { fontSize: 17, fontWeight: '800', color: C.txt },
  badge:      { backgroundColor: C.blue, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  badgeTxt:   { fontSize: 11, fontWeight: '700', color: C.white },
  date:       { fontSize: 12, color: C.txt2 },
  item:       { flexDirection: 'row', paddingVertical: 4 },
  itemTxt:    { fontSize: 14, color: C.txt2, flex: 1, lineHeight: 20 },
});
