import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  TouchableOpacity, RefreshControl,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/Colors';
import { summary as summaryApi, transactions } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';
import { BalanceCard } from '../../components/BalanceCard';
import { TransactionItem } from '../../components/TransactionItem';

type Period = 'month' | 'year' | 'all';
const PERIOD_LABELS: Record<Period, string> = { month: 'Bu Ay', year: 'Bu Yıl', all: 'Tümü' };
const PERIODS: Period[] = ['month', 'year', 'all'];

function fmt(n: number) {
  if (!n || isNaN(n)) return '—';
  if (Math.abs(n) >= 1e6) return `₺${(n/1e6).toFixed(1)}M`;
  if (Math.abs(n) >= 1e3) return `₺${(n/1e3).toFixed(1)}B`;
  return `₺${Math.round(n)}`;
}

export default function DashboardScreen() {
  const { user, activeProfile } = useAuthStore();
  const [sum,      setSum]      = useState<any>(null);
  const [recent,   setRecent]   = useState<any[]>([]);
  const [period,   setPeriod]   = useState<Period>('month');
  const [loading,  setLoading]  = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRefreshing(true); else setLoading(true);
    try {
      const now = new Date();
      const [s, tx] = await Promise.all([
        summaryApi.get(period, now.getFullYear(), period === 'month' ? now.getMonth()+1 : undefined),
        transactions.list(),
      ]);
      setSum(s);
      setRecent(Array.isArray(tx) ? tx.slice(0, 10) : []);
    } catch {}
    finally { setLoading(false); setRefreshing(false); }
  }, [period]);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <SafeAreaView style={s.container}>
      <View style={s.center}><ActivityIndicator size="large" color={Colors.blue} /></View>
    </SafeAreaView>
  );

  const gelir  = sum?.gelir ?? 0;
  const gider  = sum?.gider ?? 0;
  const net    = sum?.net   ?? (gelir - gider);

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={Colors.blue} />}
      >
        {/* Başlık */}
        <View style={s.topBar}>
          <View>
            <Text style={s.greeting}>Merhaba, {user?.username} 👋</Text>
            <Text style={s.profileName}>{activeProfile?.name}</Text>
          </View>
        </View>

        {/* Bakiye kartı */}
        <BalanceCard
          balance={net} income={gelir} expense={gider}
          period={PERIOD_LABELS[period]}
          onPeriodChange={() => {
            const i = PERIODS.indexOf(period);
            setPeriod(PERIODS[(i+1) % PERIODS.length]);
          }}
        />

        {/* İstatistik kutuları */}
        {sum && (
          <View style={s.statsRow}>
            <StatBox label="Kullanılabilir" value={fmt(sum.kullanilabilir_nakit ?? net)} color={net >= 0 ? Colors.green : Colors.red} />
            <StatBox label="Kart Borcu"     value={fmt(sum.kart_borcu ?? 0)}            color={Colors.yellow} />
            <StatBox label="Asgari Ödeme"   value={fmt(sum.asgari_odeme ?? 0)}          color={Colors.red} />
          </View>
        )}

        {/* Son işlemler */}
        <View style={s.section}>
          <Text style={s.sectionTitle}>Son İşlemler</Text>
          {recent.length === 0
            ? <View style={s.empty}><Text style={s.emptyIcon}>📭</Text><Text style={s.emptyTxt}>Henüz işlem yok</Text></View>
            : <View style={s.txList}>
                {recent.map((tx, i) => (
                  <View key={tx.id}>
                    <TransactionItem item={tx} />
                    {i < recent.length - 1 && <View style={s.sep} />}
                  </View>
                ))}
              </View>
          }
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function StatBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <View style={st.box}>
      <Text style={[st.val, { color }]}>{value}</Text>
      <Text style={st.lbl}>{label}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: Colors.bg },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center' },
  topBar:      { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 16 },
  greeting:    { fontSize: 20, fontWeight: '700', color: Colors.textPrimary },
  profileName: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },
  statsRow:    { flexDirection: 'row', marginHorizontal: 16, marginTop: 12, gap: 8 },
  section:     { marginTop: 24, paddingBottom: 24, paddingHorizontal: 16 },
  sectionTitle:{ fontSize: 14, fontWeight: '700', color: Colors.textSecondary, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 },
  txList:      { backgroundColor: Colors.bgCard, borderRadius: 16, borderWidth: 1, borderColor: Colors.border, overflow: 'hidden' },
  sep:         { height: 1, backgroundColor: Colors.border, marginHorizontal: 14 },
  empty:       { alignItems: 'center', paddingVertical: 32 },
  emptyIcon:   { fontSize: 40, marginBottom: 8 },
  emptyTxt:    { fontSize: 14, color: Colors.textSecondary },
});
const st = StyleSheet.create({
  box: { flex: 1, backgroundColor: Colors.bgCard, borderRadius: 14, padding: 12, borderWidth: 1, borderColor: Colors.border, alignItems: 'center', gap: 3 },
  val: { fontSize: 15, fontWeight: '800' },
  lbl: { fontSize: 10, color: Colors.textSecondary, textAlign: 'center' },
});
