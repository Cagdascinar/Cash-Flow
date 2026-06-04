import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors } from '../constants/Colors';

interface Props {
  balance: number;
  income: number;
  expense: number;
  period: string;
  onPeriodChange: () => void;
}

function fmt(n: number) {
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: 'TRY',
    minimumFractionDigits: 2,
  }).format(n);
}

export function BalanceCard({ balance, income, expense, period, onPeriodChange }: Props) {
  const isPositive = balance >= 0;

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.periodLabel}>Net Bakiye</Text>
        <TouchableOpacity style={styles.periodBtn} onPress={onPeriodChange}>
          <Text style={styles.periodText}>{period}</Text>
          <Text style={styles.chevron}>⌄</Text>
        </TouchableOpacity>
      </View>

      <Text style={[styles.balance, { color: isPositive ? Colors.green : Colors.red }]}>
        {fmt(balance)}
      </Text>

      <View style={styles.row}>
        <View style={styles.stat}>
          <View style={[styles.dot, { backgroundColor: Colors.green }]} />
          <View>
            <Text style={styles.statLabel}>Gelir</Text>
            <Text style={[styles.statValue, { color: Colors.green }]}>{fmt(income)}</Text>
          </View>
        </View>

        <View style={styles.divider} />

        <View style={styles.stat}>
          <View style={[styles.dot, { backgroundColor: Colors.red }]} />
          <View>
            <Text style={styles.statLabel}>Gider</Text>
            <Text style={[styles.statValue, { color: Colors.red }]}>{fmt(expense)}</Text>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bgCard,
    borderRadius: 20,
    padding: 24,
    marginHorizontal: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  periodLabel: {
    fontSize: 13,
    color: Colors.textSecondary,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
  },
  periodBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.bgInput,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
    gap: 4,
  },
  periodText: {
    fontSize: 13,
    color: Colors.textPrimary,
    fontWeight: '600',
  },
  chevron: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  balance: {
    fontSize: 36,
    fontWeight: '800',
    letterSpacing: -1,
    marginBottom: 20,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stat: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statLabel: {
    fontSize: 12,
    color: Colors.textMuted,
    marginBottom: 2,
  },
  statValue: {
    fontSize: 15,
    fontWeight: '700',
  },
  divider: {
    width: 1,
    height: 32,
    backgroundColor: Colors.border,
    marginHorizontal: 16,
  },
});
