import { View, Text, ScrollView, StyleSheet, ActivityIndicator, RefreshControl, TouchableOpacity, Alert } from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { C, money } from '../../constants/Colors';
import { goals as goalsApi, summary as summaryApi, budgets as budgetsApi } from '../../services/api';
import { useRouter } from 'expo-router';

function Bar({ v, max, color }: { v: number; max: number; color: string }) {
  return (
    <View style={b.track}>
      <View style={[b.fill, { width: `${Math.min(max > 0 ? (v/max)*100 : 0, 100)}%`, backgroundColor: color }]} />
    </View>
  );
}
const b = StyleSheet.create({
  track: { height: 6, backgroundColor: C.input, borderRadius: 3, overflow: 'hidden', marginTop: 8 },
  fill:  { height: '100%', borderRadius: 3 },
});

export default function BudgetScreen() {
  const router = useRouter();
  const [goals,  setGoals]  = useState<any[]>([]);
  const [sum,    setSum]    = useState<any>(null);
  const [loading, setLoad]  = useState(true);
  const [ref,    setRef]    = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoad(true);
    try {
      const now = new Date();
      const [g, s] = await Promise.all([
        goalsApi.list(),
        summaryApi.get('month', now.getFullYear(), now.getMonth() + 1),
      ]);
      setGoals(Array.isArray(g) ? g : []);
      setSum(s);
    } catch {} finally { setLoad(false); setRef(false); }
  }, []);

  async function delGoal(id: number, name: string) {
    Alert.alert('Hedefi Sil', `"${name}" hedefini silmek istiyor musunuz?`, [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await goalsApi.delete(id); setGoals(p => p.filter(g => g.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  useEffect(() => { load(); }, [load]);

  const budgets: Record<string, number> = sum?.budgets ?? {};
  const giderCats: Record<string, number> = sum?.gider_cats ?? {};
  const net = (sum?.gelir ?? 0) - (sum?.gider ?? 0);

  if (loading) return (
    <SafeAreaView style={s.container}>
      <View style={s.center}><ActivityIndicator size="large" color={C.blue} /></View>
    </SafeAreaView>
  );

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>

        <View style={s.header}>
          <Text style={s.title}>Bütçe & Hedefler</Text>
          <View style={{ flexDirection: 'row', gap: 8 }}>
            <TouchableOpacity style={s.hBtn} onPress={() => router.push('/add-goal' as any)}>
              <Text style={s.hBtnTxt}>+ Hedef</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[s.hBtn, { backgroundColor: C.card }]} onPress={() => router.push('/set-budget' as any)}>
              <Text style={[s.hBtnTxt, { color: C.txt }]}>⚙️ Limit</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Bu ay özeti */}
        {sum && (
          <View style={s.monthCard}>
            <View style={s.row}>
              <Text style={s.monthLbl}>Bu Ay Net Tasarruf</Text>
              <Text style={[s.monthVal, { color: net >= 0 ? C.green : C.red }]}>{money(net)}</Text>
            </View>
            <Bar v={Math.max(net, 0)} max={sum.gelir || 1} color={net >= 0 ? C.green : C.red} />
            <Text style={s.monthSub}>
              Gelirinizin %{sum.gelir > 0 ? Math.round((Math.max(net, 0) / sum.gelir) * 100) : 0}'ini tasarruf ettiniz
            </Text>
          </View>
        )}

        {/* Hedefler */}
        <Text style={s.sectLbl}>Aylık Hedefler</Text>
        {goals.length === 0
          ? <View style={s.emptyCard}><Text style={s.emptyIco}>🎯</Text><Text style={s.emptyTxt}>Hedef eklenmedi</Text><Text style={s.emptySub}>Web'den ekleyebilirsiniz</Text></View>
          : <View style={s.cards}>
              {goals.map((g: any) => {
                const target = g.monthly_target ?? 0;
                const reached = Math.min(Math.max(net, 0), target);
                const pct = target > 0 ? (reached / target) * 100 : 0;
                const color = pct >= 100 ? C.green : pct >= 50 ? C.yellow : C.red;
                return (
                  <View key={g.id} style={s.card}>
                    <View style={s.row}>
                      <Text style={[s.cardTit, { flex: 1 }]}>{g.name}</Text>
                      <Text style={[s.pct, { color }]}>%{Math.round(pct)}</Text>
                      <TouchableOpacity onPress={() => delGoal(g.id, g.name)} style={{ paddingLeft: 10 }}>
                        <Text style={{ color: C.muted, fontSize: 16 }}>✕</Text>
                      </TouchableOpacity>
                    </View>
                    <Bar v={reached} max={target} color={color} />
                    <View style={[s.row, { marginTop: 6 }]}>
                      <Text style={s.cardSub}>{money(reached)} / aylık {money(target)}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
        }

        {/* Bütçe limitleri */}
        {Object.keys(budgets).length > 0 && (
          <>
            <Text style={[s.sectLbl, { marginTop: 24 }]}>Kategori Limitleri</Text>
            <View style={s.cards}>
              {Object.entries(budgets).map(([cat, lim], i) => {
                const limit = Number(lim);
                const spent = giderCats[cat] ?? 0;
                const pct   = limit > 0 ? (spent / limit) * 100 : 0;
                const color = pct > 100 ? C.red : pct > 75 ? C.yellow : C.green;
                return (
                  <View key={i} style={s.card}>
                    <View style={s.row}>
                      <Text style={s.cardTit}>{cat}</Text>
                      <Text style={[s.pct, { color }]}>{money(spent)} / {money(limit)}</Text>
                    </View>
                    <Bar v={spent} max={limit} color={color} />
                    {pct > 100 && <Text style={s.over}>⚠️ {money(spent - limit)} aşıldı</Text>}
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
  container: { flex: 1, backgroundColor: C.bg },
  center:    { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8 },
  title:     { fontSize: 22, fontWeight: '800', color: C.txt },
  hBtn:      { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 7 },
  hBtnTxt:   { fontSize: 13, fontWeight: '700', color: C.white },
  monthCard: { margin: 16, backgroundColor: C.card, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: C.border },
  row:       { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  monthLbl:  { fontSize: 13, color: C.txt2, fontWeight: '600' },
  monthVal:  { fontSize: 18, fontWeight: '800' },
  monthSub:  { fontSize: 12, color: C.muted, marginTop: 8 },
  sectLbl:   { fontSize: 11, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 1, paddingHorizontal: 16, marginTop: 20, marginBottom: 10 },
  cards:     { paddingHorizontal: 16, gap: 10 },
  card:      { backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  cardTit:   { fontSize: 14, fontWeight: '600', color: C.txt },
  cardSub:   { fontSize: 12, color: C.txt2 },
  pct:       { fontSize: 13, fontWeight: '700' },
  over:      { fontSize: 12, color: C.red, marginTop: 6 },
  emptyCard: { marginHorizontal: 16, backgroundColor: C.card, borderRadius: 14, padding: 32, alignItems: 'center', borderWidth: 1, borderColor: C.border },
  emptyIco:  { fontSize: 36, marginBottom: 8 },
  emptyTxt:  { fontSize: 15, fontWeight: '600', color: C.txt },
  emptySub:  { fontSize: 13, color: C.txt2, marginTop: 4 },
});
