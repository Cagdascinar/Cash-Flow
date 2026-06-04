import { View, Text, ScrollView, StyleSheet, ActivityIndicator, RefreshControl } from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { C } from '../../constants/Colors';
import { summary as summaryApi, transactions } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';
import { BalanceCard } from '../../components/BalanceCard';
import { TransactionItem, type Tx } from '../../components/TransactionItem';

type Period = 'ay' | 'yil' | 'tum';
const PERIOD_MAP: Record<Period, string> = { ay: 'month', yil: 'year', tum: 'all' };

export default function Dashboard() {
  const { user, activeProfile } = useAuthStore();
  const [sum,        setSum]    = useState<any>(null);
  const [recent,     setRecent] = useState<Tx[]>([]);
  const [period,     setPeriod] = useState<Period>('ay');
  const [loading,    setLoad]   = useState(true);
  const [refreshing, setRef]    = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoad(true);
    try {
      const now = new Date();
      const [s, tx] = await Promise.all([
        summaryApi.get(
          PERIOD_MAP[period],
          now.getFullYear(),
          period === 'ay' ? now.getMonth() + 1 : undefined,
        ),
        transactions.list(),
      ]);
      setSum(s);
      setRecent(Array.isArray(tx) ? (tx as Tx[]).slice(0, 10) : []);
    } catch (e) {
      console.warn('dashboard load error', e);
    } finally { setLoad(false); setRef(false); }
  }, [period]);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <SafeAreaView style={s.container}>
      <View style={s.center}><ActivityIndicator size="large" color={C.blue} /></View>
    </SafeAreaView>
  );

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={C.blue} />}
      >
        {/* Başlık */}
        <View style={s.header}>
          <View>
            <Text style={s.greeting}>Merhaba, {user?.username} 👋</Text>
            <Text style={s.profile}>{activeProfile?.name}</Text>
          </View>
        </View>

        {/* Bakiye kartı */}
        <BalanceCard
          gelir={sum?.gelir ?? 0}
          gider={sum?.gider ?? 0}
          net={sum?.net   ?? 0}
          kullanilabilir={sum?.kullanilabilir_nakit ?? (sum?.net ?? 0)}
          kartBorcu={sum?.kart_borcu ?? 0}
          period={period}
          onPeriod={setPeriod}
        />

        {/* Son işlemler */}
        <View style={s.section}>
          <Text style={s.sectionTitle}>Son İşlemler</Text>
          {recent.length === 0
            ? <View style={s.empty}><Text style={s.emptyIco}>📭</Text><Text style={s.emptyTxt}>Henüz işlem yok</Text></View>
            : <View style={s.list}>
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

const s = StyleSheet.create({
  container:    { flex: 1, backgroundColor: C.bg },
  center:       { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:       { paddingHorizontal: 16, paddingVertical: 16 },
  greeting:     { fontSize: 20, fontWeight: '700', color: C.txt },
  profile:      { fontSize: 13, color: C.txt2, marginTop: 2 },
  section:      { marginTop: 24, paddingHorizontal: 16, paddingBottom: 24 },
  sectionTitle: { fontSize: 12, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 },
  list:         { backgroundColor: C.card, borderRadius: 16, borderWidth: 1, borderColor: C.border, overflow: 'hidden' },
  sep:          { height: 1, backgroundColor: C.border, marginHorizontal: 14 },
  empty:        { alignItems: 'center', paddingVertical: 32 },
  emptyIco:     { fontSize: 40, marginBottom: 8 },
  emptyTxt:     { fontSize: 14, color: C.txt2 },
});
