import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Colors } from '../constants/Colors';

interface Transaction {
  id: number; type: 'gelir' | 'gider';
  amount: number; category: string;
  description?: string; date: string;
}
interface Props { item: Transaction; onPress?: (item: Transaction) => void; onDelete?: (id: number) => void; }

const CAT_ICONS: Record<string, string> = {
  'Maaş':'💼','Serbest Meslek':'💻','Kira Geliri':'🏠',
  'Yatırım Geliri / Satış':'📈','Yatırım / Temettü':'💹',
  'Hediye / İkramiye':'🎁','Diğer Gelir':'💰',
  'Kira / Mortgage':'🏠','Market / Gıda':'🛒','Faturalar':'⚡',
  'Ulaşım':'🚗','Yemek / Restoran':'🍔','Eğlence':'🎬',
  'Sağlık':'❤️','Giyim':'👕','Eğitim':'📚',
  'Abonelikler':'📱','Elektronik':'💡','Sigorta':'🛡️',
  'Vergi / Harç':'🧾','Kredi Kartı Ödemesi':'💳',
  'Yatırım Fonu':'📊','Hisse Senedi':'📉',
  'Döviz Alımı':'💵','Altın Alımı':'🥇',
  'Hesaplar Arası Transfer':'🔄','Diğer Gider':'💸',
};

function fmt(n: number) {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 2 }).format(n);
}

function fmtDate(d: string) {
  return new Date(d).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
}

export function TransactionItem({ item, onPress, onDelete }: Props) {
  const isIncome = item.type === 'gelir';
  const icon = CAT_ICONS[item.category] ?? (isIncome ? '💰' : '💸');

  return (
    <TouchableOpacity
      style={s.item}
      onPress={() => onPress?.(item)}
      activeOpacity={0.7}
    >
      {/* İkon */}
      <View style={[s.iconBox, isIncome ? s.iconGreen : s.iconRed]}>
        <Text style={s.iconTxt}>{icon}</Text>
      </View>

      {/* Bilgi */}
      <View style={s.info}>
        <Text style={s.cat} numberOfLines={1}>{item.category}</Text>
        <Text style={s.desc} numberOfLines={1}>
          {item.description ? item.description : fmtDate(item.date)}
        </Text>
      </View>

      {/* Tutar */}
      <Text style={[s.amount, { color: isIncome ? Colors.green : Colors.red }]}>
        {isIncome ? '+' : '-'}{fmt(item.amount)}
      </Text>
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  item: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 10, paddingHorizontal: 14, gap: 11,
    backgroundColor: Colors.bgCard,
  },
  iconBox: {
    width: 40, height: 40, borderRadius: 12,
    alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
  },
  iconGreen: {
    backgroundColor: 'rgba(34,197,94,.12)',
    borderWidth: 1, borderColor: 'rgba(34,197,94,.2)',
  },
  iconRed: {
    backgroundColor: 'rgba(239,68,68,.12)',
    borderWidth: 1, borderColor: 'rgba(239,68,68,.2)',
  },
  iconTxt: { fontSize: 18 },
  info: { flex: 1, minWidth: 0 },
  cat: { fontSize: 14, fontWeight: '700', color: Colors.textPrimary, letterSpacing: -0.1 },
  desc: { fontSize: 12, color: Colors.textSecondary, marginTop: 2 },
  amount: { fontSize: 15, fontWeight: '800', flexShrink: 0, letterSpacing: -0.3 },
});
