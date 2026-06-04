import {
  View, Text, ScrollView, StyleSheet,
  TouchableOpacity, Alert, ActivityIndicator,
} from 'react-native';
import { useState, useEffect } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/Colors';
import { api } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

interface MenuItemProps {
  icon: string; label: string; sub?: string;
  onPress: () => void; danger?: boolean;
}

function MenuRow({ icon, label, sub, onPress, danger }: MenuItemProps) {
  return (
    <TouchableOpacity style={s.row} onPress={onPress} activeOpacity={0.7}>
      <View style={s.rowLeft}>
        <View style={[s.iconBox, danger && { backgroundColor: '#2A1018' }]}>
          <Text style={s.rowIcon}>{icon}</Text>
        </View>
        <View>
          <Text style={[s.rowLabel, danger && { color: Colors.red }]}>{label}</Text>
          {sub && <Text style={s.rowSub}>{sub}</Text>}
        </View>
      </View>
      <Text style={s.chevron}>›</Text>
    </TouchableOpacity>
  );
}

export default function MoreScreen() {
  const { user, logout } = useAuthStore();
  const [cards, setCards]   = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.cards.list()
      .then((d: any) => setCards(d.cards ?? d ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleLogout() {
    Alert.alert('Çıkış', 'Oturumu kapatmak istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      {
        text: 'Çıkış Yap', style: 'destructive',
        onPress: async () => { await api.auth.logout(); logout(); },
      },
    ]);
  }

  const totalDebt  = cards.reduce((s, c) => s + (c.used_ ?? 0), 0);
  const totalLimit = cards.reduce((s, c) => s + (c.limit_ ?? 0), 0);
  const fmt = (n: number) =>
    new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 0 }).format(n);

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={s.header}><Text style={s.title}>Daha Fazla</Text></View>

        {/* Profil kartı */}
        <View style={s.profileCard}>
          <View style={s.avatar}>
            <Text style={s.avatarText}>{user?.username?.charAt(0).toUpperCase() ?? '?'}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={s.profileName}>{user?.username}</Text>
            <Text style={s.profileEmail}>{user?.email}</Text>
          </View>
          {user?.is_premium && (
            <View style={s.proBadge}><Text style={s.proText}>PRO</Text></View>
          )}
        </View>

        {/* Kart özeti */}
        {!loading && cards.length > 0 && (
          <View style={s.cardSummary}>
            <View style={s.cardSumItem}>
              <Text style={s.cardSumVal}>{fmt(totalDebt)}</Text>
              <Text style={s.cardSumLabel}>Toplam Borç</Text>
            </View>
            <View style={s.divV} />
            <View style={s.cardSumItem}>
              <Text style={[s.cardSumVal, { color: Colors.green }]}>{fmt(totalLimit - totalDebt)}</Text>
              <Text style={s.cardSumLabel}>Kullanılabilir</Text>
            </View>
            <View style={s.divV} />
            <View style={s.cardSumItem}>
              <Text style={s.cardSumVal}>{cards.length}</Text>
              <Text style={s.cardSumLabel}>Kart</Text>
            </View>
          </View>
        )}

        <Text style={s.groupLabel}>Finans</Text>
        <View style={s.group}>
          <MenuRow icon="💳" label="Kredi Kartları" sub={`${cards.length} kart · ${fmt(totalDebt)} borç`}
            onPress={() => Alert.alert('Yakında', 'Kart detay ekranı yapılıyor')} />
          <View style={s.sep} />
          <MenuRow icon="🏦" label="Hesaplar" sub="Banka hesapları"
            onPress={() => Alert.alert('Yakında', 'Hesap ekranı yapılıyor')} />
          <View style={s.sep} />
          <MenuRow icon="📈" label="Yatırımlar" sub="Portföy takibi"
            onPress={() => Alert.alert('Yakında', 'Yatırım ekranı yapılıyor')} />
          <View style={s.sep} />
          <MenuRow icon="🔄" label="Tekrarlayan İşlemler"
            onPress={() => Alert.alert('Yakında', 'Tekrarlayan işlemler ekranı yapılıyor')} />
        </View>

        <Text style={s.groupLabel}>Kurumsal</Text>
        <View style={s.group}>
          <MenuRow icon="🏢" label="Tedarikçiler"
            onPress={() => Alert.alert('Yakında', 'Tedarikçi ekranı yapılıyor')} />
          <View style={s.sep} />
          <MenuRow icon="🏗️" label="Varlıklar" sub="Demirbaş ve araçlar"
            onPress={() => Alert.alert('Yakında', 'Varlık ekranı yapılıyor')} />
          <View style={s.sep} />
          <MenuRow icon="📄" label="Faturalar"
            onPress={() => Alert.alert('Yakında', 'Fatura ekranı yapılıyor')} />
        </View>

        <Text style={s.groupLabel}>Ayarlar</Text>
        <View style={s.group}>
          <MenuRow icon="🤖" label="Telegram Botu" sub="İşlem girişi için bağla"
            onPress={() => Alert.alert('Yakında', 'Telegram bağlantı ekranı yapılıyor')} />
          <View style={s.sep} />
          <MenuRow icon="📤" label="Dışa Aktar" sub="Excel / PDF"
            onPress={() => Alert.alert('Yakında', 'Dışa aktarım yapılıyor')} />
        </View>

        <View style={s.group}>
          <MenuRow icon="🚪" label="Çıkış Yap" onPress={handleLogout} danger />
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  header: { paddingHorizontal: 16, paddingTop: 8 },
  title: { fontSize: 24, fontWeight: '800', color: Colors.textPrimary },
  profileCard: {
    flexDirection: 'row', alignItems: 'center',
    marginHorizontal: 16, marginTop: 16,
    backgroundColor: Colors.bgCard, borderRadius: 16,
    padding: 16, borderWidth: 1, borderColor: Colors.border, gap: 12,
  },
  avatar: { width: 48, height: 48, borderRadius: 24, backgroundColor: Colors.primary, alignItems: 'center', justifyContent: 'center' },
  avatarText: { fontSize: 20, fontWeight: '700', color: Colors.white },
  profileName: { fontSize: 16, fontWeight: '700', color: Colors.textPrimary },
  profileEmail: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  proBadge: { backgroundColor: Colors.primary, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3 },
  proText: { fontSize: 11, fontWeight: '800', color: Colors.white },
  cardSummary: {
    flexDirection: 'row', marginHorizontal: 16, marginTop: 12,
    backgroundColor: Colors.bgCard, borderRadius: 14,
    borderWidth: 1, borderColor: Colors.border, padding: 16,
  },
  cardSumItem: { flex: 1, alignItems: 'center' },
  cardSumVal: { fontSize: 16, fontWeight: '800', color: Colors.textPrimary },
  cardSumLabel: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  divV: { width: 1, backgroundColor: Colors.border },
  groupLabel: {
    fontSize: 12, fontWeight: '700', color: Colors.textMuted,
    textTransform: 'uppercase', letterSpacing: 1,
    paddingHorizontal: 16, marginTop: 24, marginBottom: 8,
  },
  group: {
    marginHorizontal: 16, backgroundColor: Colors.bgCard,
    borderRadius: 16, borderWidth: 1, borderColor: Colors.border, overflow: 'hidden',
  },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 14 },
  rowLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconBox: { width: 36, height: 36, borderRadius: 10, backgroundColor: Colors.bgInput, alignItems: 'center', justifyContent: 'center' },
  rowIcon: { fontSize: 18 },
  rowLabel: { fontSize: 15, fontWeight: '600', color: Colors.textPrimary },
  rowSub: { fontSize: 12, color: Colors.textSecondary },
  chevron: { fontSize: 20, color: Colors.textMuted },
  sep: { height: 1, backgroundColor: Colors.border, marginLeft: 62 },
});
