import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { ploss as plossApi } from '../services/api';

export default function PLossScreen() {
  const router  = useRouter();
  const now     = new Date();
  const [year,  setYear]  = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [data,  setData]  = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [ref,   setRef]   = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setData(await plossApi.get(year)); } catch {}
    finally { setLoading(false); setRef(false); }
  }, [year]);

  useEffect(() => { load(); }, [load]);

  const MONTHS = ['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'];

  // Seçili aya ait veriyi bul
  const periodKey = `${year}-${String(month).padStart(2, '0')}`;
  const monthData = data?.monthly?.find((m: any) => m.period === periodKey);

  function prevMonth() {
    if (month === 1) { setMonth(12); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  }
  function nextMonth() {
    if (month === 12) { setMonth(1); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  }

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Kar-Zarar</Text>
        <View style={{ width: 60 }} />
      </View>

      {/* Dönem */}
      <View style={s.periodRow}>
        <TouchableOpacity onPress={prevMonth}><Text style={s.arrow}>‹</Text></TouchableOpacity>
        <Text style={s.periodTxt}>{MONTHS[month - 1]} {year}</Text>
        <TouchableOpacity onPress={nextMonth}><Text style={s.arrow}>›</Text></TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}
            contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>

            {/* Aylık özet */}
            {monthData ? (
              <>
                <View style={[s.netCard, { borderColor: (monthData.net ?? 0) >= 0 ? '#166534' : '#7c2d12' }]}>
                  <Text style={s.netLbl}>Net Kar / Zarar</Text>
                  <Text style={[s.netVal, { color: (monthData.net ?? 0) >= 0 ? '#4ade80' : C.red }]}>
                    {money(monthData.net ?? 0)}
                  </Text>
                  <Text style={s.netSub}>{MONTHS[month-1]} {year} dönemi</Text>
                </View>

                <View style={s.section}>
                  <Text style={s.secTitle}>AYLARA GÖRE ÖZET</Text>
                  <View style={s.rowLine}>
                    <Text style={s.lbl}>Gelir</Text>
                    <Text style={[s.val, { color: '#4ade80' }]}>{money(monthData.gelir ?? 0)}</Text>
                  </View>
                  <View style={s.rowLine}>
                    <Text style={s.lbl}>Gider</Text>
                    <Text style={[s.val, { color: C.red }]}>{money(monthData.gider ?? 0)}</Text>
                  </View>
                  <View style={[s.rowLine, { borderBottomWidth: 0 }]}>
                    <Text style={[s.lbl, { fontWeight: '800', color: C.txt }]}>Net</Text>
                    <Text style={[s.val, { fontWeight: '800', color: (monthData.net ?? 0) >= 0 ? '#4ade80' : C.red }]}>
                      {money(monthData.net ?? 0)}
                    </Text>
                  </View>
                </View>
              </>
            ) : (
              <View style={[s.netCard, { borderColor: C.border }]}>
                <Text style={[s.netLbl, { marginBottom: 8 }]}>{MONTHS[month-1]} {year}</Text>
                <Text style={{ color: C.muted, fontSize: 14 }}>Bu ay için veri yok</Text>
              </View>
            )}

            {/* Yıllık özet */}
            {data && (
              <View style={s.section}>
                <Text style={s.secTitle}>{year} YILI TOPLAM</Text>
                <View style={s.rowLine}>
                  <Text style={s.lbl}>Toplam Gelir</Text>
                  <Text style={[s.val, { color: '#4ade80' }]}>{money(data.total_gelir ?? 0)}</Text>
                </View>
                <View style={s.rowLine}>
                  <Text style={s.lbl}>Toplam Gider</Text>
                  <Text style={[s.val, { color: C.red }]}>{money(data.total_gider ?? 0)}</Text>
                </View>
                <View style={[s.rowLine, { borderBottomWidth: 0 }]}>
                  <Text style={[s.lbl, { fontWeight: '800', color: C.txt }]}>Yıllık Net Kar</Text>
                  <Text style={[s.val, { fontWeight: '800', color: (data.net_kar ?? 0) >= 0 ? '#4ade80' : C.red }]}>
                    {money(data.net_kar ?? 0)}
                  </Text>
                </View>
              </View>
            )}

            {/* Aylık grafik (tüm yıl) */}
            {data?.monthly?.length > 0 && (
              <View style={s.section}>
                <Text style={s.secTitle}>AYLIK GELİŞİM</Text>
                {(data.monthly as any[]).map((m: any) => {
                  const isSelected = m.period === periodKey;
                  return (
                    <TouchableOpacity key={m.period} style={[s.monthRow, isSelected && s.monthRowActive]}
                      onPress={() => {
                        const [y, mo] = m.period.split('-').map(Number);
                        setYear(y); setMonth(mo);
                      }}>
                      <Text style={[s.monthPeriod, isSelected && { color: '#4ade80' }]}>{m.period}</Text>
                      <View style={s.monthBars}>
                        <Text style={{ color: '#4ade80', fontSize: 12 }}>{money(m.gelir)}</Text>
                        <Text style={{ color: C.muted, fontSize: 10 }}>→</Text>
                        <Text style={{ color: C.red, fontSize: 12 }}>{money(m.gider)}</Text>
                      </View>
                      <Text style={[s.monthNet, { color: (m.net ?? 0) >= 0 ? '#4ade80' : C.red }]}>
                        {(m.net ?? 0) >= 0 ? '+' : ''}{money(m.net ?? 0)}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            )}

            {/* En büyük gider kategorileri */}
            {data?.gider_cats?.length > 0 && (
              <View style={s.section}>
                <Text style={s.secTitle}>EN BÜYÜK GİDER KATEGORİLERİ</Text>
                {(data.gider_cats as [string, number][]).slice(0, 5).map(([cat, amt]) => (
                  <View key={cat} style={s.rowLine}>
                    <Text style={s.lbl}>{cat}</Text>
                    <Text style={[s.val, { color: C.red }]}>{money(amt)}</Text>
                  </View>
                ))}
              </View>
            )}
          </ScrollView>
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:          { flex: 1, backgroundColor: C.bg },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:      { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:        { fontSize: 24, color: C.txt },
  title:       { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  periodRow:   { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 10, gap: 24 },
  arrow:       { fontSize: 30, color: C.txt, paddingHorizontal: 8 },
  periodTxt:   { fontSize: 17, fontWeight: '700', color: C.txt, minWidth: 140, textAlign: 'center' },
  netCard:     { backgroundColor: C.card, borderRadius: 16, padding: 20, marginBottom: 12, borderWidth: 1.5, alignItems: 'center' },
  netLbl:      { fontSize: 12, color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  netVal:      { fontSize: 34, fontWeight: '800', marginTop: 6 },
  netSub:      { fontSize: 12, color: C.txt2, marginTop: 4 },
  section:     { backgroundColor: C.card, borderRadius: 14, padding: 14, marginBottom: 12, borderWidth: 1, borderColor: C.border },
  secTitle:    { fontSize: 10, fontWeight: '800', color: C.muted, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 8 },
  rowLine:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#1a2030' },
  lbl:         { fontSize: 14, color: C.txt2 },
  val:         { fontSize: 14, fontWeight: '600' },
  monthRow:    { flexDirection: 'row', alignItems: 'center', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#1a2030' },
  monthRowActive: { backgroundColor: 'rgba(74,222,128,.06)', borderRadius: 8, paddingHorizontal: 6 },
  monthPeriod: { width: 72, fontSize: 13, fontWeight: '600', color: C.txt2 },
  monthBars:   { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 6 },
  monthNet:    { fontSize: 13, fontWeight: '800', minWidth: 80, textAlign: 'right' },
});
