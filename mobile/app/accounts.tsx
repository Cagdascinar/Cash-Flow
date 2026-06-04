import {
  View, Text, ScrollView, StyleSheet,
  ActivityIndicator, RefreshControl, TouchableOpacity,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Colors } from '../constants/Colors';
import { accounts as accountsApi } from '../services/api';

function fmt(n: number) {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 0 }).format(n ?? 0);
}

const TYPE_LABELS: Record<string, string> = {
  vadesiz: 'Vadesiz Hesap', vadeli: 'Vadeli Hesap',
  kredi_karti: 'Kredi Kartı', kmh: 'KMH', diger: 'Diğer',
};

export default function AccountsScreen() {
  const [list,       setList]     = useState<any[]>([]);
  const [loading,    setLoading]  = useState(true);
  const [refreshing, setRef]      = useState(false);
  const router = useRouter();

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const data = await accountsApi.list();
      setList(Array.isArray(data) ? data : []);
    } finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const totalBalance = list
    .filter(a => !['kredi_karti', 'kmh'].includes(a.type))
    .reduce((s, a) => s + (a.computed_balance ?? 0), 0);

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
        <View style={s.header}>
          <TouchableOpacity onPress={() => router.back()}>
            <Text style={s.backIco}>←</Text>
          </TouchableOpacity>
          <Text style={s.title}>Hesaplar</Text>
        </View>

        {/* Toplam bakiye */}
        {list.length > 0 && (
          <View style={s.totalCard}>
            <Text style={s.totalLabel}>Toplam Nakit Bakiye</Text>
            <Text style={[s.totalVal, { color: totalBalance >= 0 ? Colors.green : Colors.red }]}>
              {fmt(totalBalance)}
            </Text>
            <Text style={s.totalSub}>{list.filter(a => !['kredi_karti','kmh'].includes(a.type)).length} hesap</Text>
          </View>
        )}

        {/* Hesap listesi */}
        {list.length === 0
          ? <View style={s.empty}>
              <Text style={s.emptyIco}>🏦</Text>
              <Text style={s.emptyTxt}>Henüz hesap eklenmedi</Text>
              <Text style={s.emptySub}>Web uygulamasından hesap ekleyebilirsiniz</Text>
            </View>
          : list.map(acc => {
              const bal = acc.computed_balance ?? 0;
              const isDebt = ['kredi_karti', 'kmh'].includes(acc.type);
              const color = isDebt ? Colors.red : bal >= 0 ? Colors.green : Colors.red;
              const dotColor = acc.color ?? Colors.blue;
              return (
                <View key={acc.id} style={s.card}>
                  <View style={s.cardLeft}>
                    <View style={[s.dot, { backgroundColor: dotColor }]} />
                    <View style={{ flex: 1 }}>
                      <Text style={s.accName}>{acc.name}</Text>
                      <Text style={s.bankName}>{acc.bank} · {TYPE_LABELS[acc.type] ?? acc.type}</Text>
                    </View>
                  </View>
                  <View style={s.cardRight}>
                    <Text style={[s.balance, { color }]}>{fmt(Math.abs(bal))}</Text>
                    {isDebt && <Text style={s.debtLabel}>Borç</Text>}
                    {acc.available != null && (
                      <Text style={s.available}>Kalan: {fmt(acc.available)}</Text>
                    )}
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
  container:  { flex: 1, backgroundColor: Colors.bg },
  center:     { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:     { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8, gap: 12 },
  backIco:    { fontSize: 24, color: Colors.textPrimary },
  title:      { fontSize: 22, fontWeight: '800', color: Colors.textPrimary },
  totalCard:  { margin: 16, backgroundColor: '#0d1f3c', borderRadius: 16, padding: 20, borderWidth: 1, borderColor: 'rgba(99,160,255,.15)', alignItems: 'center' },
  totalLabel: { fontSize: 13, color: 'rgba(255,255,255,.45)', fontWeight: '500' },
  totalVal:   { fontSize: 32, fontWeight: '900', marginTop: 4, letterSpacing: -1 },
  totalSub:   { fontSize: 12, color: 'rgba(255,255,255,.35)', marginTop: 4 },
  card:       { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 10, backgroundColor: Colors.bgCard, borderRadius: 14, padding: 16, borderWidth: 1, borderColor: Colors.border },
  cardLeft:   { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 12 },
  dot:        { width: 12, height: 12, borderRadius: 6 },
  accName:    { fontSize: 15, fontWeight: '600', color: Colors.textPrimary },
  bankName:   { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  cardRight:  { alignItems: 'flex-end' },
  balance:    { fontSize: 16, fontWeight: '800' },
  debtLabel:  { fontSize: 11, color: Colors.red, marginTop: 2 },
  available:  { fontSize: 11, color: Colors.green, marginTop: 2 },
  empty:      { alignItems: 'center', paddingVertical: 48 },
  emptyIco:   { fontSize: 48, marginBottom: 12 },
  emptyTxt:   { fontSize: 16, fontWeight: '600', color: Colors.textPrimary },
  emptySub:   { fontSize: 13, color: Colors.textSecondary, marginTop: 4 },
});
