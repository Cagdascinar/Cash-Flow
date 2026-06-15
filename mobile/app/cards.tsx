import { View, Text, ScrollView, StyleSheet, ActivityIndicator, RefreshControl, TouchableOpacity, Alert } from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { cards as cardsApi } from '../services/api';
import { SwipeableRow } from '../components/SwipeableRow';

const TYPE_ICO: Record<string, string> = { kredi: '💳', banka: '🏦', yemek: '🍽️', hediye: '🎁' };

function Bar({ used, limit }: { used: number; limit: number }) {
  const pct   = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  const color = pct > 85 ? C.red : pct > 60 ? C.yellow : C.green;
  return (
    <View>
      <View style={b.track}><View style={[b.fill, { width: `${pct}%`, backgroundColor: color }]} /></View>
      <View style={b.row}>
        <Text style={b.txt}>Kullanılan: {money(used)}</Text>
        <Text style={[b.pct, { color }]}>%{Math.round(pct)}</Text>
      </View>
    </View>
  );
}
const b = StyleSheet.create({
  track: { height: 6, backgroundColor: C.input, borderRadius: 3, overflow: 'hidden', marginTop: 10 },
  fill:  { height: '100%', borderRadius: 3 },
  row:   { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  txt:   { fontSize: 12, color: C.txt2 },
  pct:   { fontSize: 12, fontWeight: '700' },
});

export default function CardsScreen() {
  const [list,  setList]   = useState<any[]>([]);
  const [load,  setLoad]   = useState(true);
  const [ref,   setRef]    = useState(false);
  const router = useRouter();

  const fetch = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoad(true);
    try { setList(await cardsApi.list() as any[]); } catch {}
    finally { setLoad(false); setRef(false); }
  }, []);

  async function delCard(id: number) {
    Alert.alert('Kartı Sil', 'Bu kartı silmek istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await cardsApi.delete(id); setList(p => p.filter(c => c.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  useEffect(() => { fetch(); }, [fetch]);

  const debt  = list.reduce((s, c) => s + (c.used_  ?? 0), 0);
  const limit = list.reduce((s, c) => s + (c.limit_ ?? 0), 0);
  const min   = list.reduce((s, c) => s + Math.round((c.used_ ?? 0) * ((c.min_pct ?? 25) / 100)), 0);

  if (load) return <SafeAreaView style={s.bg}><View style={s.center}><ActivityIndicator color={C.blue} /></View></SafeAreaView>;

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={ref} onRefresh={() => fetch(true)} tintColor={C.blue} />}>

        <View style={s.header}>
          <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
          <Text style={s.title}>Kredi Kartları</Text>
          <TouchableOpacity style={s.addBtn} onPress={() => router.push('/add-card' as any)}>
            <Text style={s.addTxt}>+ Ekle</Text>
          </TouchableOpacity>
        </View>

        {list.length > 0 && (
          <View style={s.row3}>
            {[['Borç', money(debt), C.red], ['Kullanılabilir', money(limit - debt), C.green], ['Asgari', money(min), C.yellow]].map(([lbl, val, col]) => (
              <View key={lbl as string} style={s.box}>
                <Text style={[s.boxVal, { color: col as string }]}>{val}</Text>
                <Text style={s.boxLbl}>{lbl}</Text>
              </View>
            ))}
          </View>
        )}

        {list.length === 0
          ? <View style={s.empty}><Text style={{ fontSize: 48 }}>💳</Text><Text style={s.emptyTxt}>Kart eklenmedi</Text><Text style={s.emptySub}>Web'den ekleyebilirsiniz</Text></View>
          : list.map(c => (
              <SwipeableRow
                key={c.id}
                style={{ marginHorizontal: 16, marginBottom: 12, borderRadius: 16 }}
                actions={[{ label: 'Sil', icon: '🗑️', color: '#dc2626', onPress: () => delCard(c.id) }]}
              >
                <View style={s.card}>
                  <View style={s.cardTop}>
                    <View style={s.ico}><Text style={{ fontSize: 20 }}>{TYPE_ICO[c.card_type] ?? '💳'}</Text></View>
                    <View style={{ flex: 1 }}>
                      <Text style={s.bank}>{c.bank_name}</Text>
                      <Text style={s.cname}>{c.card_name || c.card_type}</Text>
                    </View>
                    <Text style={s.lim}>Limit: {money(c.limit_)}</Text>
                  </View>
                  <Bar used={c.used_ ?? 0} limit={c.limit_ ?? 0} />
                  <View style={s.footer}>
                    {[['Ekstre', String(c.statement_day)], ['Son Ödeme', String(c.due_day)], ['Asgari', money(Math.round((c.used_ ?? 0) * ((c.min_pct ?? 25) / 100)))]].map(([lbl, val]) => (
                      <View key={lbl as string} style={{ flex: 1, alignItems: 'center' }}>
                        <Text style={s.fLbl}>{lbl}</Text>
                        <Text style={s.fVal}>{val}</Text>
                      </View>
                    ))}
                  </View>
                  <TouchableOpacity style={s.payBtn} onPress={() => router.push({ pathname: '/pay-card' as any, params: { id: c.id, bank: c.bank_name, name: c.card_name || '', used: String(c.used_ ?? 0), min: String(Math.round((c.used_ ?? 0) * ((c.min_pct ?? 25) / 100))) } })}>
                    <Text style={s.payTxt}>💳 Ödeme Yap</Text>
                  </TouchableOpacity>
                </View>
              </SwipeableRow>
            ))
        }
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:      { flex: 1, backgroundColor: C.bg },
  center:  { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:  { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8, gap: 12 },
  back:    { fontSize: 24, color: C.txt },
  title:   { fontSize: 22, fontWeight: '800', color: C.txt, flex: 1 },
  addBtn:  { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 7 },
  addTxt:  { fontSize: 14, fontWeight: '700', color: C.white },
  row3:    { flexDirection: 'row', marginHorizontal: 16, marginBottom: 12, gap: 8 },
  box:     { flex: 1, backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  boxVal:  { fontSize: 13, fontWeight: '800' },
  boxLbl:  { fontSize: 10, color: C.txt2, marginTop: 2 },
  card:    { backgroundColor: C.card, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: C.border },
  cardTop: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  ico:     { width: 40, height: 40, borderRadius: 12, backgroundColor: C.input, alignItems: 'center', justifyContent: 'center' },
  bank:    { fontSize: 15, fontWeight: '700', color: C.txt },
  cname:   { fontSize: 12, color: C.txt2, marginTop: 2 },
  lim:     { fontSize: 12, color: C.txt2, fontWeight: '600' },
  footer:  { flexDirection: 'row', marginTop: 14, paddingTop: 14, borderTopWidth: 1, borderTopColor: C.border },
  fLbl:    { fontSize: 11, color: C.muted },
  fVal:    { fontSize: 14, fontWeight: '700', color: C.txt, marginTop: 2 },
  payBtn:  { marginTop: 12, backgroundColor: C.green, borderRadius: 10, paddingVertical: 10, alignItems: 'center' },
  payTxt:  { fontSize: 13, fontWeight: '700', color: C.white },
  empty:   { alignItems: 'center', paddingVertical: 48 },
  emptyTxt:{ fontSize: 16, fontWeight: '600', color: C.txt, marginTop: 12 },
  emptySub:{ fontSize: 13, color: C.txt2, marginTop: 4 },
});
