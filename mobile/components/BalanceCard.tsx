import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { C, money } from '../constants/Colors';

type Period = 'ay' | 'yil' | 'tum';
const TABS: { key: Period; label: string }[] = [
  { key: 'ay',  label: 'Bu Ay'  },
  { key: 'yil', label: 'Bu Yıl' },
  { key: 'tum', label: 'Tümü'   },
];

interface Props {
  gelir: number; gider: number; net: number;
  period: Period; onPeriod: (p: Period) => void;
  kullanilabilir: number; kartBorcu: number;
}

export function BalanceCard({ gelir, gider, net, period, onPeriod, kullanilabilir, kartBorcu }: Props) {
  const savingRate = gelir > 0 ? Math.round((Math.max(net, 0) / gelir) * 100) : 0;

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
      <Text style={[s.balance, { color: net >= 0 ? '#4ade80' : '#f87171' }]}>
        {money(net, 2)}
      </Text>

      {/* Gelir / Gider chips */}
      <View style={s.chips}>
        <View style={[s.chip, { backgroundColor: 'rgba(74,222,128,.08)', borderColor: 'rgba(74,222,128,.2)' }]}>
          <View style={s.chipArrowBox}>
            <Text style={[s.chipArrow, { color: '#4ade80' }]}>↑</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[s.chipVal, { color: '#4ade80' }]}>{money(gelir)}</Text>
            <Text style={s.chipLabel}>Gelir</Text>
          </View>
        </View>
        <View style={[s.chip, { backgroundColor: 'rgba(248,113,113,.08)', borderColor: 'rgba(248,113,113,.2)' }]}>
          <View style={s.chipArrowBox}>
            <Text style={[s.chipArrow, { color: '#f87171' }]}>↓</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[s.chipVal, { color: '#f87171' }]}>{money(gider)}</Text>
            <Text style={s.chipLabel}>Gider</Text>
          </View>
        </View>
      </View>

      {/* Alt bilgi */}
      <View style={s.footer}>
        <View style={s.footerItem}>
          <Text style={s.footerLbl}>Kullanılabilir</Text>
          <Text style={[s.footerVal, { color: kullanilabilir >= 0 ? '#4ade80' : '#f87171' }]}>{money(kullanilabilir)}</Text>
        </View>
        <View style={s.divider} />
        <View style={s.footerItem}>
          <Text style={s.footerLbl}>Kart Borcu</Text>
          <Text style={[s.footerVal, { color: '#fbbf24' }]}>{money(kartBorcu)}</Text>
        </View>
        <View style={s.divider} />
        <View style={s.footerItem}>
          <Text style={s.footerLbl}>Tasarruf</Text>
          <Text style={[s.footerVal, { color: savingRate >= 20 ? '#4ade80' : savingRate >= 10 ? '#fbbf24' : '#f87171' }]}>
            %{savingRate}
          </Text>
        </View>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  card: { marginHorizontal: 16, borderRadius: 24, padding: 20, backgroundColor: C.hero, borderWidth: 1, borderColor: 'rgba(99,160,255,.12)', shadowColor: '#000', shadowOffset: { width: 0, height: 12 }, shadowOpacity: 0.5, shadowRadius: 24, elevation: 10 },
  top:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  label:{ fontSize: 11, color: 'rgba(255,255,255,.6)', fontWeight: '700', letterSpacing: 1.5, textTransform: 'uppercase' },
  hedgehog: { fontSize: 22 },
  tabs: { flexDirection: 'row', gap: 6, marginBottom: 16 },
  tab:  { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 20, backgroundColor: 'rgba(255,255,255,.06)' },
  tabActive: { backgroundColor: 'rgba(0,122,255,.25)' },
  tabTxt: { fontSize: 12, color: 'rgba(255,255,255,.5)', fontWeight: '600' },
  tabTxtActive: { color: '#60a5fa', fontWeight: '700' },
  balance: { fontSize: 38, fontWeight: '900', letterSpacing: -1.5, marginBottom: 16 },
  chips: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  chip:  { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 8, padding: 10, borderRadius: 12, borderWidth: 1 },
  chipArrowBox: { width: 28, height: 28, borderRadius: 8, backgroundColor: 'rgba(255,255,255,.06)', alignItems: 'center', justifyContent: 'center' },
  chipArrow: { fontSize: 14, fontWeight: '800' },
  chipVal:   { fontSize: 14, fontWeight: '800', letterSpacing: -0.3 },
  chipLabel: { fontSize: 11, color: 'rgba(255,255,255,.55)', marginTop: 2, fontWeight: '500' },
  footer:    { flexDirection: 'row', paddingTop: 14, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,.1)' },
  footerItem:{ flex: 1, alignItems: 'center' },
  footerLbl: { fontSize: 10, color: 'rgba(255,255,255,.5)', marginBottom: 4, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5 },
  footerVal: { fontSize: 13, fontWeight: '800' },
  divider:   { width: 1, backgroundColor: 'rgba(255,255,255,.1)', marginHorizontal: 8 },
});
