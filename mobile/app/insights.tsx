import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator, RefreshControl, TouchableOpacity,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { misc } from '../services/api';

const TYPE_COLOR: Record<string, string> = {
  warning: '#f0b90b',
  success: C.green,
  info:    C.blue,
  danger:  C.red,
};

const TYPE_ICO: Record<string, string> = {
  warning: '⚠️',
  success: '✅',
  info:    '💡',
  danger:  '🚨',
};

export default function InsightsScreen() {
  const router = useRouter();
  const [data,    setData]    = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setData(await misc.insights()); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const insights: any[] = data?.insights ?? [];
  const categories: any[] = data?.category_breakdown ?? [];
  const topCats = [...categories].sort((a, b) => b.total - a.total).slice(0, 5);

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>AI Analiz</Text>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>

            {insights.length === 0
              ? <View style={s.empty}>
                  <Text style={s.emptyIco}>🤖</Text>
                  <Text style={s.emptyTxt}>Henüz analiz yok</Text>
                  <Text style={s.emptySub}>Birkaç işlem ekledikten sonra AI analizler görünür</Text>
                </View>
              : <>
                  <Text style={s.sectLbl}>Öneriler & Uyarılar</Text>
                  {insights.map((item: any, i: number) => {
                    const type = item.type ?? 'info';
                    const color = TYPE_COLOR[type] ?? C.blue;
                    return (
                      <View key={i} style={[s.card, { borderLeftColor: color, borderLeftWidth: 4 }]}>
                        <View style={s.cardTop}>
                          <Text style={s.cardIco}>{TYPE_ICO[type] ?? '💡'}</Text>
                          <Text style={[s.cardTitle, { color }]}>{item.title}</Text>
                        </View>
                        <Text style={s.cardMsg}>{item.message}</Text>
                      </View>
                    );
                  })}
                </>
            }

            {topCats.length > 0 && (
              <>
                <Text style={[s.sectLbl, { marginTop: 24 }]}>En Çok Harcanan Kategoriler</Text>
                <View style={s.catGroup}>
                  {topCats.map((cat: any, i: number) => (
                    <View key={i}>
                      {i > 0 && <View style={s.sep} />}
                      <View style={s.catRow}>
                        <View style={{ flex: 1 }}>
                          <Text style={s.catName}>{cat.category}</Text>
                          <View style={s.barTrack}>
                            <View style={[s.barFill, {
                              width: `${Math.min((cat.total / (topCats[0]?.total || 1)) * 100, 100)}%`,
                              backgroundColor: i === 0 ? C.red : C.blue,
                            }]} />
                          </View>
                        </View>
                        <Text style={[s.catAmt, { color: C.red }]}>{money(cat.total)}</Text>
                      </View>
                    </View>
                  ))}
                </View>
              </>
            )}

            {data?.monthly_trend && (
              <>
                <Text style={[s.sectLbl, { marginTop: 24 }]}>Aylık Trend</Text>
                <View style={s.trendCard}>
                  {(data.monthly_trend as any[]).slice(-4).map((m: any, i: number) => (
                    <View key={i} style={s.trendItem}>
                      <Text style={s.trendMonth}>{m.month ?? m.label ?? ''}</Text>
                      <Text style={[s.trendGelir, { color: C.green }]}>+{money(m.gelir ?? 0)}</Text>
                      <Text style={[s.trendGider, { color: C.red }]}>-{money(m.gider ?? 0)}</Text>
                    </View>
                  ))}
                </View>
              </>
            )}

            <View style={{ height: 40 }} />
          </ScrollView>
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:  { flex: 1, backgroundColor: C.bg },
  center:     { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:     { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:       { fontSize: 24, color: C.txt },
  title:      { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  sectLbl:    { fontSize: 11, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 1, paddingHorizontal: 16, marginTop: 20, marginBottom: 10 },
  card:       { marginHorizontal: 16, marginBottom: 10, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  cardTop:    { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  cardIco:    { fontSize: 18 },
  cardTitle:  { fontSize: 14, fontWeight: '700', flex: 1 },
  cardMsg:    { fontSize: 13, color: C.txt2, lineHeight: 20 },
  catGroup:   { marginHorizontal: 16, backgroundColor: C.card, borderRadius: 14, borderWidth: 1, borderColor: C.border, overflow: 'hidden' },
  sep:        { height: 1, backgroundColor: C.border },
  catRow:     { flexDirection: 'row', alignItems: 'center', padding: 14, gap: 12 },
  catName:    { fontSize: 13, fontWeight: '600', color: C.txt, marginBottom: 6 },
  barTrack:   { height: 4, backgroundColor: C.input, borderRadius: 2, overflow: 'hidden' },
  barFill:    { height: '100%', borderRadius: 2 },
  catAmt:     { fontSize: 14, fontWeight: '800', minWidth: 80, textAlign: 'right' },
  trendCard:  { marginHorizontal: 16, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border, flexDirection: 'row', justifyContent: 'space-around' },
  trendItem:  { alignItems: 'center', gap: 4 },
  trendMonth: { fontSize: 11, color: C.muted, fontWeight: '600' },
  trendGelir: { fontSize: 12, fontWeight: '700' },
  trendGider: { fontSize: 12, fontWeight: '700' },
  empty:      { alignItems: 'center', paddingVertical: 60 },
  emptyIco:   { fontSize: 48, marginBottom: 12 },
  emptyTxt:   { fontSize: 16, fontWeight: '700', color: C.txt },
  emptySub:   { fontSize: 13, color: C.txt2, marginTop: 6, textAlign: 'center', paddingHorizontal: 32 },
});
