import { View, Text, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';

const FAQS = [
  {
    q: 'Nasıl işlem eklerim?',
    a: 'Alt menüdeki + butonuna basın. İşlem türü (gelir/gider), tutarı, tarih ve kategoriyi doldurup kaydedin.',
  },
  {
    q: 'Kredi kartı borçlarımı nasıl takip ederim?',
    a: 'Daha Fazla → Kredi Kartları bölümüne gidin. Kartınızı ekleyin ve her harcamayı kart ödemesi olarak kaydedin. Ekstre tarihi geldiğinde "Öde" butonuyla ödeme yapın.',
  },
  {
    q: 'Tekrarlayan giderleri nasıl otomatikleştiririm?',
    a: 'Daha Fazla → Tekrarlayan İşlemler. Kira, abonelik gibi sabit giderleri buradan tanımlayın. "Uygula" butonuyla tek tıkla bu ay kayıt ekleyin.',
  },
  {
    q: 'Birden fazla hesabım var, nasıl yönetirim?',
    a: 'Daha Fazla → Hesaplar bölümünden banka hesaplarınızı ekleyin. İşlem girerken hangi hesaptan yapıldığını seçebilirsiniz.',
  },
  {
    q: 'Verilerimi nasıl yedeklerim / dışa aktarırım?',
    a: 'Daha Fazla → Ayarlar → Dışa Aktarma. Excel veya PDF olarak aylık raporunuzu indirip mailinize gönderebilirsiniz.',
  },
  {
    q: 'Aile veya şirket profili nasıl oluştururum?',
    a: 'Daha Fazla → Profiller → Yeni Profil. Sahis, Aile veya Şirket türü seçin. Her profil tamamen bağımsız veri tutar.',
  },
  {
    q: 'Yatırım portföyümü nasıl takip ederim?',
    a: 'Daha Fazla → Yatırımlar. Hisse, TEFAS, altın veya diğer yatırımlarınızı ekleyin. Anlık fiyat güncellemesi otomatik yapılır.',
  },
  {
    q: 'Planlanmış işlem ne işe yarar?',
    a: 'Gelecek tarihli hatırlatıcı gibi çalışır. "Daha Fazla → Planlanmış" bölümünde tarih ve tutar girin; işlem tarihi geldiğinde size hatırlatılır ve tek tıkla uygulanır.',
  },
  {
    q: 'Hesabımı nasıl silerim?',
    a: 'Daha Fazla → Ayarlar → Hesap Yönetimi → Hesabı Sil. Bu işlem geri alınamaz ve tüm verileriniz silinir.',
  },
  {
    q: 'Şifremi unuttum, ne yapmalıyım?',
    a: 'Giriş ekranındaki "Şifremi Unuttum" bağlantısını kullanın. Kayıtlı e-posta adresinize sıfırlama bağlantısı gönderilir.',
  },
];

export default function HelpScreen() {
  const router = useRouter();
  const [open, setOpen] = useState<number | null>(null);

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Yardım & SSS</Text>
      </View>
      <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
        <Text style={s.sub}>Sık sorulan sorular</Text>
        {FAQS.map((faq, i) => (
          <TouchableOpacity key={i} style={s.card} activeOpacity={0.8} onPress={() => setOpen(open === i ? null : i)}>
            <View style={s.qRow}>
              <Text style={s.q}>{faq.q}</Text>
              <Text style={[s.chev, open === i && s.chevOpen]}>{open === i ? '▲' : '▼'}</Text>
            </View>
            {open === i && <Text style={s.a}>{faq.a}</Text>}
          </TouchableOpacity>
        ))}

        <View style={s.contactCard}>
          <Text style={s.contactTitle}>📬 Destek</Text>
          <Text style={s.contactTxt}>Sorunuz hâlâ çözülmediyse destek ekibimize ulaşın.</Text>
          <View style={s.contactBadge}>
            <Text style={s.contactBadgeTxt}>destek@kirpifinans.com</Text>
          </View>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:         { flex: 1, backgroundColor: C.bg },
  header:     { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 4, gap: 12 },
  back:       { fontSize: 24, color: C.txt },
  title:      { fontSize: 20, fontWeight: '800', color: C.txt },
  sub:        { fontSize: 13, color: C.txt2, paddingHorizontal: 16, marginTop: 4, marginBottom: 12 },
  card:       { marginHorizontal: 16, marginBottom: 8, backgroundColor: C.card, borderRadius: 14, padding: 16, borderWidth: 1, borderColor: C.border },
  qRow:       { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  q:          { fontSize: 15, fontWeight: '600', color: C.txt, flex: 1, lineHeight: 22 },
  chev:       { fontSize: 12, color: C.muted, marginTop: 4 },
  chevOpen:   { color: C.blue },
  a:          { fontSize: 14, color: C.txt2, marginTop: 10, lineHeight: 22 },
  contactCard: { marginHorizontal: 16, marginTop: 20, backgroundColor: 'rgba(0,122,255,0.08)', borderRadius: 16, padding: 16, borderWidth: 1, borderColor: 'rgba(0,122,255,0.2)' },
  contactTitle: { fontSize: 16, fontWeight: '700', color: C.txt, marginBottom: 6 },
  contactTxt:   { fontSize: 13, color: C.txt2, marginBottom: 12 },
  contactBadge: { backgroundColor: C.input, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8, alignSelf: 'flex-start' },
  contactBadgeTxt: { fontSize: 13, color: C.blue, fontWeight: '600' },
});
