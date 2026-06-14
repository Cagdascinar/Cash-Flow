import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { investments as invApi } from '../services/api';

const TYPES = [
  { key: 'hisse', label: '📉 Hisse' },
  { key: 'fon',   label: '📊 Fon' },
  { key: 'doviz', label: '💵 Döviz' },
  { key: 'altin', label: '🥇 Altın' },
];

export default function InvestmentsScreen() {
  const router = useRouter();
  const [list,    setList]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [modal,   setModal]   = useState(false);

  // Ekle formu
  const [name,    setName]    = useState('');
  const [ticker,  setTicker]  = useState('');
  const [type,    setType]    = useState('hisse');
  const [qty,     setQty]     = useState('');
  const [price,   setPrice]   = useState('');
  const [date,    setDate]    = useState(new Date().toISOString().split('T')[0]);
  const [saving,  setSaving]  = useState(false);

  // TEFAS arama
  const [tefasKod, setTefasKod] = useState('');
  const [tefasRes, setTefasRes] = useState<any>(null);
  const [tefasLoad, setTefasLoad] = useState(false);

  // Gelir kayıt modali
  const [incomeModal, setIncomeModal]   = useState(false);
  const [incomeTarget, setIncomeTarget] = useState<any>(null);
  const [incomeAmt,    setIncomeAmt]    = useState('');
  const [incomeDate,   setIncomeDate]   = useState(new Date().toISOString().split('T')[0]);
  const [incomeNote,   setIncomeNote]   = useState('');
  const [savingIncome, setSavingIncome] = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const [d, val] = await Promise.all([invApi.list(), invApi.value().catch(() => null)]);
      const valMap: Record<number, number> = {};
      if (val?.investments) {
        (val.investments as any[]).forEach((v: any) => { valMap[v.id] = v.current_value; });
      }
      const merged = (Array.isArray(d) ? d : []).map((i: any) => ({
        ...i,
        current_value: valMap[i.id] ?? i.current_value ?? (i.quantity * i.buy_price),
      }));
      setList(merged);
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function searchTefas() {
    if (!tefasKod.trim()) return;
    setTefasLoad(true); setTefasRes(null);
    try {
      const d = await invApi.tefas(tefasKod.trim().toUpperCase());
      setTefasRes(d);
      if (d?.name) { setName(d.name); setType('fon'); }
      if (d?.price) setPrice(String(d.price));
    } catch { Alert.alert('Hata', 'Fon bulunamadı'); }
    finally { setTefasLoad(false); }
  }

  async function save() {
    const q = parseFloat(qty.replace(',', '.'));
    const p = parseFloat(price.replace(',', '.'));
    if (!name.trim() || !q || !p) { Alert.alert('Hata', 'İsim, miktar ve fiyat gerekli'); return; }
    setSaving(true);
    try {
      await invApi.create({ name: name.trim(), symbol: ticker.trim().toUpperCase(), itype: type, quantity: q, buy_price: p, buy_date: date });
      setModal(false);
      setName(''); setTicker(''); setQty(''); setPrice(''); setTefasKod(''); setTefasRes(null);
      load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function sellOrDelete(id: number) {
    Alert.alert('İşlem', 'Ne yapmak istiyorsunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: '💰 Sat', onPress: () => {
        Alert.prompt('Satış Fiyatı', 'Birim satış fiyatı (₺)', async (val) => {
          if (!val) return;
          const sp = parseFloat(val.replace(',', '.'));
          if (!sp || sp <= 0) { Alert.alert('Hata', 'Geçerli fiyat girin'); return; }
          try {
            await invApi.sell(id, { sell_price: sp, sell_date: new Date().toISOString().split('T')[0] });
            Alert.alert('✅ Satış Yapıldı');
            load();
          } catch (e: any) { Alert.alert('Hata', e.message); }
        });
      }},
      { text: '💵 Gelir Kaydet', onPress: () => {
        const inv = list.find(i => i.id === id);
        setIncomeTarget(inv); setIncomeAmt(''); setIncomeNote('');
        setIncomeModal(true);
      }},
      { text: '🗑️ Sil', style: 'destructive', onPress: async () => {
        try { await invApi.delete(id); setList(p => p.filter(i => i.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  async function saveIncome() {
    const amt = parseFloat(incomeAmt.replace(',', '.'));
    if (!amt || amt <= 0) { Alert.alert('Hata', 'Geçerli tutar girin'); return; }
    setSavingIncome(true);
    try {
      await invApi.bookIncome(incomeTarget.id, { amount: amt, date: incomeDate, note: incomeNote.trim() });
      setIncomeModal(false);
      Alert.alert('✅ Gelir kaydedildi');
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSavingIncome(false); }
  }

  const totalValue = list.reduce((s, i) => s + (i.current_value ?? 0), 0);
  const totalCost  = list.reduce((s, i) => s + (i.quantity * i.buy_price), 0);
  const pnl        = totalValue - totalCost;

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Yatırımlar</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => setModal(true)}>
          <Text style={s.addTxt}>+ Ekle</Text>
        </TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>

            {list.length > 0 && (
              <View style={s.summaryCard}>
                <View style={s.sumRow}>
                  <View style={s.sumItem}>
                    <Text style={s.sumLbl}>Portföy Değeri</Text>
                    <Text style={[s.sumVal, { color: C.blue }]}>{money(totalValue)}</Text>
                  </View>
                  <View style={s.sumDiv} />
                  <View style={s.sumItem}>
                    <Text style={s.sumLbl}>Maliyet</Text>
                    <Text style={s.sumVal}>{money(totalCost)}</Text>
                  </View>
                  <View style={s.sumDiv} />
                  <View style={s.sumItem}>
                    <Text style={s.sumLbl}>Kar / Zarar</Text>
                    <Text style={[s.sumVal, { color: pnl >= 0 ? C.green : C.red }]}>
                      {pnl >= 0 ? '+' : ''}{money(pnl)}
                    </Text>
                  </View>
                </View>
              </View>
            )}

            {list.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>📈</Text><Text style={s.emptyTxt}>Yatırım eklenmedi</Text></View>
              : list.map(inv => {
                  const currentVal = inv.current_value ?? (inv.quantity * inv.buy_price);
                  const cost       = inv.quantity * inv.buy_price;
                  const gain       = currentVal - cost;
                  const pct        = cost > 0 ? ((gain / cost) * 100) : 0;
                  return (
                    <TouchableOpacity key={inv.id} style={s.card} onLongPress={() => sellOrDelete(inv.id)} onPress={() => sellOrDelete(inv.id)}>
                      <View style={s.cardTop}>
                        <View style={{ flex: 1 }}>
                          <Text style={s.invName}>{inv.name} {inv.ticker ? `(${inv.ticker})` : ''}</Text>
                          <Text style={s.invType}>{inv.inv_type ?? inv.itype} · {inv.quantity} adet</Text>
                        </View>
                        <Text style={{ color: C.muted, fontSize: 20, paddingLeft: 8 }}>⋯</Text>
                      </View>
                      <View style={s.cardBot}>
                        <View>
                          <Text style={s.botLbl}>Maliyet</Text>
                          <Text style={s.botVal}>{money(cost)}</Text>
                        </View>
                        <View>
                          <Text style={s.botLbl}>Güncel Değer</Text>
                          <Text style={s.botVal}>{money(currentVal)}</Text>
                        </View>
                        <View>
                          <Text style={s.botLbl}>Kar/Zarar</Text>
                          <Text style={[s.botVal, { color: gain >= 0 ? C.green : C.red }]}>
                            {gain >= 0 ? '+' : ''}{money(gain)} (%{Math.abs(pct).toFixed(1)})
                          </Text>
                        </View>
                      </View>
                    </TouchableOpacity>
                  );
                })
            }
            <View style={{ height: 40 }} />
          </ScrollView>
      }

      {/* Yatırım Ekle Modal */}
      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.modal} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
              <View style={s.mHeader}>
                <Text style={s.mTitle}>Yatırım Ekle</Text>
                <TouchableOpacity onPress={() => { setModal(false); setTefasRes(null); setTefasKod(''); }}><Text style={s.close}>✕</Text></TouchableOpacity>
              </View>

              {/* TEFAS Arama */}
              <View style={s.mField}>
                <Text style={s.mLbl}>TEFAS Fon Kodu ile Ara</Text>
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  <TextInput
                    style={[s.mInput, { flex: 1 }]} value={tefasKod} onChangeText={setTefasKod}
                    placeholder="YAB, TI2..." placeholderTextColor={C.muted}
                    autoCapitalize="characters"
                  />
                  <TouchableOpacity style={s.searchBtn} onPress={searchTefas} disabled={tefasLoad}>
                    {tefasLoad ? <ActivityIndicator color={C.white} size="small" /> : <Text style={s.searchTxt}>Ara</Text>}
                  </TouchableOpacity>
                </View>
                {tefasRes && (
                  <View style={s.tefasResult}>
                    <Text style={s.tefasName}>{tefasRes.name}</Text>
                    {tefasRes.price && <Text style={s.tefasPrice}>Güncel Fiyat: ₺{tefasRes.price}</Text>}
                  </View>
                )}
              </View>

              {[
                { lbl: 'Yatırım Adı *', val: name, set: setName, ph: 'Apple, Bitcoin...' },
                { lbl: 'Sembol/Ticker', val: ticker, set: setTicker, ph: 'AAPL, BTC' },
                { lbl: 'Miktar *', val: qty, set: setQty, ph: '10', kb: 'decimal-pad' as const },
                { lbl: 'Alış Fiyatı (₺) *', val: price, set: setPrice, ph: '1500', kb: 'decimal-pad' as const },
                { lbl: 'Alış Tarihi', val: date, set: setDate, ph: 'YYYY-MM-DD' },
              ].map(({ lbl, val, set, ph, kb }) => (
                <View key={lbl} style={s.mField}>
                  <Text style={s.mLbl}>{lbl}</Text>
                  <TextInput style={s.mInput} value={val} onChangeText={set} placeholder={ph} placeholderTextColor={C.muted} keyboardType={kb} />
                </View>
              ))}

              <View style={s.mField}>
                <Text style={s.mLbl}>Yatırım Tipi</Text>
                <View style={s.typeGrid}>
                  {TYPES.map(t => (
                    <TouchableOpacity key={t.key} style={[s.typeBtn, type === t.key && s.typeA]} onPress={() => setType(t.key)}>
                      <Text style={[s.typeTxt, type === t.key && { color: C.white }]}>{t.label}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>📈 Yatırımı Ekle</Text>}
              </TouchableOpacity>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>

      {/* Gelir Kayıt Modal */}
      <Modal visible={incomeModal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.modal} edges={['top']}>
          <View style={s.mHeader}>
            <Text style={s.mTitle}>Gelir Kaydet</Text>
            <TouchableOpacity onPress={() => setIncomeModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
          </View>
          <View style={{ padding: 16 }}>
            {incomeTarget && <Text style={{ fontSize: 14, color: C.txt2, marginBottom: 16 }}>{incomeTarget.name} için temettü / kira / faiz geliri</Text>}
            <Text style={s.mLbl}>Tutar (₺)</Text>
            <TextInput style={[s.mInput, { marginBottom: 14 }]} value={incomeAmt} onChangeText={setIncomeAmt} placeholder="0,00" placeholderTextColor={C.muted} keyboardType="decimal-pad" />
            <Text style={s.mLbl}>Tarih</Text>
            <TextInput style={[s.mInput, { marginBottom: 14 }]} value={incomeDate} onChangeText={setIncomeDate} placeholder="YYYY-MM-DD" placeholderTextColor={C.muted} />
            <Text style={s.mLbl}>Not</Text>
            <TextInput style={[s.mInput, { marginBottom: 24 }]} value={incomeNote} onChangeText={setIncomeNote} placeholder="Temettü, kira..." placeholderTextColor={C.muted} />
            <TouchableOpacity style={[s.saveBtn, savingIncome && { opacity: 0.6 }]} onPress={saveIncome} disabled={savingIncome}>
              {savingIncome ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>💵 Geliri Kaydet</Text>}
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: C.bg },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:      { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:        { fontSize: 24, color: C.txt },
  title:       { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  addBtn:      { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 7 },
  addTxt:      { fontSize: 14, fontWeight: '700', color: C.white },
  summaryCard: { margin: 16, backgroundColor: C.hero, borderRadius: 16, padding: 16, borderWidth: 1, borderColor: 'rgba(99,160,255,.15)' },
  sumRow:      { flexDirection: 'row', alignItems: 'center' },
  sumItem:     { flex: 1, alignItems: 'center' },
  sumLbl:      { fontSize: 11, color: 'rgba(255,255,255,.45)', marginBottom: 4 },
  sumVal:      { fontSize: 15, fontWeight: '800', color: C.txt },
  sumDiv:      { width: 1, height: 36, backgroundColor: 'rgba(255,255,255,.1)', marginHorizontal: 8 },
  card:        { marginHorizontal: 16, marginBottom: 10, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  cardTop:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 },
  invName:     { fontSize: 15, fontWeight: '700', color: C.txt },
  invType:     { fontSize: 12, color: C.txt2, marginTop: 2 },
  cardBot:     { flexDirection: 'row', justifyContent: 'space-between' },
  botLbl:      { fontSize: 11, color: C.muted },
  botVal:      { fontSize: 13, fontWeight: '700', color: C.txt, marginTop: 2 },
  empty:       { alignItems: 'center', paddingVertical: 48 },
  emptyIco:    { fontSize: 48, marginBottom: 12 },
  emptyTxt:    { fontSize: 15, color: C.txt2 },
  modal:       { flex: 1, backgroundColor: C.bg },
  mHeader:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8 },
  mTitle:      { fontSize: 20, fontWeight: '800', color: C.txt },
  close:       { fontSize: 20, color: C.muted },
  mField:      { marginHorizontal: 16, marginTop: 16, gap: 6 },
  mLbl:        { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  mInput:      { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  typeGrid:    { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  typeBtn:     { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: C.input, borderWidth: 1, borderColor: C.border },
  typeA:       { backgroundColor: C.blue, borderColor: C.blue },
  typeTxt:     { fontSize: 13, color: C.txt2 },
  saveBtn:     { margin: 16, marginTop: 24, marginBottom: 32, backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  saveTxt:     { fontSize: 16, fontWeight: '700', color: C.white },
  searchBtn:   { backgroundColor: C.blue, borderRadius: 12, paddingHorizontal: 16, justifyContent: 'center' },
  searchTxt:   { fontSize: 14, fontWeight: '700', color: C.white },
  tefasResult: { backgroundColor: C.input, borderRadius: 10, padding: 12, marginTop: 8 },
  tefasName:   { fontSize: 13, fontWeight: '600', color: C.txt },
  tefasPrice:  { fontSize: 12, color: C.green, marginTop: 4 },
});
