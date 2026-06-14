import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money, fmtDate } from '../constants/Colors';
import { scheduled as schedApi } from '../services/api';

type StatusTab = 'bekliyor' | 'yapildi' | 'hepsi';

function todayISO() { return new Date().toISOString().slice(0, 10); }

export default function ScheduledScreen() {
  const router = useRouter();
  const [tab,     setTab]     = useState<StatusTab>('bekliyor');
  const [list,    setList]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [modal,   setModal]   = useState(false);
  const [saving,  setSaving]  = useState(false);

  const [type,    setType]    = useState<'gider'|'gelir'>('gider');
  const [amount,  setAmount]  = useState('');
  const [date,    setDate]    = useState(todayISO());
  const [cat,     setCat]     = useState('');
  const [desc,    setDesc]    = useState('');

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const status = tab === 'hepsi' ? undefined : tab;
      setList((await schedApi.list(status)) || []);
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, [tab]);

  useEffect(() => { load(); }, [load]);

  function resetForm() { setType('gider'); setAmount(''); setDate(todayISO()); setCat(''); setDesc(''); }

  async function save() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!amt || !date) { Alert.alert('Hata', 'Tutar ve tarih zorunlu'); return; }
    setSaving(true);
    try {
      await schedApi.create({ type, amount: amt, scheduled_date: date, category: cat.trim(), description: desc.trim() });
      setModal(false); resetForm(); load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function execute(item: any) {
    Alert.alert('Uygula', `"${item.description || item.category}" işlemi bugün için eklensin mi?`, [
      { text: 'İptal', style: 'cancel' },
      { text: 'Uygula', onPress: async () => {
        try { await schedApi.execute(item.id); load(); Alert.alert('✓', 'İşlem eklendi'); }
        catch (e: any) { Alert.alert('Hata', (e as any).message); }
      }},
    ]);
  }

  async function del(id: number) {
    Alert.alert('Sil', 'Bu planlanmış işlem silinsin mi?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await schedApi.delete(id); setList(p => p.filter(x => x.id !== id)); }
        catch (e: any) { Alert.alert('Hata', (e as any).message); }
      }},
    ]);
  }

  function isOverdue(item: any) {
    return item.status === 'bekliyor' && item.scheduled_date < todayISO();
  }

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Planlanmış</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => { resetForm(); setModal(true); }}>
          <Text style={s.addTxt}>+ Ekle</Text>
        </TouchableOpacity>
      </View>

      {/* Tab */}
      <View style={s.tabRow}>
        {([['bekliyor','Bekliyor'],['yapildi','Yapıldı'],['hepsi','Hepsi']] as [StatusTab,string][]).map(([k,l]) => (
          <TouchableOpacity key={k} style={[s.tabBtn, tab===k && s.tabBtnA]} onPress={() => setTab(k)}>
            <Text style={[s.tabTxt, tab===k && s.tabTxtA]}>{l}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>
            {list.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>📅</Text><Text style={s.emptyTxt}>Planlanmış işlem yok</Text></View>
              : list.map(item => {
                  const overdue = isOverdue(item);
                  return (
                    <View key={item.id} style={[s.card, overdue && s.cardOverdue]}>
                      <View style={[s.typeDot, { backgroundColor: item.type === 'gelir' ? C.green : C.red }]} />
                      <View style={{ flex: 1 }}>
                        <Text style={s.desc} numberOfLines={1}>{item.description || item.category || '—'}</Text>
                        <Text style={[s.date, overdue && { color: C.red }]}>
                          {overdue ? '⚠️ ' : '📅 '}{fmtDate(item.scheduled_date)}
                          {item.category ? ` · ${item.category}` : ''}
                        </Text>
                      </View>
                      <Text style={[s.amount, { color: item.type === 'gelir' ? C.green : C.red }]}>
                        {money(item.amount)}
                      </Text>
                      {item.status === 'bekliyor' && (
                        <TouchableOpacity style={s.execBtn} onPress={() => execute(item)}>
                          <Text style={s.execTxt}>▶</Text>
                        </TouchableOpacity>
                      )}
                      {item.status === 'yapildi' && (
                        <View style={s.doneBadge}><Text style={s.doneTxt}>✓</Text></View>
                      )}
                      <TouchableOpacity onPress={() => del(item.id)}>
                        <Text style={{ color: C.muted, fontSize: 16 }}>✕</Text>
                      </TouchableOpacity>
                    </View>
                  );
                })
            }
            <View style={{ height: 40 }} />
          </ScrollView>
      }

      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Planlanmış İşlem</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }}>
              <Text style={s.mLbl}>Tür</Text>
              <View style={{ flexDirection: 'row', gap: 10, marginBottom: 14 }}>
                {(['gider','gelir'] as const).map(t => (
                  <TouchableOpacity key={t} style={[s.typeBtn, type===t && s.typeBtnA]} onPress={() => setType(t)}>
                    <Text style={[s.typeBtnT, type===t && { color: C.white }]}>
                      {t === 'gider' ? '↓ Gider' : '↑ Gelir'}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={s.mLbl}>Tutar (₺) *</Text>
              <TextInput style={s.mInput} value={amount} onChangeText={setAmount}
                placeholder="1500,00" placeholderTextColor={C.muted} keyboardType="decimal-pad" />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Planlanan Tarih *</Text>
              <TextInput style={s.mInput} value={date} onChangeText={setDate}
                placeholder="YYYY-AA-GG" placeholderTextColor={C.muted} />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Kategori</Text>
              <TextInput style={s.mInput} value={cat} onChangeText={setCat}
                placeholder="Kira, Market..." placeholderTextColor={C.muted} />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Açıklama</Text>
              <TextInput style={s.mInput} value={desc} onChangeText={setDesc}
                placeholder="İsteğe bağlı" placeholderTextColor={C.muted} />

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>📅 Kaydet</Text>}
              </TouchableOpacity>
              <View style={{ height: 40 }} />
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:          { flex: 1, backgroundColor: C.bg },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:      { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:        { fontSize: 24, color: C.txt },
  title:       { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  addBtn:      { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 7 },
  addTxt:      { fontSize: 14, fontWeight: '700', color: C.white },
  tabRow:      { flexDirection: 'row', marginHorizontal: 16, marginTop: 12, backgroundColor: C.input, borderRadius: 12, padding: 4, gap: 4 },
  tabBtn:      { flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: 'center' },
  tabBtnA:     { backgroundColor: C.card },
  tabTxt:      { fontSize: 13, fontWeight: '600', color: C.txt2 },
  tabTxtA:     { color: C.txt, fontWeight: '700' },
  card:        { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 8, marginTop: 8, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border, gap: 10 },
  cardOverdue: { borderColor: C.red, backgroundColor: 'rgba(246,70,93,0.06)' },
  typeDot:     { width: 10, height: 10, borderRadius: 5, flexShrink: 0 },
  desc:        { fontSize: 15, fontWeight: '600', color: C.txt },
  date:        { fontSize: 12, color: C.txt2, marginTop: 2 },
  amount:      { fontSize: 15, fontWeight: '800' },
  execBtn:     { backgroundColor: C.blue, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
  execTxt:     { color: C.white, fontWeight: '700', fontSize: 14 },
  doneBadge:   { backgroundColor: 'rgba(14,203,129,0.15)', borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4 },
  doneTxt:     { color: C.green, fontWeight: '700', fontSize: 13 },
  empty:       { alignItems: 'center', paddingVertical: 48 },
  emptyIco:    { fontSize: 48, marginBottom: 12 },
  emptyTxt:    { fontSize: 15, color: C.txt2 },
  mHeader:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:      { fontSize: 20, fontWeight: '800', color: C.txt },
  close:       { fontSize: 20, color: C.muted },
  mLbl:        { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:      { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  typeBtn:     { flex: 1, paddingVertical: 12, borderRadius: 12, backgroundColor: C.card, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  typeBtnA:    { backgroundColor: C.blue, borderColor: C.blue },
  typeBtnT:    { fontSize: 14, fontWeight: '700', color: C.txt2 },
  saveBtn:     { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 16 },
  saveTxt:     { fontSize: 16, fontWeight: '700', color: C.white },
});
