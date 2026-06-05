import { View, Text, ScrollView, StyleSheet, ActivityIndicator, RefreshControl, TouchableOpacity } from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { accounts as accountsApi } from '../services/api';

const TYPE_LBL: Record<string, string> = { vadesiz: 'Vadesiz', vadeli: 'Vadeli', kredi_karti: 'Kredi Kartı', kmh: 'KMH', diger: 'Diğer' };

export default function AccountsScreen() {
  const [list,  setList] = useState<any[]>([]);
  const [load,  setLoad] = useState(true);
  const [ref,   setRef]  = useState(false);
  const router = useRouter();

  const fetch = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoad(true);
    try { setList(await accountsApi.list() as any[]); } catch {}
    finally { setLoad(false); setRef(false); }
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  const totalCash = list
    .filter(a => !['kredi_karti', 'kmh'].includes(a.type))
    .reduce((s, a) => s + (a.computed_balance ?? 0), 0);

  if (load) return <SafeAreaView style={s.bg}><View style={s.center}><ActivityIndicator color={C.blue} /></View></SafeAreaView>;

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={ref} onRefresh={() => fetch(true)} tintColor={C.blue} />}>

        <View style={s.header}>
          <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
          <Text style={s.title}>Hesaplar</Text>
          <TouchableOpacity style={s.addBtn} onPress={() => router.push('/add-account' as any)}>
            <Text style={s.addTxt}>+ Ekle</Text>
          </TouchableOpacity>
        </View>

        {list.length > 0 && (
          <View style={s.totalCard}>
            <Text style={s.totalLbl}>Toplam Nakit Bakiye</Text>
            <Text style={[s.totalVal, { color: totalCash >= 0 ? C.green : C.red }]}>{money(totalCash)}</Text>
          </View>
        )}

        {list.length === 0
          ? <View style={s.empty}><Text style={{ fontSize: 48 }}>🏦</Text><Text style={s.emptyTxt}>Hesap eklenmedi</Text><Text style={s.emptySub}>Web'den ekleyebilirsiniz</Text></View>
          : list.map(a => {
              const bal   = a.computed_balance ?? 0;
              const isD   = ['kredi_karti', 'kmh'].includes(a.type);
              const color = isD ? C.red : bal >= 0 ? C.green : C.red;
              return (
                <View key={a.id} style={s.card}>
                  <View style={[s.dot, { backgroundColor: a.color ?? C.blue }]} />
                  <View style={{ flex: 1 }}>
                    <Text style={s.name}>{a.name}</Text>
                    <Text style={s.bank}>{a.bank} · {TYPE_LBL[a.type] ?? a.type}</Text>
                  </View>
                  <View style={{ alignItems: 'flex-end' }}>
                    <Text style={[s.bal, { color }]}>{money(Math.abs(bal))}</Text>
                    {isD && <Text style={{ fontSize: 11, color: C.red }}>Borç</Text>}
                    {a.available != null && <Text style={{ fontSize: 11, color: C.green }}>Kalan: {money(a.available)}</Text>}
                  </View>
                </View>
              );
            })
        }
        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:       { flex: 1, backgroundColor: C.bg },
  center:   { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:   { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8, gap: 12 },
  back:     { fontSize: 24, color: C.txt },
  title:    { fontSize: 22, fontWeight: '800', color: C.txt, flex: 1 },
  addBtn:   { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 7 },
  addTxt:   { fontSize: 14, fontWeight: '700', color: C.white },
  totalCard:{ margin: 16, backgroundColor: '#0d1f3c', borderRadius: 16, padding: 20, borderWidth: 1, borderColor: 'rgba(99,160,255,.15)', alignItems: 'center' },
  totalLbl: { fontSize: 13, color: 'rgba(255,255,255,.45)' },
  totalVal: { fontSize: 30, fontWeight: '900', marginTop: 4, letterSpacing: -1 },
  card:     { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 10, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border, gap: 12 },
  dot:      { width: 12, height: 12, borderRadius: 6 },
  name:     { fontSize: 15, fontWeight: '600', color: C.txt },
  bank:     { fontSize: 12, color: C.txt2, marginTop: 2 },
  bal:      { fontSize: 16, fontWeight: '800' },
  empty:    { alignItems: 'center', paddingVertical: 48 },
  emptyTxt: { fontSize: 16, fontWeight: '600', color: C.txt, marginTop: 12 },
  emptySub: { fontSize: 13, color: C.txt2, marginTop: 4 },
});
