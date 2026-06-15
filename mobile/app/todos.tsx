import {
  View, Text, FlatList, StyleSheet, TextInput, TouchableOpacity,
  Alert, ActivityIndicator, RefreshControl,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { misc } from '../services/api';
import { SwipeableRow } from '../components/SwipeableRow';

function fmtDate(d: Date) {
  return d.toISOString().split('T')[0];
}

function dayLabel(d: Date) {
  const today = new Date(); today.setHours(0,0,0,0);
  const target = new Date(d); target.setHours(0,0,0,0);
  const diff = Math.round((target.getTime() - today.getTime()) / 86400000);
  if (diff === 0) return 'Bugün';
  if (diff === -1) return 'Dün';
  if (diff === 1) return 'Yarın';
  return d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' });
}

export default function TodosScreen() {
  const router = useRouter();
  const [date,    setDate]    = useState(new Date());
  const [todos,   setTodos]   = useState<any[]>([]);
  const [text,    setText]    = useState('');
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [adding,  setAdding]  = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const d = await misc.todos(fmtDate(date)) as any;
      setTodos(Array.isArray(d) ? d : (d.todos ?? []));
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, [date]);

  useEffect(() => { load(); }, [load]);

  function changeDay(delta: number) {
    const d = new Date(date);
    d.setDate(d.getDate() + delta);
    setDate(d);
  }

  async function add() {
    if (!text.trim()) return;
    setAdding(true);
    try {
      await misc.addTodo({ text: text.trim(), date: fmtDate(date) });
      setText('');
      load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setAdding(false); }
  }

  async function toggle(id: number, done: boolean) {
    try {
      await misc.updateTodo(id, { done: done ? 0 : 1 });
      setTodos(prev => prev.map(t => t.id === id ? { ...t, done: done ? 0 : 1 } : t));
    } catch {}
  }

  async function del(id: number) {
    try {
      await misc.deleteTodo(id);
      setTodos(prev => prev.filter(t => t.id !== id));
    } catch (e: any) { Alert.alert('Hata', e.message); }
  }

  const active   = todos.filter(t => !t.done && !t.archived);
  const done     = todos.filter(t => t.done);

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Yapılacaklar</Text>
      </View>

      {/* Tarih navigator */}
      <View style={s.dateNav}>
        <TouchableOpacity style={s.dayBtn} onPress={() => changeDay(-1)}>
          <Text style={s.dayBtnTxt}>‹</Text>
        </TouchableOpacity>
        <Text style={s.dayLabel}>{dayLabel(date)}</Text>
        <TouchableOpacity style={s.dayBtn} onPress={() => changeDay(1)}>
          <Text style={s.dayBtnTxt}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Add input */}
      <View style={s.addRow}>
        <TextInput
          style={s.addInput}
          placeholder="Yapılacak ekle..."
          placeholderTextColor={C.muted}
          value={text}
          onChangeText={setText}
          onSubmitEditing={add}
          returnKeyType="done"
        />
        <TouchableOpacity style={[s.addBtn, adding && { opacity: 0.6 }]} onPress={add} disabled={adding}>
          {adding ? <ActivityIndicator color={C.white} size="small" /> : <Text style={s.addBtnTxt}>+</Text>}
        </TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <FlatList
            data={[...active, ...done]}
            keyExtractor={item => String(item.id)}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}
            contentContainerStyle={{ paddingBottom: 24 }}
            ListHeaderComponent={active.length === 0 && done.length === 0 ? (
              <View style={s.empty}><Text style={s.emptyIco}>✅</Text><Text style={s.emptyTxt}>Bu gün için yapılacak yok</Text></View>
            ) : null}
            renderItem={({ item }) => (
              <SwipeableRow
                style={{ marginHorizontal: 16, marginTop: 10, borderRadius: 12 }}
                actions={[{ label: 'Sil', icon: '🗑️', color: '#dc2626', onPress: () => del(item.id) }]}
              >
                <TouchableOpacity style={s.item} onPress={() => toggle(item.id, !!item.done)} activeOpacity={0.7}>
                  <View style={[s.checkbox, item.done && s.checkboxDone]}>
                    {item.done && <Text style={s.checkmark}>✓</Text>}
                  </View>
                  <Text style={[s.itemText, item.done && s.itemDone]}>{item.text}</Text>
                </TouchableOpacity>
              </SwipeableRow>
            )}
          />
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  center:    { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:    { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:      { fontSize: 24, color: C.txt },
  title:     { fontSize: 20, fontWeight: '800', color: C.txt },
  dateNav:   { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginHorizontal: 16, marginTop: 12, backgroundColor: C.card, borderRadius: 14, padding: 4, borderWidth: 1, borderColor: C.border },
  dayBtn:    { padding: 10 },
  dayBtnTxt: { fontSize: 22, color: C.txt, fontWeight: '700' },
  dayLabel:  { fontSize: 16, fontWeight: '700', color: C.txt },
  addRow:    { flexDirection: 'row', marginHorizontal: 16, marginTop: 12, gap: 8 },
  addInput:  { flex: 1, backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  addBtn:    { width: 48, height: 48, backgroundColor: C.blue, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
  addBtnTxt: { fontSize: 24, color: C.white, fontWeight: '300' },
  item:      { flexDirection: 'row', alignItems: 'center', backgroundColor: C.card, borderRadius: 12, padding: 14, borderWidth: 1, borderColor: C.border, gap: 12 },
  checkbox:  { width: 22, height: 22, borderRadius: 6, borderWidth: 2, borderColor: C.border, alignItems: 'center', justifyContent: 'center' },
  checkboxDone: { backgroundColor: C.green, borderColor: C.green },
  checkmark: { fontSize: 12, color: C.white, fontWeight: '800' },
  itemText:  { flex: 1, fontSize: 15, color: C.txt },
  itemDone:  { color: C.muted, textDecorationLine: 'line-through' },
  empty:     { alignItems: 'center', paddingVertical: 48 },
  emptyIco:  { fontSize: 48, marginBottom: 12 },
  emptyTxt:  { fontSize: 15, color: C.txt2 },
});
