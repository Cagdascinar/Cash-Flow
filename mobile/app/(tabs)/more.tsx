import { View, Text, ScrollView, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { useEffect, useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../../constants/Colors';
import { cards as cardsApi, auth } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

function Row({ ico, label, sub, right, onPress, danger }: { ico: string; label: string; sub?: string; right?: string; onPress: () => void; danger?: boolean }) {
  return (
    <TouchableOpacity style={r.row} onPress={onPress} activeOpacity={0.7}>
      <View style={r.left}>
        <View style={[r.ico, danger && { backgroundColor: '#2a1018' }]}>
          <Text style={r.icoTxt}>{ico}</Text>
        </View>
        <View>
          <Text style={[r.lbl, danger && { color: C.red }]}>{label}</Text>
          {sub && <Text style={r.sub}>{sub}</Text>}
        </View>
      </View>
      <View style={r.right}>
        {right && <Text style={r.rightTxt}>{right}</Text>}
        <Text style={r.chevron}>›</Text>
      </View>
    </TouchableOpacity>
  );
}
const r = StyleSheet.create({
  row:      { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 14 },
  left:     { flexDirection: 'row', alignItems: 'center', gap: 12, flex: 1 },
  ico:      { width: 36, height: 36, borderRadius: 10, backgroundColor: C.input, alignItems: 'center', justifyContent: 'center' },
  icoTxt:   { fontSize: 18 },
  lbl:      { fontSize: 15, fontWeight: '600', color: C.txt },
  sub:      { fontSize: 12, color: C.txt2, marginTop: 1 },
  right:    { flexDirection: 'row', alignItems: 'center', gap: 4 },
  rightTxt: { fontSize: 13, color: C.txt2 },
  chevron:  { fontSize: 20, color: C.muted },
});

export default function MoreScreen() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const [cardsList, setCList] = useState<any[]>([]);

  useEffect(() => {
    cardsApi.list().then(d => setCList(Array.isArray(d) ? d : [])).catch(() => {});
  }, []);

  const totalDebt  = cardsList.reduce((s, c) => s + (c.used_  ?? 0), 0);
  const totalLimit = cardsList.reduce((s, c) => s + (c.limit_ ?? 0), 0);
  const soon = () => Alert.alert('Yakında', 'Bu özellik yakında eklenecek');

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={s.header}><Text style={s.title}>Daha Fazla</Text></View>

        {/* Profil */}
        <View style={s.profile}>
          <View style={s.avatar}><Text style={s.avatarTxt}>{user?.username?.[0]?.toUpperCase() ?? '?'}</Text></View>
          <View style={{ flex: 1 }}>
            <Text style={s.username}>{user?.username}</Text>
            <Text style={s.email}>{user?.email}</Text>
          </View>
          <View style={user?.is_premium ? s.proBadge : s.trialBadge}>
            <Text style={user?.is_premium ? s.proTxt : s.trialTxt}>{user?.is_premium ? 'PRO' : 'Deneme'}</Text>
          </View>
        </View>

        {/* Kart özeti kartı */}
        {cardsList.length > 0 && (
          <TouchableOpacity style={s.cardBanner} onPress={() => router.push('/cards' as any)}>
            <View style={s.cbItem}>
              <Text style={[s.cbVal, { color: C.red }]}>{money(totalDebt)}</Text>
              <Text style={s.cbLbl}>Toplam Borç</Text>
            </View>
            <View style={s.cbDiv} />
            <View style={s.cbItem}>
              <Text style={[s.cbVal, { color: C.green }]}>{money(totalLimit - totalDebt)}</Text>
              <Text style={s.cbLbl}>Kullanılabilir</Text>
            </View>
            <View style={s.cbDiv} />
            <View style={s.cbItem}>
              <Text style={s.cbVal}>{cardsList.length}</Text>
              <Text style={s.cbLbl}>Kart</Text>
            </View>
            <Text style={{ fontSize: 18, color: C.muted }}>›</Text>
          </TouchableOpacity>
        )}

        <Text style={s.grp}>Finans</Text>
        <View style={s.group}>
          <Row ico="💳" label="Kredi Kartları" sub={`${cardsList.length} kart`} right={money(totalDebt)} onPress={() => router.push('/cards' as any)} />
          <View style={s.sep} />
          <Row ico="🏦" label="Hesaplar" sub="Banka hesapları" onPress={() => router.push('/accounts' as any)} />
          <View style={s.sep} />
          <Row ico="📈" label="Yatırımlar" sub="Portföy takibi" onPress={soon} />
          <View style={s.sep} />
          <Row ico="🔄" label="Tekrarlayan İşlemler" onPress={soon} />
        </View>

        <Text style={s.grp}>Kurumsal</Text>
        <View style={s.group}>
          <Row ico="🏢" label="Tedarikçiler" onPress={soon} />
          <View style={s.sep} />
          <Row ico="🏗️" label="Varlıklar" sub="Demirbaş ve araçlar" onPress={soon} />
          <View style={s.sep} />
          <Row ico="📄" label="Faturalar" onPress={soon} />
        </View>

        <Text style={s.grp}>Araçlar</Text>
        <View style={s.group}>
          <Row ico="🤖" label="Telegram Botu" sub="Mesajla işlem gir" onPress={soon} />
          <View style={s.sep} />
          <Row ico="📤" label="Dışa Aktar" sub="Excel / PDF" onPress={soon} />
        </View>

        <View style={[s.group, { marginTop: 16 }]}>
          <Row ico="🚪" label="Çıkış Yap" onPress={async () => {
            Alert.alert('Çıkış', 'Oturumu kapatmak istiyor musunuz?', [
              { text: 'İptal', style: 'cancel' },
              { text: 'Çıkış Yap', style: 'destructive', onPress: async () => { await auth.logout(); logout(); } },
            ]);
          }} danger />
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:  { flex: 1, backgroundColor: C.bg },
  header:     { paddingHorizontal: 16, paddingTop: 8 },
  title:      { fontSize: 24, fontWeight: '800', color: C.txt },
  profile:    { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginTop: 16, backgroundColor: C.card, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: C.border, gap: 12 },
  avatar:     { width: 48, height: 48, borderRadius: 24, backgroundColor: C.blue, alignItems: 'center', justifyContent: 'center' },
  avatarTxt:  { fontSize: 20, fontWeight: '700', color: C.white },
  username:   { fontSize: 16, fontWeight: '700', color: C.txt },
  email:      { fontSize: 13, color: C.txt2, marginTop: 2 },
  proBadge:   { backgroundColor: C.blue, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  proTxt:     { fontSize: 11, fontWeight: '800', color: C.white },
  trialBadge: { backgroundColor: C.input, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  trialTxt:   { fontSize: 11, fontWeight: '600', color: C.txt2 },
  cardBanner: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginTop: 12, backgroundColor: C.card, borderRadius: 14, borderWidth: 1, borderColor: C.border, padding: 14, gap: 0 },
  cbItem:     { flex: 1, alignItems: 'center' },
  cbVal:      { fontSize: 14, fontWeight: '800', color: C.txt },
  cbLbl:      { fontSize: 10, color: C.txt2, marginTop: 2 },
  cbDiv:      { width: 1, height: 32, backgroundColor: C.border },
  grp:        { fontSize: 11, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 1.2, paddingHorizontal: 16, marginTop: 24, marginBottom: 8 },
  group:      { marginHorizontal: 16, backgroundColor: C.card, borderRadius: 16, borderWidth: 1, borderColor: C.border, overflow: 'hidden' },
  sep:        { height: 1, backgroundColor: C.border, marginLeft: 62 },
});
