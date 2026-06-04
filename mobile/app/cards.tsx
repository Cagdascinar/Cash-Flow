import {
  View, Text, ScrollView, StyleSheet,
  ActivityIndicator, RefreshControl, TouchableOpacity, Alert,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Colors } from '../constants/Colors';
import { cards as cardsApi } from '../services/api';

function fmt(n: number) {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 0 }).format(n ?? 0);
}

function UtilBar({ used, limit }: { used: number; limit: number }) {
  const pct = limit > 0 ? Math.min((used / limit) * 100, 100) : 0;
  const color = pct > 85 ? Colors.red : pct > 60 ? Colors.yellow : Colors.green;
  return (
    <View>
      <View style={b.track}>
        <View style={[b.fill, { width: `${pct}%`, backgroundColor: color }]} />
      </View>
      <View style={b.row}>
        <Text style={b.txt}>Kullanılan: {fmt(used)}</Text>
        <Text style={[b.pct, { color }]}>%{Math.round(pct)}</Text>
      </View>
    </View>
  );
}
const b = StyleSheet.create({
  track: { height: 6, backgroundColor: Colors.bgInput, borderRadius: 3, overflow: 'hidden', marginTop: 10 },
  fill:  { height: '100%', borderRadius: 3 },
  row:   { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  txt:   { fontSize: 12, color: Colors.textSecondary },
  pct:   { fontSize: 12, fontWeight: '700' },
});

const TYPE_ICONS: Record<string, string> = {
  kredi: '💳', banka: '🏦', yemek: '🍽️', hediye: '🎁',
};

export default function CardsScreen() {
  const [cardsList,  setCards]    = useState<any[]>([]);
  const [loading,    setLoading]  = useState(true);
  const [refreshing, setRef]      = useState(false);
  const router = useRouter();

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const data = await cardsApi.list();
      setCards(Array.isArray(data) ? data : []);
    } finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const totalDebt  = cardsList.reduce((s, c) => s + (c.used_  ?? 0), 0);
  const totalLimit = cardsList.reduce((s, c) => s + (c.limit_ ?? 0), 0);
  const totalMin   = cardsList.reduce((s, c) => s + Math.round((c.used_ ?? 0) * ((c.min_pct ?? 25) / 100)), 0);

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
        {/* Header */}
        <View style={s.header}>
          <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
            <Text style={s.backIco}>←</Text>
          </TouchableOpacity>
          <Text style={s.title}>Kredi Kartları</Text>
        </View>

        {/* Özet */}
        {cardsList.length > 0 && (
          <View style={s.summaryRow}>
            <SumBox label="Toplam Borç"      value={fmt(totalDebt)}             color={Colors.red} />
            <SumBox label="Kullanılabilir"   value={fmt(totalLimit - totalDebt)} color={Colors.green} />
            <SumBox label="Asgari Ödeme"     value={fmt(totalMin)}              color={Colors.yellow} />
          </View>
        )}

        {/* Kart listesi */}
        {cardsList.length === 0
          ? <View style={s.empty}>
              <Text style={s.emptyIco}>💳</Text>
              <Text style={s.emptyTxt}>Henüz kart eklenmedi</Text>
              <Text style={s.emptySub}>Web uygulamasından kart ekleyebilirsiniz</Text>
            </View>
          : cardsList.map(c => (
              <View key={c.id} style={s.card}>
                <View style={s.cardTop}>
                  <View style={s.cardIcon}>
                    <Text style={s.cardIconTxt}>{TYPE_ICONS[c.card_type] ?? '💳'}</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={s.bankName}>{c.bank_name}</Text>
                    <Text style={s.cardName}>{c.card_name || c.card_type}</Text>
                  </View>
                  <View style={s.limitBadge}>
                    <Text style={s.limitTxt}>Limit: {fmt(c.limit_)}</Text>
                  </View>
                </View>

                <UtilBar used={c.used_ ?? 0} limit={c.limit_ ?? 0} />

                <View style={s.cardFooter}>
                  <View style={s.footerItem}>
                    <Text style={s.footerLabel}>Ekstre Günü</Text>
                    <Text style={s.footerVal}>{c.statement_day}</Text>
                  </View>
                  <View style={s.footerItem}>
                    <Text style={s.footerLabel}>Son Ödeme</Text>
                    <Text style={s.footerVal}>{c.due_day}</Text>
                  </View>
                  <View style={s.footerItem}>
                    <Text style={s.footerLabel}>Asgari</Text>
                    <Text style={[s.footerVal, { color: Colors.yellow }]}>
                      {fmt(Math.round((c.used_ ?? 0) * ((c.min_pct ?? 25) / 100)))}
                    </Text>
                  </View>
                </View>
              </View>
            ))
        }

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function SumBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <View style={sm.box}>
      <Text style={[sm.val, { color }]}>{value}</Text>
      <Text style={sm.lbl}>{label}</Text>
    </View>
  );
}
const sm = StyleSheet.create({
  box: { flex: 1, backgroundColor: Colors.bgCard, borderRadius: 14, padding: 12, borderWidth: 1, borderColor: Colors.border, alignItems: 'center' },
  val: { fontSize: 14, fontWeight: '800', marginBottom: 2 },
  lbl: { fontSize: 10, color: Colors.textSecondary, textAlign: 'center' },
});

const s = StyleSheet.create({
  container:  { flex: 1, backgroundColor: Colors.bg },
  center:     { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:     { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8, gap: 12 },
  backBtn:    {},
  backIco:    { fontSize: 24, color: Colors.textPrimary },
  title:      { fontSize: 22, fontWeight: '800', color: Colors.textPrimary },
  summaryRow: { flexDirection: 'row', marginHorizontal: 16, marginBottom: 16, gap: 8 },
  card:       { marginHorizontal: 16, marginBottom: 12, backgroundColor: Colors.bgCard, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: Colors.border },
  cardTop:    { flexDirection: 'row', alignItems: 'center', gap: 12 },
  cardIcon:   { width: 40, height: 40, borderRadius: 12, backgroundColor: Colors.bgInput, alignItems: 'center', justifyContent: 'center' },
  cardIconTxt:{ fontSize: 20 },
  bankName:   { fontSize: 15, fontWeight: '700', color: Colors.textPrimary },
  cardName:   { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  limitBadge: { backgroundColor: Colors.bgInput, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4 },
  limitTxt:   { fontSize: 12, color: Colors.textSecondary, fontWeight: '600' },
  cardFooter: { flexDirection: 'row', marginTop: 14, paddingTop: 14, borderTopWidth: 1, borderTopColor: Colors.border },
  footerItem: { flex: 1, alignItems: 'center' },
  footerLabel:{ fontSize: 11, color: Colors.textMuted },
  footerVal:  { fontSize: 14, fontWeight: '700', color: Colors.textPrimary, marginTop: 2 },
  empty:      { alignItems: 'center', paddingVertical: 48 },
  emptyIco:   { fontSize: 48, marginBottom: 12 },
  emptyTxt:   { fontSize: 16, fontWeight: '600', color: Colors.textPrimary },
  emptySub:   { fontSize: 13, color: Colors.textSecondary, marginTop: 4 },
});
