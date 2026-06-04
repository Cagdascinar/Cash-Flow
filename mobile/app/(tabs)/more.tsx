import {
  View, Text, ScrollView, StyleSheet,
  TouchableOpacity, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/Colors';
import { api } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

interface MenuItem {
  icon: string;
  label: string;
  sub?: string;
  onPress: () => void;
  danger?: boolean;
}

function MenuRow({ icon, label, sub, onPress, danger }: MenuItem) {
  return (
    <TouchableOpacity style={styles.row} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.rowLeft}>
        <View style={[styles.iconBox, danger && { backgroundColor: '#2A1018' }]}>
          <Text style={styles.rowIcon}>{icon}</Text>
        </View>
        <View style={styles.rowText}>
          <Text style={[styles.rowLabel, danger && { color: Colors.red }]}>{label}</Text>
          {sub && <Text style={styles.rowSub}>{sub}</Text>}
        </View>
      </View>
      <Text style={styles.chevron}>›</Text>
    </TouchableOpacity>
  );
}

export default function MoreScreen() {
  const { user, activeProfile, logout } = useAuthStore();
  const router = useRouter();

  async function handleLogout() {
    Alert.alert('Çıkış', 'Oturumu kapatmak istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      {
        text: 'Çıkış Yap',
        style: 'destructive',
        onPress: async () => {
          try { await api.auth.logout(); } catch {}
          logout();
        },
      },
    ]);
  }

  const isPremium = user?.is_premium;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>Daha Fazla</Text>
        </View>

        {/* Profile Card */}
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {user?.username?.charAt(0).toUpperCase() ?? '?'}
            </Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>{user?.username}</Text>
            <Text style={styles.profileEmail}>{user?.email}</Text>
          </View>
          {isPremium && (
            <View style={styles.premiumBadge}>
              <Text style={styles.premiumText}>PRO</Text>
            </View>
          )}
        </View>

        {/* Menu Groups */}
        <Text style={styles.groupLabel}>Finans</Text>
        <View style={styles.group}>
          <MenuRow
            icon="💳" label="Kredi Kartları"
            sub="Limit ve borç takibi"
            onPress={() => {}}
          />
          <View style={styles.divider} />
          <MenuRow
            icon="🏦" label="Hesaplar"
            sub="Banka hesapları"
            onPress={() => {}}
          />
          <View style={styles.divider} />
          <MenuRow
            icon="📈" label="Yatırımlar"
            sub="Portföy takibi"
            onPress={() => {}}
          />
          <View style={styles.divider} />
          <MenuRow
            icon="🔄" label="Tekrarlayan İşlemler"
            onPress={() => {}}
          />
        </View>

        <Text style={styles.groupLabel}>Kurumsal</Text>
        <View style={styles.group}>
          <MenuRow
            icon="🏢" label="Tedarikçiler"
            onPress={() => {}}
          />
          <View style={styles.divider} />
          <MenuRow
            icon="🏗️" label="Varlıklar"
            sub="Demirbaş ve araçlar"
            onPress={() => {}}
          />
          <View style={styles.divider} />
          <MenuRow
            icon="📄" label="Faturalar"
            onPress={() => {}}
          />
        </View>

        <Text style={styles.groupLabel}>Ayarlar</Text>
        <View style={styles.group}>
          <MenuRow
            icon="👤" label="Profil Yönetimi"
            sub={`${user?.profiles?.length ?? 0} profil`}
            onPress={() => {}}
          />
          <View style={styles.divider} />
          <MenuRow
            icon="🤖" label="Telegram Botu"
            sub="İşlem girişi için bağla"
            onPress={() => {}}
          />
          <View style={styles.divider} />
          <MenuRow
            icon="📤" label="Dışa Aktar"
            sub="Excel / PDF"
            onPress={() => {}}
          />
        </View>

        <View style={styles.group}>
          <MenuRow
            icon="🚪" label="Çıkış Yap"
            onPress={handleLogout}
            danger
          />
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  header: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 4 },
  title: { fontSize: 24, fontWeight: '800', color: Colors.textPrimary },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 16,
    backgroundColor: Colors.bgCard,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    gap: 12,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { fontSize: 20, fontWeight: '700', color: Colors.white },
  profileInfo: { flex: 1 },
  profileName: { fontSize: 16, fontWeight: '700', color: Colors.textPrimary },
  profileEmail: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  premiumBadge: {
    backgroundColor: Colors.primary,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  premiumText: { fontSize: 11, fontWeight: '800', color: Colors.white },
  groupLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
    paddingHorizontal: 16,
    marginTop: 24,
    marginBottom: 8,
  },
  group: {
    marginHorizontal: 16,
    backgroundColor: Colors.bgCard,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  rowLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: Colors.bgInput,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rowIcon: { fontSize: 18 },
  rowText: { gap: 1 },
  rowLabel: { fontSize: 15, fontWeight: '600', color: Colors.textPrimary },
  rowSub: { fontSize: 12, color: Colors.textSecondary },
  chevron: { fontSize: 20, color: Colors.textMuted },
  divider: { height: 1, backgroundColor: Colors.border, marginLeft: 62 },
});
