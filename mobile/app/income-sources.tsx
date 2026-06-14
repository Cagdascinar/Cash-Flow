import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { incomeSources as srcApi } from '../services/api';

const IS_TYPES: Record<string, string> = {
  maas: '💼 Maaş', serbest: '💻 Serbest', kira: '🏠 Kira',
  yatirim: '📈 Yatırım', emekli: '🏛️ Emekli', diger: '💰 Diğer',
};
const IS_FREQ: Record<string, string> = {
  haftalik: 'Haftalık', aylik: 'Aylık', uc_aylik: '3 Aylık',
  alti_aylik: '6 Aylık', yillik: 'Yıllık',
};

export default function IncomeSourcesScreen() {
  const router = useRouter();
  const [list,    setList]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [modal,   setModal]   = useState(false);
  const [saving,  setSaving]  = useState(false);

  const [name,    setName]    = useState('');
  const [type,    setType]    = useState('maas');
  const [amount,  setAmount]  = useState('');
  const [freq,    setFreq]    = useState('aylik');

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setList((await srcApi.list()) || []); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  function resetForm() { setName(''); setType('maas'); setAmount(''); setFreq('aylik'); }

  async function save() {
    if (!name.trim()) { Alert.alert('Hata', 'Ad zorunlu'); return; }
    const amt = parseFloat(amount.replace(',', '.'));
    if (!amt) { Alert.alert('Hata', 'Geçerli bir tutar girin'); return; }
    setSaving(true);
    try {
      await srcApi.create({ name: name.trim(), type, amount: amt, frequency: freq });
      setModal(false); resetForm(); load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function toggle(item: any) {
    try {
      await srcApi.update(item.id, { is_active: item.is_active ? 0 : 1 });
      setList(p => p.map(x => x.id === item.id ? { ...x, is_active: x.is_active ? 0 : 1 } : x));
    } catch (e: any) { Alert.alert('Hata', (e as any).message); }
  }

  async function del(id: number, nm: string) {
    Alert.alert('Sil', `"${nm}" silinsin mi?`, [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await srcApi.delete(id); setList(p => p.filter(x => x.id !== id)); }
        catch (e: any) { Alert.alert('Hata', (e as any).message); }
      }},
    ]);
  }

  const monthly = list
    .filter(x => x.is_active)
    .reduce((s, x) => {
      const m: Record<string, number> = { haftalik: 4.33, aylik: 1, uc_aylik: 1/3, alti_aylik: 1/6, yillik: 1/12 };
      return s + x.amount * (m[x.frequency] ?? 1);
    }, 0);

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Para Kaynakları</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => { resetForm(); setModal(true); }}>
          <Text style={s.addTxt}>+ Ekle</Text>
        </TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>

            {/* Özet */}
            <View style={s.summaryRow}>
              <View style={s.sumCard}>
                <Text style={s.sumVal}>{money(monthly)}</Text>
                <Text style={s.sumLbl}>Aylık Gelir</Text>
              </View>
              <View style={s.sumCard}>
                <Text style={s.sumVal}>{money(monthly * 12)}</Text>
                <Text style={s.sumLbl}>Yıllık Gelir</Text>
              </View>
              <View style={s.sumCard}>
                <Text style={[s.sumVal, { color: C.green }]}>{list.filter(x => x.is_active).length}</Text>
                <Text style={s.sumLbl}>Aktif Kaynak</Text>
              </View>
            </View>

            {list.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>💰</Text><Text style={s.emptyTxt}>Kaynak eklenmedi</Text></View>
              : list.map(item => (
                  <View key={item.id} style={[s.card, !item.is_active && s.cardPassive]}>
                    <View style={s.cardLeft}>
                      <Text style={s.icoTxt}>{IS_TYPES[item.type]?.split(' ')[0] ?? '💰'}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={[s.name, !item.is_active && { color: C.txt2 }]}>{item.name}</Text>
                      <Text style={s.sub}>
                        {IS_FREQ[item.frequency] ?? item.frequency} · {IS_TYPES[item.type]?.split(' ').slice(1).join(' ') ?? item.type}
                      </Text>
                    </View>
                    <View style={{ alignItems: 'flex-end', gap: 6 }}>
                      <Text style={[s.amount, { color: item.is_active ? C.green : C.muted }]}>
                        {money(item.amount)}
                      </Text>
                      <TouchableOpacity style={[s.toggleBtn, item.is_active && s.toggleBtnActive]}
                        onPress={() => toggle(item)}>
                        <Text style={{ color: item.is_active ? C.white : C.txt2, fontSize: 11, fontWeight: '700' }}>
                          {item.is_active ? '● Aktif' : '○ Pasif'}
                        </Text>
                      </TouchableOpacity>
                    </View>
                    <TouchableOpacity onPress={() => del(item.id, item.name)}>
                      <Text style={{ color: C.muted, fontSize: 16 }}>✕</Text>
                    </TouchableOpacity>
                  </View>
                ))
            }
            <View style={{ height: 40 }} />
          </ScrollView>
      }

      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Gelir Kaynağı Ekle</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }}>
              <Text style={s.mLbl}>Ad *</Text>
              <TextInput style={s.mInput} value={name} onChangeText={setName}
                placeholder="Firma Maaşı" placeholderTextColor={C.muted} />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Tür</Text>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 4 }}>
                {Object.entries(IS_TYPES).map(([k, v]) => (
                  <TouchableOpacity key={k} style={[s.chip, type===k && s.chipActive]} onPress={() => setType(k)}>
                    <Text style={[s.chipTxt, type===k && { color: C.white }]}>{v}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={[s.mLbl, { marginTop: 14 }]}>Tutar (₺) *</Text>
              <TextInput style={s.mInput} value={amount} onChangeText={setAmount}
                placeholder="15.000,00" placeholderTextColor={C.muted} keyboardType="decimal-pad" />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Sıklık</Text>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
                {Object.entries(IS_FREQ).map(([k, v]) => (
                  <TouchableOpacity key={k} style={[s.chip, freq===k && s.chipActive]} onPress={() => setFreq(k)}>
                    <Text style={[s.chipTxt, freq===k && { color: C.white }]}>{v}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>💰 Kaydet</Text>}
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
  summaryRow:  { flexDirection: 'row', marginHorizontal: 16, marginTop: 16, gap: 10 },
  sumCard:     { flex: 1, backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  sumVal:      { fontSize: 14, fontWeight: '800', color: C.txt },
  sumLbl:      { fontSize: 10, color: C.txt2, marginTop: 4 },
  card:        { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 8, marginTop: 8, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border, gap: 10 },
  cardPassive: { opacity: 0.5 },
  cardLeft:    { width: 36, height: 36, borderRadius: 10, backgroundColor: C.input, alignItems: 'center', justifyContent: 'center' },
  icoTxt:      { fontSize: 18 },
  name:        { fontSize: 15, fontWeight: '700', color: C.txt },
  sub:         { fontSize: 12, color: C.txt2, marginTop: 2 },
  amount:      { fontSize: 14, fontWeight: '800' },
  toggleBtn:   { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8, backgroundColor: C.input, borderWidth: 1, borderColor: C.border },
  toggleBtnActive: { backgroundColor: C.green, borderColor: C.green },
  empty:       { alignItems: 'center', paddingVertical: 48 },
  emptyIco:    { fontSize: 48, marginBottom: 12 },
  emptyTxt:    { fontSize: 15, color: C.txt2 },
  mHeader:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:      { fontSize: 20, fontWeight: '800', color: C.txt },
  close:       { fontSize: 20, color: C.muted },
  mLbl:        { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:      { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  chip:        { paddingHorizontal: 12, paddingVertical: 8, backgroundColor: C.card, borderRadius: 20, borderWidth: 1, borderColor: C.border },
  chipActive:  { backgroundColor: C.blue, borderColor: C.blue },
  chipTxt:     { fontSize: 13, color: C.txt2 },
  saveBtn:     { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 20 },
  saveTxt:     { fontSize: 16, fontWeight: '700', color: C.white },
});
