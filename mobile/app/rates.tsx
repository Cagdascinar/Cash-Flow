import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity, ScrollView, RefreshControl } from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { misc } from '../services/api';

const RATE_ICONS: Record<string, string> = {
  usd: '🇺🇸', eur: '🇪🇺', gbp: '🇬🇧', jpy: '🇯🇵',
  gold: '🥇', silver: '🥈', bist100: '📈',
};

export default function RatesScreen() {
  const router = useRouter();
  const [rates,   setRates]   = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setRates(await misc.rates()); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const items = rates ? Object.entries(rates).filter(([k]) => k !== 'timestamp') : [];

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <View>
          <Text style={s.title}>Canlı Kurlar</Text>
          {rates?.timestamp && <Text style={s.ts}>{new Date(rates.timestamp * 1000).toLocaleTimeString('tr-TR')}</Text>}
        </View>
        <TouchableOpacity onPress={() => load(true)} style={s.refreshBtn}>
          <Text style={s.refreshTxt}>↻ Yenile</Text>
        </TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>
            <View style={s.grid}>
              {items.map(([key, val]) => {
                const v = Number(val);
                return (
                  <View key={key} style={s.card}>
                    <Text style={s.ico}>{RATE_ICONS[key.toLowerCase()] ?? '💱'}</Text>
                    <Text style={s.symbol}>{key.toUpperCase()}</Text>
                    <Text style={s.price}>₺{v.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}</Text>
                  </View>
                );
              })}
            </View>
            {items.length === 0 && (
              <View style={s.empty}>
                <Text style={s.emptyIco}>📡</Text>
                <Text style={s.emptyTxt}>Kurlar yüklenemedi</Text>
              </View>
            )}
            <View style={{ height: 40 }} />
          </ScrollView>
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:         { flex: 1, backgroundColor: C.bg },
  center:     { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:     { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8, gap: 12 },
  back:       { fontSize: 24, color: C.txt },
  title:      { fontSize: 20, fontWeight: '800', color: C.txt },
  ts:         { fontSize: 11, color: C.txt2, marginTop: 2 },
  refreshBtn: { marginLeft: 'auto' as any, backgroundColor: C.card, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 7, borderWidth: 1, borderColor: C.border },
  refreshTxt: { fontSize: 13, fontWeight: '600', color: C.blue },
  grid:       { flexDirection: 'row', flexWrap: 'wrap', padding: 12, gap: 10 },
  card:       { width: '47%', backgroundColor: C.card, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: C.border, alignItems: 'center', gap: 6 },
  ico:        { fontSize: 32 },
  symbol:     { fontSize: 14, fontWeight: '700', color: C.txt2 },
  price:      { fontSize: 18, fontWeight: '800', color: C.txt },
  empty:      { alignItems: 'center', paddingVertical: 48 },
  emptyIco:   { fontSize: 48, marginBottom: 12 },
  emptyTxt:   { fontSize: 15, color: C.txt2 },
});
