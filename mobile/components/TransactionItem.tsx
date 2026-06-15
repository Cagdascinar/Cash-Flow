import { View, Text, StyleSheet, TouchableOpacity, Animated, PanResponder } from 'react-native';
import { useRef } from 'react';
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

const ACTIONS_WIDTH = 140;
const OPEN_THRESHOLD = -60;

export function TransactionItem({ item, onPress, onDelete }: {
  item: Tx;
  onPress?: (t: Tx) => void;
  onDelete?: (id: number) => void;
}) {
  const isGelir = item.type === 'gelir';
  const icon = ICONS[item.category] ?? (isGelir ? '💰' : '💸');
  const tags = item.tags ? item.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

  const x = useRef(new Animated.Value(0)).current;
  const isOpen = useRef(false);

  function snapTo(toValue: number) {
    isOpen.current = toValue !== 0;
    Animated.spring(x, { toValue, useNativeDriver: true, overshootClamping: true }).start();
  }

  const pan = useRef(PanResponder.create({
    onMoveShouldSetPanResponder: (_, g) =>
      Math.abs(g.dx) > 8 && Math.abs(g.dx) > Math.abs(g.dy) * 1.5,
    onPanResponderMove: (_, g) => {
      const base = isOpen.current ? -ACTIONS_WIDTH : 0;
      const next = Math.min(0, Math.max(-ACTIONS_WIDTH, base + g.dx));
      x.setValue(next);
    },
    onPanResponderRelease: (_, g) => {
      if (isOpen.current) {
        snapTo(g.dx > 30 ? 0 : -ACTIONS_WIDTH);
      } else {
        snapTo(g.dx < OPEN_THRESHOLD ? -ACTIONS_WIDTH : 0);
      }
    },
  })).current;

  function handlePress() {
    if (isOpen.current) { snapTo(0); return; }
    onPress?.(item);
  }

  return (
    <View style={s.swipeWrap}>
      {/* Açılan aksiyon butonları */}
      <View style={s.actions}>
        <TouchableOpacity
          style={s.editBtn}
          onPress={() => { snapTo(0); onPress?.(item); }}
          activeOpacity={0.8}
        >
          <Text style={s.actionIcon}>✏️</Text>
          <Text style={s.actionTxt}>Düzenle</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={s.delBtn}
          onPress={() => { snapTo(0); onDelete?.(item.id); }}
          activeOpacity={0.8}
        >
          <Text style={s.actionIcon}>🗑️</Text>
          <Text style={s.actionTxt}>Sil</Text>
        </TouchableOpacity>
      </View>

      {/* Kaydırılabilir işlem satırı */}
      <Animated.View style={{ transform: [{ translateX: x }] }} {...pan.panHandlers}>
        <TouchableOpacity style={s.item} onPress={handlePress} activeOpacity={0.7}>
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
      </Animated.View>
    </View>
  );
}

const s = StyleSheet.create({
  swipeWrap:  { position: 'relative', overflow: 'hidden', backgroundColor: C.card },
  actions:    { position: 'absolute', right: 0, top: 0, bottom: 0, width: ACTIONS_WIDTH, flexDirection: 'row' },
  editBtn:    { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 4, backgroundColor: '#2563eb' },
  delBtn:     { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 4, backgroundColor: '#dc2626' },
  actionIcon: { fontSize: 18 },
  actionTxt:  { fontSize: 11, fontWeight: '700', color: '#fff' },

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
