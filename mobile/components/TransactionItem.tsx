import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { C, money, fmtDate } from '../constants/Colors';

export interface Tx {
  id: number; type: 'gelir' | 'gider';
  amount: number; category: string;
  description?: string; date: string;
  project_id?: number | null; project_name?: string | null;
  tags?: string;
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

export function TransactionItem({ item, onPress, onDelete }: {
  item: Tx;
  onPress?: (t: Tx) => void;
  onDelete?: (id: number) => void;
}) {
  const isGelir = item.type === 'gelir';
  const icon = ICONS[item.category] ?? (isGelir ? '💰' : '💸');
  const tags = item.tags ? item.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

  return (
    <TouchableOpacity style={s.item} onPress={() => onPress?.(item)} activeOpacity={0.7}>
      <View style={[s.iconBox, isGelir ? s.greenBox : s.redBox]}>
        <Text style={s.icon}>{icon}</Text>
      </View>
      <View style={s.info}>
        <Text style={s.cat} numberOfLines={1}>{item.category}</Text>
        <View style={s.metaRow}>
          <Text style={s.sub} numberOfLines={1}>
            {item.description || fmtDate(item.date)}
          </Text>
          {item.project_name && (
            <View style={s.projBadge}>
              <Text style={s.projTxt}>📁 {item.project_name}</Text>
            </View>
          )}
          {tags.length > 0 && tags.slice(0, 2).map(t => (
            <View key={t} style={s.tagBadge}>
              <Text style={s.tagTxt}>{t}</Text>
            </View>
          ))}
        </View>
      </View>
      <Text style={[s.amount, { color: isGelir ? '#4ade80' : '#f87171' }]}>
        {isGelir ? '+' : '-'}{money(item.amount, 2)}
      </Text>
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  item:      { flexDirection: 'row', alignItems: 'center', paddingVertical: 11, paddingHorizontal: 14, gap: 12, backgroundColor: C.card },
  iconBox:   { width: 42, height: 42, borderRadius: 12, alignItems: 'center', justifyContent: 'center', borderWidth: 1, flexShrink: 0 },
  greenBox:  { backgroundColor: 'rgba(74,222,128,.08)', borderColor: 'rgba(74,222,128,.2)' },
  redBox:    { backgroundColor: 'rgba(248,113,113,.08)', borderColor: 'rgba(248,113,113,.2)' },
  icon:      { fontSize: 19 },
  info:      { flex: 1, minWidth: 0 },
  cat:       { fontSize: 14, fontWeight: '700', color: C.txt },
  metaRow:   { flexDirection: 'row', alignItems: 'center', gap: 4, flexWrap: 'wrap', marginTop: 2 },
  sub:       { fontSize: 12, color: C.txt2 },
  projBadge: { backgroundColor: 'rgba(0,122,255,.12)', borderRadius: 6, paddingHorizontal: 5, paddingVertical: 1 },
  projTxt:   { fontSize: 10, color: '#60a5fa', fontWeight: '600' },
  tagBadge:  { backgroundColor: C.input, borderRadius: 6, paddingHorizontal: 5, paddingVertical: 1 },
  tagTxt:    { fontSize: 10, color: C.txt2, fontWeight: '500' },
  amount:    { fontSize: 14, fontWeight: '800', letterSpacing: -0.3 },
});
