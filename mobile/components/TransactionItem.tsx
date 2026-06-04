import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { C, money, fmtDate } from '../constants/Colors';

export interface Tx {
  id: number; type: 'gelir' | 'gider';
  amount: number; category: string;
  description?: string; date: string;
}

const ICONS: Record<string, string> = {
  'Maaş':'💼','Serbest Meslek':'💻','Kira Geliri':'🏠',
  'Yatırım Geliri / Satış':'📈','Yatırım / Temettü':'💹',
  'Hediye / İkramiye':'🎁','Hesaplar Arası Transfer':'🔄','Diğer Gelir':'💰',
  'Kira / Mortgage':'🏠','Market / Gıda':'🛒','Faturalar':'⚡',
  'Ulaşım':'🚗','Yemek / Restoran':'🍔','Eğlence':'🎬',
  'Sağlık':'❤️','Giyim':'👕','Eğitim':'📚',
  'Abonelikler':'📱','Elektronik':'💡','Sigorta':'🛡️',
  'Vergi / Harç':'🧾','Kredi Kartı Ödemesi':'💳','Yemek Kartı Ödemesi':'🍽️',
  'Döviz Alımı':'💵','Altın Alımı':'🥇','Yatırım Fonu':'📊','Hisse Senedi':'📉',
  'Diğer Gider':'💸',
};

export function TransactionItem({ item, onPress, onDelete }: { item: Tx; onPress?: (t: Tx) => void; onDelete?: (id: number) => void }) {
  const isGelir = item.type === 'gelir';
  const icon = ICONS[item.category] ?? (isGelir ? '💰' : '💸');
  return (
    <TouchableOpacity style={s.item} onPress={() => onPress?.(item)} activeOpacity={0.7}>
      <View style={[s.iconBox, isGelir ? s.green : s.red]}>
        <Text style={s.icon}>{icon}</Text>
      </View>
      <View style={s.info}>
        <Text style={s.cat} numberOfLines={1}>{item.category}</Text>
        <Text style={s.sub} numberOfLines={1}>{item.description || fmtDate(item.date)}</Text>
      </View>
      <Text style={[s.amount, { color: isGelir ? C.green : C.red }]}>
        {isGelir ? '+' : '-'}{money(item.amount, 2)}
      </Text>
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  item:    { flexDirection: 'row', alignItems: 'center', paddingVertical: 11, paddingHorizontal: 14, gap: 12, backgroundColor: C.card },
  iconBox: { width: 42, height: 42, borderRadius: 12, alignItems: 'center', justifyContent: 'center', borderWidth: 1 },
  green:   { backgroundColor: 'rgba(34,197,94,.1)', borderColor: 'rgba(34,197,94,.25)' },
  red:     { backgroundColor: 'rgba(239,68,68,.1)',  borderColor: 'rgba(239,68,68,.25)' },
  icon:    { fontSize: 19 },
  info:    { flex: 1 },
  cat:     { fontSize: 14, fontWeight: '700', color: C.txt },
  sub:     { fontSize: 12, color: C.txt2, marginTop: 2 },
  amount:  { fontSize: 14, fontWeight: '800', letterSpacing: -0.3 },
});
