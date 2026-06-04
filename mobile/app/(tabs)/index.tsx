import {
  View, Text, ScrollView, StyleSheet,
  ActivityIndicator, TouchableOpacity, RefreshControl,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/Colors';
import { api } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';
import { BalanceCard } from '../../components/BalanceCard';
import { TransactionItem } from '../../components/TransactionItem';

type Period = 'ay' | 'yil' | 'tum';
const PERIOD_LABELS: Record<Period, string> = { ay: 'Bu Ay', yil: 'Bu Yıl', tum: 'Tümü' };
const PERIODS: Period[] = ['ay', 'yil', 'tum'];

export default function DashboardScreen() {
  const { user, activeProfile } = useAuthStore();
  const [summary, setSummary] = useState<any>(null);
  const [recent, setRecent] = useState<any[]>([]);
  const [period, setPeriod] = useState<Period>('ay');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (showRefresh = false) => {
    if (!activeProfile) return;
    if (showRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const now = new Date();
      const params: Record<string, string> = {};
      if (period === 'ay') {
        params.year = String(now.getFullYear());
        params.month = String(now.getMonth() + 1);
      } else if (period === 'yil') {
        params.year = String(now.getFullYear());
      }

      const [sumData, txData] = await Promise.all([
        api.summary(activeProfile.id, params.year ? Number(params.year) : undefined, params.month ? Number(params.month) : undefined),
        api.transactions.list(activeProfile.id, { limit: '10', ...params }),
      ]);
      setSummary(sumData);
      setRecent((txData as any).transactions ?? []);
    } catch {
      // silent fail — show cached data
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeProfile, period]);

  useEffect(() => { load(); }, [load]);

  function cyclePeriod() {
    const idx = PERIODS.indexOf(period);
    setPeriod(PERIODS[(idx + 1) % PERIODS.length]);
  }

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  const income = summary?.income ?? 0;
  const expense = summary?.expense ?? 0;
  const balance = income - expense;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => load(true)}
            tintColor={Colors.primary}
          />
        }
      >
        {/* Header */}
        <View style={styles.topBar}>
          <View>
            <Text style={styles.greeting}>Merhaba, {user?.username} 👋</Text>
            <Text style={styles.profileName}>{activeProfile?.name}</Text>
          </View>
        </View>

        {/* Balance Card */}
        <BalanceCard
          balance={balance}
          income={income}
          expense={expense}
          period={PERIOD_LABELS[period]}
          onPeriodChange={cyclePeriod}
        />

        {/* Quick Stats */}
        {summary && (
          <View style={styles.statsRow}>
            <StatCard
              label="Tasarruf Oranı"
              value={income > 0 ? `%${Math.round(((income - expense) / income) * 100)}` : '—'}
              color={balance >= 0 ? Colors.green : Colors.red}
            />
            <StatCard
              label="İşlem Sayısı"
              value={String(summary.transaction_count ?? 0)}
              color={Colors.primary}
            />
            <StatCard
              label="Günlük Ort."
              value={fmtShort(expense / 30)}
              color={Colors.yellow}
            />
          </View>
        )}

        {/* Recent Transactions */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Son İşlemler</Text>
          </View>

          {recent.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyIcon}>📭</Text>
              <Text style={styles.emptyText}>Henüz işlem yok</Text>
            </View>
          ) : (
            <View style={styles.txList}>
              {recent.map((tx) => (
                <TransactionItem key={tx.id} item={tx} />
              ))}
            </View>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <View style={statStyles.card}>
      <Text style={[statStyles.value, { color }]}>{value}</Text>
      <Text style={statStyles.label}>{label}</Text>
    </View>
  );
}

function fmtShort(n: number) {
  if (isNaN(n) || !isFinite(n)) return '—';
  if (n >= 1000) return `₺${(n / 1000).toFixed(1)}B`;
  return `₺${Math.round(n)}`;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  greeting: { fontSize: 20, fontWeight: '700', color: Colors.textPrimary },
  profileName: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  statsRow: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginTop: 12,
    gap: 8,
  },
  section: { marginTop: 24, paddingBottom: 24 },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    marginBottom: 8,
  },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: Colors.textPrimary },
  txList: {
    backgroundColor: Colors.bgCard,
    marginHorizontal: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: Colors.border,
    overflow: 'hidden',
  },
  empty: { alignItems: 'center', paddingVertical: 32 },
  emptyIcon: { fontSize: 40, marginBottom: 8 },
  emptyText: { fontSize: 14, color: Colors.textSecondary },
});

const statStyles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: Colors.bgCard,
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    gap: 4,
  },
  value: { fontSize: 18, fontWeight: '800' },
  label: { fontSize: 11, color: Colors.textSecondary, textAlign: 'center' },
});
