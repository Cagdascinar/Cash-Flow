import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors } from '../constants/Colors';

interface Props {
  balance: number;
  income:  number;
  expense: number;
  period:  string;
  onPeriodChange: () => void;
}

function fmt(n: number) {
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency', currency: 'TRY', minimumFractionDigits: 2,
  }).format(n);
}

const PERIODS = ['Ay', 'Yıl', 'Tümü'];

export function BalanceCard({ balance, income, expense, period, onPeriodChange }: Props) {
  const isPos = balance >= 0;
  const activePeriodIdx = ['Bu Ay', 'Bu Yıl', 'Tümü'].indexOf(period);

  return (
    <View style={s.card}>
      {/* Header */}
      <View style={s.topRow}>
        <Text style={s.greeting}>Bu {period}</Text>
        <Text style={s.hedgehog}>🦔</Text>
      </View>

      {/* Periyot sekmeleri */}
      <View style={s.tabs}>
        {PERIODS.map((p, i) => (
          <TouchableOpacity
            key={p}
            style={[s.tab, activePeriodIdx === i && s.tabActive]}
            onPress={onPeriodChange}
          >
            <Text style={[s.tabText, activePeriodIdx === i && s.tabTextActive]}>{p}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Bakiye etiketi */}
      <Text style={s.balLabel}>NET BAKİYE</Text>

      {/* Ana bakiye */}
      <Text style={[s.balance, { color: isPos ? Colors.green : Colors.red }]}>
        {fmt(balance)}
      </Text>

      {/* Gelir / Gider chips */}
      <View style={s.chips}>
        <View style={[s.chip, { backgroundColor: 'rgba(14,203,129,.12)' }]}>
          <Text style={s.chipArrow}>↑</Text>
          <Text style={[s.chipVal, { color: Colors.green }]}>{fmt(income)}</Text>
          <Text style={s.chipLabel}>Gelir</Text>
        </View>
        <View style={[s.chip, { backgroundColor: 'rgba(246,70,93,.12)' }]}>
          <Text style={s.chipArrow}>↓</Text>
          <Text style={[s.chipVal, { color: Colors.red }]}>{fmt(expense)}</Text>
          <Text style={s.chipLabel}>Gider</Text>
        </View>
        <View style={[s.chip, { backgroundColor: 'rgba(0,122,255,.1)' }]}>
          <Text style={s.chipArrow}>=</Text>
          <Text style={[s.chipVal, { color: Colors.blue }]}>{fmt(balance)}</Text>
          <Text style={s.chipLabel}>Net</Text>
        </View>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    borderRadius: 28,
    padding: 24,
    backgroundColor: '#0d1f3c',
    borderWidth: 1,
    borderColor: 'rgba(99,160,255,.12)',
    shadowColor: '#050e22',
    shadowOffset: { width: 0, height: 20 },
    shadowOpacity: 0.7,
    shadowRadius: 40,
    elevation: 12,
  },
  topRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  greeting: { fontSize: 13, color: 'rgba(255,255,255,.45)', fontWeight: '500' },
  hedgehog: { fontSize: 22 },
  tabs: { flexDirection: 'row', gap: 6, marginBottom: 16 },
  tab: {
    paddingHorizontal: 14, paddingVertical: 5,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,.06)',
  },
  tabActive: { backgroundColor: 'rgba(0,122,255,.25)' },
  tabText: { fontSize: 12, color: 'rgba(255,255,255,.45)', fontWeight: '600' },
  tabTextActive: { color: Colors.blue },
  balLabel: {
    fontSize: 11, fontWeight: '700', color: 'rgba(255,255,255,.35)',
    letterSpacing: 1.5, textTransform: 'uppercase', marginBottom: 6,
  },
  balance: { fontSize: 36, fontWeight: '900', letterSpacing: -1, marginBottom: 20 },
  chips: { flexDirection: 'row', gap: 8 },
  chip: { flex: 1, borderRadius: 12, padding: 10, alignItems: 'center', gap: 2 },
  chipArrow: { fontSize: 14, color: 'rgba(255,255,255,.4)', fontWeight: '700' },
  chipVal: { fontSize: 12, fontWeight: '800' },
  chipLabel: { fontSize: 10, color: 'rgba(255,255,255,.35)', fontWeight: '500' },
});
