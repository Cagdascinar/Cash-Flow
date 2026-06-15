import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { recurring as recurringApi } from '../services/api';
import { SwipeableRow } from '../components/SwipeableRow';

const GELIR = ['Maaş','Serbest Meslek','Kira Geliri','Yatırım Geliri / Satış','Diğer Gelir'];
const GIDER = ['Kira / Mortgage','Faturalar','Abonelikler','Sigorta','Kredi Kartı Ödemesi','Diğer Gider'];
const FREQ  = [{ key: 'monthly', label: 'Aylık' }, { key: 'weekly', label: 'Haftalık' }, { key: 'daily', label: 'Günlük' }];

export default function RecurringScreen() {
  const router = useRouter();
  const [list,    setList]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [modal,   setModal]   = useState(false);

  // Form state
  const [editTarget, setEditTarget] = useState<any>(null);
  const [type,    setType]    = useState<'gider'|'gelir'>('gider');
  const [amount,  setAmount]  = useState('');
  const [desc,    setDesc]    = useState('');
  const [cat,     setCat]     = useState(GIDER[0]);
  const [day,     setDay]     = useState('1');
  const [saving,  setSaving]  = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setList(await recurringApi.list() as any[]); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  function openEdit(r: any) {
    setEditTarget(r);
    setType(r.type);
    setAmount(String(r.amount));
    setDesc(r.description ?? '');
    setCat(r.category);
    setDay(String(r.day_of_month ?? 1));
    setModal(true);
  }

  function openNew() {
    setEditTarget(null);
    setType('gider'); setAmount(''); setDesc(''); setCat(GIDER[0]); setDay('1');
    setModal(true);
  }

  async function save() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!amt || amt <= 0) { Alert.alert('Hata', 'Geçerli tutar girin'); return; }
    setSaving(true);
    try {
      if (editTarget) {
        await recurringApi.update(editTarget.id, { type, amount: amt, description: desc.trim(), category: cat, day_of_month: parseInt(day) || 1 });
        setList(p => p.map(r => r.id === editTarget.id ? { ...r, type, amount: amt, description: desc.trim(), category: cat, day_of_month: parseInt(day) || 1 } : r));
      } else {
        await recurringApi.create({ type, amount: amt, description: desc.trim(), category: cat, day_of_month: parseInt(day) || 1 });
      }
      setModal(false);
      setAmount(''); setDesc('');
      if (!editTarget) load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function del(id: number) {
    Alert.alert('Sil', 'Bu tekrarlayan işlemi silmek istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await recurringApi.delete(id); setList(p => p.filter(r => r.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Tekrarlayan İşlemler</Text>
        <TouchableOpacity style={s.addBtn} onPress={openNew}>
          <Text style={s.addTxt}>+ Ekle</Text>
        </TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>
            {list.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>🔄</Text><Text style={s.emptyTxt}>Tekrarlayan işlem yok</Text></View>
              : list.map(r => (
                  <SwipeableRow
                    key={r.id}
                    style={{ marginHorizontal: 16, marginBottom: 10, borderRadius: 14 }}
                    actions={[
                      { label: 'Düzenle', icon: '✏️', color: '#2563eb', onPress: () => openEdit(r) },
                      { label: 'Sil',     icon: '🗑️', color: '#dc2626', onPress: () => del(r.id) },
                    ]}
                  >
                    <View style={s.card}>
                      <View style={s.cardLeft}>
                        <View style={[s.dot, { backgroundColor: r.type === 'gelir' ? C.green : C.red }]} />
                        <View>
                          <Text style={s.cardTitle}>{r.category}</Text>
                          <Text style={s.cardSub}>{r.description || ''} · {FREQ.find(f => f.key === r.frequency)?.label ?? r.frequency}</Text>
                        </View>
                      </View>
                      <View style={s.cardRight}>
                        <Text style={[s.amount, { color: r.type === 'gelir' ? C.green : C.red }]}>
                          {r.type === 'gelir' ? '+' : '-'}{money(r.amount)}
                        </Text>
                      </View>
                    </View>
                  </SwipeableRow>
                ))
            }
            <View style={{ height: 40 }} />
          </ScrollView>
      }

      {/* Ekle Modal */}
      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.modal} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
              <View style={s.modalHeader}>
                <Text style={s.modalTitle}>{editTarget ? 'Tekrarlayan Düzenle' : 'Tekrarlayan Ekle'}</Text>
                <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
              </View>

              <View style={s.toggle}>
                {(['gider','gelir'] as const).map(t => (
                  <TouchableOpacity key={t} style={[s.tBtn, type === t && (t === 'gelir' ? s.tGreen : s.tRed)]}
                    onPress={() => { setType(t); setCat(t === 'gelir' ? GELIR[0] : GIDER[0]); }}>
                    <Text style={[s.tTxt, type === t && { color: C.white }]}>{t === 'gelir' ? '↑ Gelir' : '↓ Gider'}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <View style={s.mField}>
                <Text style={s.mLbl}>Tutar (₺)</Text>
                <TextInput style={s.mInput} value={amount} onChangeText={setAmount} placeholder="0,00" placeholderTextColor={C.muted} keyboardType="decimal-pad" />
              </View>

              <View style={s.mField}>
                <Text style={s.mLbl}>Açıklama</Text>
                <TextInput style={s.mInput} value={desc} onChangeText={setDesc} placeholder="İsteğe bağlı" placeholderTextColor={C.muted} />
              </View>

              <View style={s.mField}>
                <Text style={s.mLbl}>Ödeme Günü (1-31)</Text>
                <TextInput style={s.mInput} value={day} onChangeText={setDay} placeholder="1" placeholderTextColor={C.muted} keyboardType="number-pad" />
              </View>

              <View style={s.mField}>
                <Text style={s.mLbl}>Kategori</Text>
                <View style={s.catGrid}>
                  {(type === 'gelir' ? GELIR : GIDER).map(c => (
                    <TouchableOpacity key={c} style={[s.catBtn, cat === c && s.catA]} onPress={() => setCat(c)}>
                      <Text style={[s.catTxt, cat === c && { color: C.white }]}>{c}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>Kaydet</Text>}
              </TouchableOpacity>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: C.bg },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:      { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8, gap: 12 },
  back:        { fontSize: 24, color: C.txt },
  title:       { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  addBtn:      { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 7 },
  addTxt:      { fontSize: 14, fontWeight: '700', color: C.white },
  card:        { flexDirection: 'row', alignItems: 'center', backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  cardLeft:    { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 12 },
  dot:         { width: 10, height: 10, borderRadius: 5 },
  cardTitle:   { fontSize: 14, fontWeight: '600', color: C.txt },
  cardSub:     { fontSize: 12, color: C.txt2, marginTop: 2 },
  cardRight:   { flexDirection: 'row', alignItems: 'center', gap: 8 },
  amount:      { fontSize: 14, fontWeight: '800' },
  empty:       { alignItems: 'center', paddingVertical: 48 },
  emptyIco:    { fontSize: 48, marginBottom: 12 },
  emptyTxt:    { fontSize: 15, color: C.txt2 },
  modal:       { flex: 1, backgroundColor: C.bg },
  modalHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 4 },
  modalTitle:  { fontSize: 20, fontWeight: '800', color: C.txt },
  close:       { fontSize: 20, color: C.muted },
  toggle:      { flexDirection: 'row', margin: 16, backgroundColor: C.input, borderRadius: 14, padding: 4, gap: 4 },
  tBtn:        { flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: 'center' },
  tGreen:      { backgroundColor: C.green },
  tRed:        { backgroundColor: C.red },
  tTxt:        { fontSize: 14, fontWeight: '600', color: C.txt2 },
  mField:      { marginHorizontal: 16, marginTop: 16, gap: 6 },
  mLbl:        { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  mInput:      { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  freqRow:     { flexDirection: 'row', gap: 8 },
  freqBtn:     { flex: 1, paddingVertical: 9, borderRadius: 10, backgroundColor: C.card, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  freqA:       { backgroundColor: C.blue, borderColor: C.blue },
  freqTxt:     { fontSize: 13, color: C.txt2 },
  catGrid:     { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  catBtn:      { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: C.input, borderWidth: 1, borderColor: C.border },
  catA:        { backgroundColor: C.blue, borderColor: C.blue },
  catTxt:      { fontSize: 13, color: C.txt2 },
  saveBtn:     { margin: 16, marginTop: 24, marginBottom: 32, backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  saveTxt:     { fontSize: 16, fontWeight: '700', color: C.white },
});
