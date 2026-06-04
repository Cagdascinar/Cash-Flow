import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors } from '../constants/Colors';

interface Transaction {
  id: number;
  type: 'gelir' | 'gider';
  amount: number;
  category: string;
  description: string;
  date: string;
}

interface Props {
  item: Transaction;
  onPress?: (item: Transaction) => void;
  onDelete?: (id: number) => void;
}

const CATEGORY_ICONS: Record<string, string> = {
  'Maaş': '💼',
  'Serbest Meslek': '💻',
  'Kira Geliri': '🏠',
  'Yatırım Getirisi': '📈',
  'Market': '🛒',
  'Fatura': '⚡',
  'Ulaşım': '🚗',
  'Sağlık': '❤️',
  'Eğlence': '🎬',
  'Yemek/Restoran': '🍔',
  'Kira': '🏠',
  'Eğitim': '📚',
  'Giyim': '👕',
  'default': '💰',
};

function fmt(n: number) {
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: 'TRY',
    minimumFractionDigits: 2,
  }).format(n);
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
}

export function TransactionItem({ item, onPress, onDelete }: Props) {
  const isIncome = item.type === 'gelir';
  const icon = CATEGORY_ICONS[item.category] ?? CATEGORY_ICONS.default;

  return (
    <TouchableOpacity
      style={styles.item}
      onPress={() => onPress?.(item)}
      activeOpacity={0.7}
    >
      <View style={styles.iconBox}>
        <Text style={styles.iconText}>{icon}</Text>
      </View>

      <View style={styles.info}>
        <Text style={styles.desc} numberOfLines={1}>{item.description || item.category}</Text>
        <Text style={styles.meta}>{item.category} · {formatDate(item.date)}</Text>
      </View>

      <Text style={[styles.amount, { color: isIncome ? Colors.green : Colors.red }]}>
        {isIncome ? '+' : '-'}{fmt(item.amount)}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    gap: 12,
  },
  iconBox: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: Colors.bgInput,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconText: {
    fontSize: 20,
  },
  info: {
    flex: 1,
    gap: 3,
  },
  desc: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  meta: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  amount: {
    fontSize: 15,
    fontWeight: '700',
  },
});
