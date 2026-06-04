import {
  View, Text, ScrollView, StyleSheet,
  ActivityIndicator, RefreshControl, TouchableOpacity, Alert,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/Colors';
import { goals as goalsApi, summary as summaryApi } from '../../services/api';

function fmt(n: number) {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 0 }).format(n ?? 0);
}

function ProgressBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <View style={p.track}>
      <View style={[p.fill, { width: `${pct}%`, backgroundColor: color }]} />
    </View>
  );
}
const p = StyleSheet.create({
  track: { height: 6, backgroundColor: Colors.bgInput, borderRadius: 3, overflow: 'hidden', marginTop: 8 },
  fill:  { height: '100%', borderRadius: 3 },
});

export default function BudgetScreen() {
  const [goalsList,  setGoals]     = useState<any[]>([]);
  const [sum,        setSum]       = useState<any>(null);
  const [loading,    setLoading]   = useState(true);
  const [refreshing, setRef]       = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const now = new Date();
      const [g, s] = await Promise.all([
        goalsApi.list(),
        summaryApi.get('month', now.getFullYear(), now.getMonth() + 1),
      ]);
      // Backend /api/goals direkt array döndürüyor
      setGoals(Array.isArray(g) ? g : []);
      setSum(s);
    } finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function deleteGoal(id: number) {
    Alert.alert('Hedefi Sil', 'Bu hedefi silmek istediğinize emin misiniz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await goalsApi.delete(id); setGoals(prev => prev.filter(g => g.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  // Bütçe limitleri: { kategori: limit }
  const budgets: Record<string, number> = sum?.budgets ?? {};
  const giderCats: Record<string, number> = sum?.gider_cats ?? {};
  const budgetList = Object.entries(budgets).map(([cat, limit]) => ({
    cat, limit: Number(limit), spent: giderCats[cat] ?? 0,
  }));

  // Bu ayın net tasarrufu
  const netThisMonth = (sum?.gelir ?? 0) - (sum?.gider ?? 0);

  if (loading) return (
    <SafeAreaView style={s.container}>
      <View style={s.center}><ActivityIndicator size="large" color={Colors.blue} /></View>
    </SafeAreaView>
  );

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={Colors.blue} />}
      >
        <View style={s.header}><Text style={s.title}>Bütçe & Hedefler</Text></View>

        {/* Bu ay özet */}
        {sum && (
          <View style={s.monthCard}>
            <View style={s.monthRow}>
              <Text style={s.monthLabel}>Bu Ay Net Tasarruf</Text>
              <Text style={[s.monthVal, { color: netThisMonth >= 0 ? Colors.green : Colors.red }]}>
                {fmt(netThisMonth)}
              </Text>
            </View>
            <ProgressBar
              value={Math.max(netThisMonth, 0)}
              max={sum.gelir || 1}
              color={netThisMonth >= 0 ? Colors.green : Colors.red}
            />
            <Text style={s.monthSub}>Gelirin %{sum.gelir > 0 ? Math.round((netThisMonth / sum.gelir) * 100) : 0}'ını tasarruf ettin</Text>
          </View>
        )}

        {/* Tasarruf hedefleri */}
        <View style={s.sectionHeader}>
          <Text style={s.sectionTitle}>Aylık Tasarruf Hedefleri</Text>
        </View>

        {goalsList.length === 0
          ? <View style={s.emptyCard}>
              <Text style={s.emptyIco}>🎯</Text>
              <Text style={s.emptyTxt}>Henüz hedef eklenmedi</Text>
              <Text style={s.emptySub}>Web uygulamasından hedef ekleyebilirsiniz</Text>
            </View>
          : <View style={s.cardList}>
              {goalsList.map((g: any) => {
                const monthly = g.monthly_target ?? 0;
                const reached = Math.min(Math.max(netThisMonth, 0), monthly);
                const pct = monthly > 0 ? (reached / monthly) * 100 : 0;
                const color = pct >= 100 ? Colors.green : pct >= 50 ? Colors.yellow : Colors.red;
                return (
                  <View key={g.id} style={s.card}>
                    <View style={s.cardRow}>
                      <View style={{ flex: 1 }}>
                        <Text style={s.cardTitle}>{g.name}</Text>
                        {g.note ? <Text style={s.cardNote}>{g.note}</Text> : null}
                      </View>
                      <TouchableOpacity onPress={() => deleteGoal(g.id)} style={s.delBtn}>
                        <Text style={s.delTxt}>✕</Text>
                      </TouchableOpacity>
                    </View>
                    <ProgressBar value={reached} max={monthly} color={color} />
                    <View style={[s.cardRow, { marginTop: 8 }]}>
                      <Text style={s.cardSub}>{fmt(reached)} birikiyor</Text>
                      <Text style={[s.cardSub, { color }]}>Aylık hedef: {fmt(monthly)}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
        }

        {/* Kategori bütçeleri */}
        {budgetList.length > 0 && (
          <>
            <View style={[s.sectionHeader, { marginTop: 24 }]}>
              <Text style={s.sectionTitle}>Kategori Limitleri</Text>
            </View>
            <View style={s.cardList}>
              {budgetList.map((b, i) => {
                const pct = b.limit > 0 ? (b.spent / b.limit) * 100 : 0;
                const color = pct > 100 ? Colors.red : pct > 75 ? Colors.yellow : Colors.green;
                return (
                  <View key={i} style={s.card}>
                    <View style={s.cardRow}>
                      <Text style={s.cardTitle}>{b.cat}</Text>
                      <Text style={[s.cardSub, { color, fontWeight: '700' }]}>
                        {fmt(b.spent)} / {fmt(b.limit)}
                      </Text>
                    </View>
                    <ProgressBar value={b.spent} max={b.limit} color={color} />
                    {pct > 100 && (
                      <Text style={s.overBudget}>⚠️ Limit {fmt(b.spent - b.limit)} aşıldı</Text>
                    )}
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
  container:   { flex: 1, backgroundColor: Colors.bg },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:      { paddingHorizontal: 16, paddingTop: 8 },
  title:       { fontSize: 24, fontWeight: '800', color: Colors.textPrimary },
  monthCard:   { margin: 16, backgroundColor: Colors.bgCard, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: Colors.border },
  monthRow:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  monthLabel:  { fontSize: 13, color: Colors.textSecondary, fontWeight: '600' },
  monthVal:    { fontSize: 18, fontWeight: '800' },
  monthSub:    { fontSize: 12, color: Colors.textMuted, marginTop: 8 },
  sectionHeader: { paddingHorizontal: 16, marginTop: 8, marginBottom: 10 },
  sectionTitle:{ fontSize: 12, fontWeight: '700', color: Colors.textMuted, textTransform: 'uppercase', letterSpacing: 1 },
  cardList:    { paddingHorizontal: 16, gap: 10 },
  card:        { backgroundColor: Colors.bgCard, borderRadius: 14, padding: 16, borderWidth: 1, borderColor: Colors.border },
  cardRow:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  cardTitle:   { fontSize: 15, fontWeight: '600', color: Colors.textPrimary },
  cardNote:    { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  cardSub:     { fontSize: 12, color: Colors.textSecondary },
  delBtn:      { padding: 4 },
  delTxt:      { fontSize: 14, color: Colors.textMuted },
  overBudget:  { fontSize: 12, color: Colors.red, marginTop: 6 },
  emptyCard:   { marginHorizontal: 16, backgroundColor: Colors.bgCard, borderRadius: 14, padding: 32, alignItems: 'center', borderWidth: 1, borderColor: Colors.border },
  emptyIco:    { fontSize: 36, marginBottom: 8 },
  emptyTxt:    { fontSize: 15, fontWeight: '600', color: Colors.textPrimary },
  emptySub:    { fontSize: 13, color: Colors.textSecondary, marginTop: 4, textAlign: 'center' },
});
