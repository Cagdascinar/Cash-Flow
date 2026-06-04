import {
  View, Text, ScrollView, StyleSheet,
  TouchableOpacity, Alert, ActivityIndicator,
} from 'react-native';
import { useState, useEffect } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/Colors';
import { cards as cardsApi, auth } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

function Row({ icon, label, sub, onPress, danger, badge }: {
  icon: string; label: string; sub?: string;
  onPress: () => void; danger?: boolean; badge?: string;
}) {
  return (
    <TouchableOpacity style={s.row} onPress={onPress} activeOpacity={0.7}>
      <View style={s.rowLeft}>
        <View style={[s.ico, danger && { backgroundColor: '#2A1018' }]}>
          <Text style={s.icoTxt}>{icon}</Text>
        </View>
        <View>
          <Text style={[s.rowLabel, danger && { color: Colors.red }]}>{label}</Text>
          {sub && <Text style={s.rowSub}>{sub}</Text>}
        </View>
      </View>
      <View style={s.rowRight}>
        {badge && <View style={s.badge}><Text style={s.badgeTxt}>{badge}</Text></View>}
        <Text style={s.chevron}>›</Text>
      </View>
    </TouchableOpacity>
  );
}

export default function MoreScreen() {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const [cardsList, setCards]   = useState<any[]>([]);
  const [loading,   setLoading] = useState(true);

  useEffect(() => {
    cardsApi.list()
      .then(d => setCards(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleLogout() {
    Alert.alert('Çıkış', 'Oturumu kapatmak istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Çıkış Yap', style: 'destructive', onPress: async () => {
        await auth.logout();
        logout();
      }},
    ]);
  }

  const fmt = (n: number) =>
    new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 0 }).format(n);

  const totalDebt  = cardsList.reduce((s, c) => s + (c.used_  ?? 0), 0);
  const totalLimit = cardsList.reduce((s, c) => s + (c.limit_ ?? 0), 0);

  const soon = () => Alert.alert('Yakında', 'Bu özellik yakında eklenecek');

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={s.header}><Text style={s.title}>Daha Fazla</Text></View>

        {/* Profil */}
        <View style={s.profileCard}>
          <View style={s.avatar}>
            <Text style={s.avatarTxt}>{user?.username?.charAt(0).toUpperCase() ?? '?'}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={s.username}>{user?.username}</Text>
            <Text style={s.email}>{user?.email}</Text>
          </View>
          {user?.is_premium
            ? <View style={s.proBadge}><Text style={s.proTxt}>PRO</Text></View>
            : <View style={s.trialBadge}><Text style={s.trialTxt}>Deneme</Text></View>
          }
        </View>

        {/* Kart özeti */}
        {!loading && cardsList.length > 0 && (
          <TouchableOpacity style={s.cardSummary} onPress={() => router.push('/cards' as any)}>
            <View style={s.csItem}>
              <Text style={[s.csVal, { color: Colors.red }]}>{fmt(totalDebt)}</Text>
              <Text style={s.csLabel}>Toplam Borç</Text>
            </View>
            <View style={s.divV} />
            <View style={s.csItem}>
              <Text style={[s.csVal, { color: Colors.green }]}>{fmt(totalLimit - totalDebt)}</Text>
              <Text style={s.csLabel}>Kullanılabilir</Text>
            </View>
            <View style={s.divV} />
            <View style={s.csItem}>
              <Text style={s.csVal}>{cardsList.length}</Text>
              <Text style={s.csLabel}>Kart</Text>
            </View>
            <Text style={s.csChevron}>›</Text>
          </TouchableOpacity>
        )}

        <Text style={s.groupLabel}>Finans</Text>
        <View style={s.group}>
          <Row icon="💳" label="Kredi Kartları"
            sub={cardsList.length > 0 ? `${cardsList.length} kart · ${fmt(totalDebt)} borç` : 'Kart yok'}
            onPress={() => router.push('/cards' as any)}
            badge={cardsList.length > 0 ? String(cardsList.length) : undefined}
          />
          <View style={s.sep} />
          <Row icon="🏦" label="Hesaplar" sub="Banka hesapları ve bakiyeler"
            onPress={() => router.push('/accounts' as any)} />
          <View style={s.sep} />
          <Row icon="📈" label="Yatırımlar" sub="Portföy takibi"
            onPress={soon} />
          <View style={s.sep} />
          <Row icon="🔄" label="Tekrarlayan İşlemler" sub="Otomatik gider ve gelirler"
            onPress={soon} />
        </View>

        <Text style={s.groupLabel}>Kurumsal</Text>
        <View style={s.group}>
          <Row icon="🏢" label="Tedarikçiler"        onPress={soon} />
          <View style={s.sep} />
          <Row icon="🏗️" label="Varlıklar" sub="Demirbaş ve araçlar" onPress={soon} />
          <View style={s.sep} />
          <Row icon="📄" label="Faturalar"            onPress={soon} />
        </View>

        <Text style={s.groupLabel}>Araçlar</Text>
        <View style={s.group}>
          <Row icon="🤖" label="Telegram Botu" sub="Mesajla işlem gir"  onPress={soon} />
          <View style={s.sep} />
          <Row icon="📤" label="Dışa Aktar"    sub="Excel / PDF"        onPress={soon} />
          <View style={s.sep} />
          <Row icon="📥" label="İçe Aktar"     sub="Banka ekstresi CSV" onPress={soon} />
        </View>

        <View style={s.group}>
          <Row icon="🚪" label="Çıkış Yap" onPress={handleLogout} danger />
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: Colors.bg },
  header:      { paddingHorizontal: 16, paddingTop: 8 },
  title:       { fontSize: 24, fontWeight: '800', color: Colors.textPrimary },
  profileCard: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginTop: 16, backgroundColor: Colors.bgCard, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: Colors.border, gap: 12 },
  avatar:      { width: 48, height: 48, borderRadius: 24, backgroundColor: Colors.blue, alignItems: 'center', justifyContent: 'center' },
  avatarTxt:   { fontSize: 20, fontWeight: '700', color: Colors.white },
  username:    { fontSize: 16, fontWeight: '700', color: Colors.textPrimary },
  email:       { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  proBadge:    { backgroundColor: Colors.blue,  borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  proTxt:      { fontSize: 11, fontWeight: '800', color: Colors.white },
  trialBadge:  { backgroundColor: Colors.bgInput, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  trialTxt:    { fontSize: 11, fontWeight: '600', color: Colors.textSecondary },
  cardSummary: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginTop: 12, backgroundColor: Colors.bgCard, borderRadius: 14, borderWidth: 1, borderColor: Colors.border, padding: 14 },
  csItem:      { flex: 1, alignItems: 'center' },
  csVal:       { fontSize: 15, fontWeight: '800', color: Colors.textPrimary },
  csLabel:     { fontSize: 10, color: Colors.textSecondary, marginTop: 2 },
  divV:        { width: 1, height: 32, backgroundColor: Colors.border },
  csChevron:   { fontSize: 20, color: Colors.textMuted, marginLeft: 4 },
  groupLabel:  { fontSize: 11, fontWeight: '700', color: Colors.textMuted, textTransform: 'uppercase', letterSpacing: 1.2, paddingHorizontal: 16, marginTop: 24, marginBottom: 8 },
  group:       { marginHorizontal: 16, backgroundColor: Colors.bgCard, borderRadius: 16, borderWidth: 1, borderColor: Colors.border, overflow: 'hidden' },
  row:         { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 14 },
  rowLeft:     { flexDirection: 'row', alignItems: 'center', gap: 12, flex: 1 },
  ico:         { width: 36, height: 36, borderRadius: 10, backgroundColor: Colors.bgInput, alignItems: 'center', justifyContent: 'center' },
  icoTxt:      { fontSize: 18 },
  rowLabel:    { fontSize: 15, fontWeight: '600', color: Colors.textPrimary },
  rowSub:      { fontSize: 12, color: Colors.textSecondary, marginTop: 1 },
  rowRight:    { flexDirection: 'row', alignItems: 'center', gap: 6 },
  badge:       { backgroundColor: Colors.blue, borderRadius: 10, paddingHorizontal: 7, paddingVertical: 2 },
  badgeTxt:    { fontSize: 11, fontWeight: '700', color: Colors.white },
  chevron:     { fontSize: 20, color: Colors.textMuted },
  sep:         { height: 1, backgroundColor: Colors.border, marginLeft: 62 },
});
