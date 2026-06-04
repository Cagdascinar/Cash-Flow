import {
  View, Text, ScrollView, StyleSheet,
  TouchableOpacity, ActivityIndicator, RefreshControl,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/Colors';
import { api } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

interface Goal {
  id: number;
  name: string;
  target_amount: number;
  current_amount: number;
  deadline?: string;
}

function ProgressBar({ pct, color }: { pct: number; color: string }) {
  const clamped = Math.min(Math.max(pct, 0), 100);
  return (
    <View style={bar.track}>
      <View style={[bar.fill, { width: `${clamped}%`, backgroundColor: color }]} />
    </View>
  );
}

const bar = StyleSheet.create({
  track: {
    height: 6,
    backgroundColor: '#2A2A38',
    borderRadius: 3,
    overflow: 'hidden',
    marginTop: 8,
  },
  fill: { height: '100%', borderRadius: 3 },
});

function fmt(n: number) {
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: 'TRY',
    minimumFractionDigits: 0,
  }).format(n);
}

export default function BudgetScreen() {
  const { activeProfile } = useAuthStore();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (showRefresh = false) => {
    if (!activeProfile) return;
    if (showRefresh) setRefreshing(true); else setLoading(true);
    try {
      const now = new Date();
      const [goalsData, sumData] = await Promise.all([
        api.goals.list(activeProfile.id),
        api.summary(activeProfile.id, now.getFullYear(), now.getMonth() + 1),
      ]);
      setGoals((goalsData as any).goals ?? []);
      setSummary(sumData);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [activeProfile]);

  useEffect(() => { load(); }, [load]);

  const budgets: Array<{ cat: string; spent: number; limit: number }> =
    summary?.budgets ?? [];

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.primary} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={Colors.primary} />
        }
      >
        <View style={styles.header}>
          <Text style={styles.title}>Bütçe & Hedefler</Text>
        </View>

        {/* Goals */}
        <Text style={styles.sectionTitle}>Tasarruf Hedefleri</Text>
        {goals.length === 0 ? (
          <View style={styles.emptyCard}>
            <Text style={styles.emptyIcon}>🎯</Text>
            <Text style={styles.emptyText}>Henüz hedef eklenmedi</Text>
          </View>
        ) : (
          <View style={styles.cardList}>
            {goals.map((g) => {
              const pct = g.target_amount > 0
                ? (g.current_amount / g.target_amount) * 100
                : 0;
              return (
                <View key={g.id} style={styles.card}>
                  <View style={styles.cardRow}>
                    <Text style={styles.cardTitle}>{g.name}</Text>
                    <Text style={styles.pct}>{Math.round(pct)}%</Text>
                  </View>
                  <ProgressBar pct={pct} color={pct >= 100 ? Colors.green : Colors.primary} />
                  <View style={[styles.cardRow, { marginTop: 8 }]}>
                    <Text style={styles.cardSub}>{fmt(g.current_amount)} birikiyor</Text>
                    <Text style={styles.cardSub}>Hedef: {fmt(g.target_amount)}</Text>
                  </View>
                </View>
              );
            })}
          </View>
        )}

        {/* Category Budgets */}
        {budgets.length > 0 && (
          <>
            <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Kategori Limitleri</Text>
            <View style={styles.cardList}>
              {budgets.map((b, i) => {
                const pct = b.limit > 0 ? (b.spent / b.limit) * 100 : 0;
                const over = pct > 100;
                return (
                  <View key={i} style={styles.card}>
                    <View style={styles.cardRow}>
                      <Text style={styles.cardTitle}>{b.cat}</Text>
                      <Text style={[styles.pct, over && { color: Colors.red }]}>
                        {fmt(b.spent)} / {fmt(b.limit)}
                      </Text>
                    </View>
                    <ProgressBar
                      pct={pct}
                      color={over ? Colors.red : pct > 75 ? Colors.yellow : Colors.green}
                    />
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

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 4 },
  title: { fontSize: 24, fontWeight: '800', color: Colors.textPrimary },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    paddingHorizontal: 16,
    marginTop: 20,
    marginBottom: 10,
  },
  cardList: { paddingHorizontal: 16, gap: 10 },
  card: {
    backgroundColor: Colors.bgCard,
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  cardRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { fontSize: 15, fontWeight: '600', color: Colors.textPrimary },
  cardSub: { fontSize: 12, color: Colors.textSecondary },
  pct: { fontSize: 13, fontWeight: '700', color: Colors.primary },
  emptyCard: {
    marginHorizontal: 16,
    backgroundColor: Colors.bgCard,
    borderRadius: 14,
    padding: 32,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  emptyIcon: { fontSize: 36, marginBottom: 8 },
  emptyText: { fontSize: 14, color: Colors.textSecondary },
});
