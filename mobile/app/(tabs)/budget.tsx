import {
  View, Text, ScrollView, StyleSheet,
  ActivityIndicator, RefreshControl,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/Colors';
import { api } from '../../services/api';

function fmt(n: number) {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 0 }).format(n);
}

function ProgressBar({ pct, color }: { pct: number; color: string }) {
  return (
    <View style={bar.track}>
      <View style={[bar.fill, { width: `${Math.min(Math.max(pct, 0), 100)}%`, backgroundColor: color }]} />
    </View>
  );
}
const bar = StyleSheet.create({
  track: { height: 6, backgroundColor: Colors.bgInput, borderRadius: 3, overflow: 'hidden', marginTop: 8 },
  fill:  { height: '100%', borderRadius: 3 },
});

export default function BudgetScreen() {
  const [goals,    setGoals]    = useState<any[]>([]);
  const [summary,  setSummary]  = useState<any>(null);
  const [loading,  setLoading]  = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true); else setLoading(true);
    try {
      const now = new Date();
      const [goalsData, sumData] = await Promise.all([
        api.goals.list(),
        api.summary(now.getFullYear(), now.getMonth() + 1, 'month'),
      ]);
      setGoals((goalsData as any).goals ?? []);
      setSummary(sumData);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const budgets: Record<string, number> = summary?.budgets ?? {};
  const giderCats: Record<string, number> = summary?.gider_cats ?? {};
  const budgetList = Object.entries(budgets).map(([cat, limit]) => ({
    cat, limit, spent: giderCats[cat] ?? 0,
  }));

  if (loading) {
    return <SafeAreaView style={s.container}><View style={s.center}><ActivityIndicator size="large" color={Colors.primary} /></View></SafeAreaView>;
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={Colors.primary} />}
      >
        <View style={s.header}><Text style={s.title}>Bütçe & Hedefler</Text></View>

        {/* Hedefler */}
        <Text style={s.sectionTitle}>Tasarruf Hedefleri</Text>
        {goals.length === 0 ? (
          <View style={s.emptyCard}>
            <Text style={s.emptyIcon}>🎯</Text>
            <Text style={s.emptyText}>Henüz hedef eklenmedi</Text>
          </View>
        ) : (
          <View style={s.cardList}>
            {goals.map((g: any) => {
              const pct = g.target_amount > 0 ? (g.current_amount / g.target_amount) * 100 : 0;
              return (
                <View key={g.id} style={s.card}>
                  <View style={s.row}>
                    <Text style={s.cardTitle}>{g.name}</Text>
                    <Text style={[s.pct, { color: pct >= 100 ? Colors.green : Colors.primary }]}>{Math.round(pct)}%</Text>
                  </View>
                  <ProgressBar pct={pct} color={pct >= 100 ? Colors.green : Colors.primary} />
                  <View style={[s.row, { marginTop: 8 }]}>
                    <Text style={s.sub}>{fmt(g.current_amount)}</Text>
                    <Text style={s.sub}>Hedef: {fmt(g.target_amount)}</Text>
                  </View>
                </View>
              );
            })}
          </View>
        )}

        {/* Kategori limitleri */}
        {budgetList.length > 0 && (
          <>
            <Text style={[s.sectionTitle, { marginTop: 24 }]}>Kategori Limitleri</Text>
            <View style={s.cardList}>
              {budgetList.map((b, i) => {
                const pct = b.limit > 0 ? (b.spent / b.limit) * 100 : 0;
                const color = pct > 100 ? Colors.red : pct > 75 ? Colors.yellow : Colors.green;
                return (
                  <View key={i} style={s.card}>
                    <View style={s.row}>
                      <Text style={s.cardTitle}>{b.cat}</Text>
                      <Text style={[s.pct, { color }]}>{fmt(b.spent)} / {fmt(b.limit)}</Text>
                    </View>
                    <ProgressBar pct={pct} color={color} />
                  </View>
                );
              })}
            </View>
          </>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header: { paddingHorizontal: 16, paddingTop: 8 },
  title: { fontSize: 24, fontWeight: '800', color: Colors.textPrimary },
  sectionTitle: {
    fontSize: 12, fontWeight: '700', color: Colors.textMuted,
    textTransform: 'uppercase', letterSpacing: 1,
    paddingHorizontal: 16, marginTop: 20, marginBottom: 10,
  },
  cardList: { paddingHorizontal: 16, gap: 10 },
  card: { backgroundColor: Colors.bgCard, borderRadius: 14, padding: 16, borderWidth: 1, borderColor: Colors.border },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 15, fontWeight: '600', color: Colors.textPrimary },
  sub: { fontSize: 12, color: Colors.textSecondary },
  pct: { fontSize: 13, fontWeight: '700' },
  emptyCard: {
    marginHorizontal: 16, backgroundColor: Colors.bgCard,
    borderRadius: 14, padding: 32, alignItems: 'center',
    borderWidth: 1, borderColor: Colors.border,
  },
  emptyIcon: { fontSize: 36, marginBottom: 8 },
  emptyText: { fontSize: 14, color: Colors.textSecondary },
});
