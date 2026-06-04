import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { C, money } from '../constants/Colors';

type Period = 'ay' | 'yil' | 'tum';
const TABS: { key: Period; label: string }[] = [
  { key: 'ay',  label: 'Ay'   },
  { key: 'yil', label: 'Yıl'  },
  { key: 'tum', label: 'Tümü' },
];

interface Props {
  gelir: number; gider: number; net: number;
  period: Period; onPeriod: (p: Period) => void;
  kullanilabilir: number; kartBorcu: number;
}

export function BalanceCard({ gelir, gider, net, period, onPeriod, kullanilabilir, kartBorcu }: Props) {
  return (
    <View style={s.card}>
      {/* Üst satır */}
      <View style={s.top}>
        <Text style={s.label}>NET BAKİYE</Text>
        <Text style={s.hedgehog}>🦔</Text>
      </View>

      {/* Periyot seçici */}
      <View style={s.tabs}>
        {TABS.map(t => (
          <TouchableOpacity key={t.key} style={[s.tab, period === t.key && s.tabActive]} onPress={() => onPeriod(t.key)}>
            <Text style={[s.tabTxt, period === t.key && s.tabTxtActive]}>{t.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Ana bakiye */}
      <Text style={[s.balance, { color: net >= 0 ? C.green : C.red }]}>
        {money(net, 2)}
      </Text>

      {/* Gelir / Gider chips */}
      <View style={s.chips}>
        <View style={[s.chip, { backgroundColor: 'rgba(14,203,129,.1)', borderColor: 'rgba(14,203,129,.2)' }]}>
          <Text style={s.chipArrow}>↑</Text>
          <View>
            <Text style={[s.chipVal, { color: C.green }]}>{money(gelir)}</Text>
            <Text style={s.chipLabel}>Gelir</Text>
          </View>
        </View>
        <View style={[s.chip, { backgroundColor: 'rgba(246,70,93,.1)', borderColor: 'rgba(246,70,93,.2)' }]}>
          <Text style={s.chipArrow}>↓</Text>
          <View>
            <Text style={[s.chipVal, { color: C.red }]}>{money(gider)}</Text>
            <Text style={s.chipLabel}>Gider</Text>
          </View>
        </View>
      </View>

      {/* Alt bilgi */}
      <View style={s.footer}>
        <View style={s.footerItem}>
          <Text style={s.footerLbl}>Kullanılabilir</Text>
          <Text style={[s.footerVal, { color: kullanilabilir >= 0 ? C.green : C.red }]}>{money(kullanilabilir)}</Text>
        </View>
        <View style={s.divider} />
        <View style={s.footerItem}>
          <Text style={s.footerLbl}>Kart Borcu</Text>
          <Text style={[s.footerVal, { color: C.yellow }]}>{money(kartBorcu)}</Text>
        </View>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  card: { marginHorizontal: 16, borderRadius: 24, padding: 20, backgroundColor: C.hero, borderWidth: 1, borderColor: 'rgba(99,160,255,.12)', shadowColor: '#000', shadowOffset: { width: 0, height: 12 }, shadowOpacity: 0.5, shadowRadius: 24, elevation: 10 },
  top:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  label:{ fontSize: 11, color: 'rgba(255,255,255,.4)', fontWeight: '700', letterSpacing: 1.5, textTransform: 'uppercase' },
  hedgehog: { fontSize: 22 },
  tabs: { flexDirection: 'row', gap: 6, marginBottom: 16 },
  tab:  { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 20, backgroundColor: 'rgba(255,255,255,.06)' },
  tabActive: { backgroundColor: 'rgba(0,122,255,.2)' },
  tabTxt: { fontSize: 12, color: 'rgba(255,255,255,.4)', fontWeight: '600' },
  tabTxtActive: { color: C.blue },
  balance: { fontSize: 38, fontWeight: '900', letterSpacing: -1.5, marginBottom: 16 },
  chips: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  chip:  { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 8, padding: 10, borderRadius: 12, borderWidth: 1 },
  chipArrow: { fontSize: 16, color: 'rgba(255,255,255,.3)', fontWeight: '700' },
  chipVal:   { fontSize: 14, fontWeight: '800' },
  chipLabel: { fontSize: 11, color: 'rgba(255,255,255,.35)', marginTop: 1 },
  footer:    { flexDirection: 'row', paddingTop: 14, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,.08)' },
  footerItem:{ flex: 1, alignItems: 'center' },
  footerLbl: { fontSize: 11, color: 'rgba(255,255,255,.35)', marginBottom: 3 },
  footerVal: { fontSize: 14, fontWeight: '800' },
  divider:   { width: 1, backgroundColor: 'rgba(255,255,255,.08)', marginHorizontal: 12 },
});
