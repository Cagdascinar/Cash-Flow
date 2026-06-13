import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { misc as miscApi, transactions as txApi } from '../services/api';

export default function TemplatesScreen() {
  const router = useRouter();
  const [list,    setList]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [modal,   setModal]   = useState(false);
  const [applyModal, setApplyModal] = useState(false);
  const [applying, setApplying]  = useState<any>(null);
  const [saving,  setSaving]  = useState(false);
  const [applyDate, setApplyDate] = useState('');

  const [name,     setName]     = useState('');
  const [type,     setType]     = useState<'gelir'|'gider'>('gider');
  const [amount,   setAmount]   = useState('');
  const [category, setCategory] = useState('');
  const [desc,     setDesc]     = useState('');

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setList((await miscApi.templates() as any[]) || []); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  function todayISO() {
    return new Date().toISOString().slice(0, 10);
  }

  function resetForm() {
    setName(''); setType('gider'); setAmount(''); setCategory(''); setDesc('');
  }

  async function save() {
    if (!name.trim()) { Alert.alert('Hata', 'Ad zorunlu'); return; }
    setSaving(true);
    try {
      await miscApi.addTemplate({
        name: name.trim(), type, amount: parseFloat(amount.replace(',', '.')) || 0,
        category: category.trim(), description: desc.trim(),
      });
      setModal(false); resetForm(); load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function applyTemplate(tpl: any) {
    setApplying(tpl);
    setApplyDate(todayISO());
    setApplyModal(true);
  }

  async function confirmApply() {
    if (!applying) return;
    setSaving(true);
    try {
      await miscApi.applyTemplate(applying.id, { date: applyDate });
      setApplyModal(false);
      Alert.alert('✓', 'İşlem eklendi');
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function del(id: number) {
    Alert.alert('Sil', 'Bu şablon silinsin mi?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await miscApi.deleteTemplate(id); setList(p => p.filter(t => t.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Şablonlar</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => { resetForm(); setModal(true); }}>
          <Text style={s.addTxt}>+ Ekle</Text>
        </TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>
            {list.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>📋</Text><Text style={s.emptyTxt}>Şablon eklenmedi</Text></View>
              : list.map(tpl => (
                  <View key={tpl.id} style={s.card}>
                    <View style={[s.typeDot, { backgroundColor: tpl.type === 'gelir' ? C.green : C.red }]} />
                    <View style={{ flex: 1 }}>
                      <Text style={s.name}>{tpl.name}</Text>
                      <Text style={s.sub}>{tpl.category}{tpl.description ? ` · ${tpl.description}` : ''}</Text>
                    </View>
                    <Text style={[s.amount, { color: tpl.type === 'gelir' ? C.green : C.red }]}>
                      {money(tpl.amount)}
                    </Text>
                    <TouchableOpacity style={s.applyBtn} onPress={() => applyTemplate(tpl)}>
                      <Text style={s.applyTxt}>▶</Text>
                    </TouchableOpacity>
                    <TouchableOpacity onPress={() => del(tpl.id)}><Text style={{ color: C.muted, fontSize: 16 }}>✕</Text></TouchableOpacity>
                  </View>
                ))
            }
            <View style={{ height: 40 }} />
          </ScrollView>
      }

      {/* Uygula Modal */}
      <Modal visible={applyModal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <View style={s.mHeader}>
            <Text style={s.mTitle}>Şablonu Uygula</Text>
            <TouchableOpacity onPress={() => setApplyModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
          </View>
          {applying && (
            <View style={{ padding: 16 }}>
              <View style={s.infoBox}>
                <Text style={s.infoName}>{applying.name}</Text>
                <Text style={s.infoSub}>{applying.category} · {money(applying.amount)} · {applying.type === 'gelir' ? 'Gelir' : 'Gider'}</Text>
              </View>
              <Text style={s.mLbl}>Tarih</Text>
              <TextInput style={s.mInput} value={applyDate} onChangeText={setApplyDate} placeholder="YYYY-AA-GG" />
              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={confirmApply} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>✓ İşlem Ekle</Text>}
              </TouchableOpacity>
            </View>
          )}
        </SafeAreaView>
      </Modal>

      {/* Ekle Modal */}
      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Şablon Ekle</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }}>
              <Text style={s.mLbl}>Ad *</Text>
              <TextInput style={s.mInput} value={name} onChangeText={setName} placeholder="Kira Ödemesi" placeholderTextColor={C.muted} />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Tür</Text>
              <View style={{ flexDirection: 'row', gap: 10 }}>
                {(['gider', 'gelir'] as const).map(t => (
                  <TouchableOpacity key={t} style={[s.typeBtn, type === t && s.typeBtnActive]}
                    onPress={() => setType(t)}>
                    <Text style={[s.typeBtnTxt, type === t && { color: C.white }]}>
                      {t === 'gelir' ? '↑ Gelir' : '↓ Gider'}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={[s.mLbl, { marginTop: 14 }]}>Tutar (₺)</Text>
              <TextInput style={s.mInput} value={amount} onChangeText={setAmount} placeholder="1500,00" placeholderTextColor={C.muted} keyboardType="decimal-pad" />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Kategori</Text>
              <TextInput style={s.mInput} value={category} onChangeText={setCategory} placeholder="Kira" placeholderTextColor={C.muted} />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Açıklama</Text>
              <TextInput style={s.mInput} value={desc} onChangeText={setDesc} placeholder="İsteğe bağlı" placeholderTextColor={C.muted} />

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>📋 Kaydet</Text>}
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
  card:        { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 8, marginTop: 8, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border, gap: 10 },
  typeDot:     { width: 10, height: 10, borderRadius: 5, flexShrink: 0 },
  name:        { fontSize: 15, fontWeight: '700', color: C.txt },
  sub:         { fontSize: 12, color: C.txt2, marginTop: 2 },
  amount:      { fontSize: 15, fontWeight: '800' },
  applyBtn:    { backgroundColor: C.blue, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
  applyTxt:    { color: C.white, fontWeight: '700', fontSize: 14 },
  empty:       { alignItems: 'center', paddingVertical: 48 },
  emptyIco:    { fontSize: 48, marginBottom: 12 },
  emptyTxt:    { fontSize: 15, color: C.txt2 },
  mHeader:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:      { fontSize: 20, fontWeight: '800', color: C.txt },
  close:       { fontSize: 20, color: C.muted },
  mLbl:        { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:      { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  typeBtn:     { flex: 1, paddingVertical: 12, borderRadius: 12, backgroundColor: C.card, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  typeBtnActive:{ backgroundColor: C.blue, borderColor: C.blue },
  typeBtnTxt:  { fontSize: 14, fontWeight: '700', color: C.txt2 },
  infoBox:     { backgroundColor: C.input, borderRadius: 12, padding: 14, marginBottom: 20 },
  infoName:    { fontSize: 16, fontWeight: '700', color: C.txt },
  infoSub:     { fontSize: 13, color: C.txt2, marginTop: 4 },
  saveBtn:     { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 16 },
  saveTxt:     { fontSize: 16, fontWeight: '700', color: C.white },
});
