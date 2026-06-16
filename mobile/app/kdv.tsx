import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money, fmtDate } from '../constants/Colors';
import { kdv as kdvApi } from '../services/api';
import { SwipeableRow } from '../components/SwipeableRow';

const KDV_RATES = ['1', '8', '10', '18', '20'];
const KDV_TYPES: Record<string, string> = { satis: 'Satış (Tahsil)', alis: 'Alış (İndirilecek)' };

export default function KDVScreen() {
  const router = useRouter();
  const now = new Date();
  const [year,    setYear]    = useState(now.getFullYear());
  const [month,   setMonth]   = useState(now.getMonth() + 1);
  const [summary, setSummary] = useState<any>(null);
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [modal,   setModal]   = useState(false);
  const [saving,  setSaving]  = useState(false);

  const [kdvType, setKdvType] = useState<'satis'|'alis'>('satis');
  const [rate,    setRate]    = useState('18');
  const [base,    setBase]    = useState('');
  const [desc,    setDesc]    = useState('');
  const [txDate,  setTxDate]  = useState(new Date().toISOString().slice(0, 10));

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const [sum, recs] = await Promise.all([
        kdvApi.summary(year, month),
        kdvApi.records(),
      ]);
      setSummary(sum);
      setRecords(Array.isArray(recs) ? recs : []);
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, [year, month]);

  useEffect(() => { load(); }, [load]);

  async function save() {
    if (!base) { Alert.alert('Hata', 'Matrah zorunlu'); return; }
    setSaving(true);
    try {
      await kdvApi.add({
        type: kdvType,
        rate: parseInt(rate),
        base_amount: parseFloat(base.replace(',', '.')),
        description: desc.trim(),
        transaction_date: txDate,
      });
      setModal(false);
      setBase(''); setDesc('');
      load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function del(id: number) {
    Alert.alert('Sil', 'Bu KDV kaydı silinsin mi?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await kdvApi.delete(id); setRecords(p => p.filter(x => x.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  function prevMonth() {
    if (month === 1) { setMonth(12); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  }
  function nextMonth() {
    if (month === 12) { setMonth(1); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  }

  const MONTHS = ['Oca','Şub','Mar','Nis','May','Haz','Tem','Ağu','Eyl','Eki','Kas','Ara'];

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>KDV Takibi</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => setModal(true)}>
          <Text style={s.addTxt}>+ Ekle</Text>
        </TouchableOpacity>
      </View>

      {/* Dönem seçici */}
      <View style={s.periodRow}>
        <TouchableOpacity onPress={prevMonth}><Text style={s.periodArrow}>‹</Text></TouchableOpacity>
        <Text style={s.periodTxt}>{MONTHS[month - 1]} {year}</Text>
        <TouchableOpacity onPress={nextMonth}><Text style={s.periodArrow}>›</Text></TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}
            contentContainerStyle={{ paddingBottom: 40 }}>

            {/* Özet kartları */}
            {summary && (
              <View style={s.summaryGrid}>
                <View style={[s.sumCard, { borderColor: '#166534' }]}>
                  <Text style={[s.sumVal, { color: '#4ade80' }]}>{money(summary.tahsil_edilen ?? 0)}</Text>
                  <Text style={s.sumLbl}>Tahsil Edilen KDV</Text>
                </View>
                <View style={[s.sumCard, { borderColor: '#7c2d12' }]}>
                  <Text style={[s.sumVal, { color: '#f97316' }]}>{money(summary.indirilecek ?? 0)}</Text>
                  <Text style={s.sumLbl}>İndirilecek KDV</Text>
                </View>
                <View style={[s.sumCard, { borderColor: summary.odenmesi_gereken >= 0 ? '#7c2d12' : '#166534', flex: 2 }]}>
                  <Text style={[s.sumVal, { color: summary.odenmesi_gereken >= 0 ? C.red : '#4ade80', fontSize: 18 }]}>
                    {money(Math.abs(summary.odenmesi_gereken ?? 0))}
                  </Text>
                  <Text style={s.sumLbl}>{(summary.odenmesi_gereken ?? 0) >= 0 ? 'Ödenecek KDV' : 'KDV İadesi'}</Text>
                </View>
              </View>
            )}

            {/* Kayıtlar */}
            <Text style={s.secTitle}>Tüm Kayıtlar</Text>
            {records.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>🧾</Text><Text style={s.emptyTxt}>KDV kaydı yok</Text></View>
              : records.map(rec => (
                  <SwipeableRow
                    key={rec.id}
                    style={{ marginHorizontal: 16, marginBottom: 8, borderRadius: 14 }}
                    actions={[{ label: 'Sil', icon: '🗑️', color: '#dc2626', onPress: () => del(rec.id) }]}
                  >
                    <View style={s.card}>
                      <View style={[s.typeDot, { backgroundColor: rec.type === 'satis' ? '#166534' : '#7c2d12' }]} />
                      <View style={{ flex: 1 }}>
                        <Text style={s.name}>{KDV_TYPES[rec.type] ?? rec.type}</Text>
                        <Text style={s.sub}>%{rec.rate} · {fmtDate(rec.transaction_date)}</Text>
                        {rec.description && <Text style={s.sub}>{rec.description}</Text>}
                      </View>
                      <View style={{ alignItems: 'flex-end' }}>
                        <Text style={[s.amount, { color: rec.type === 'satis' ? '#4ade80' : '#f97316' }]}>
                          {money(rec.kdv_amount)}
                        </Text>
                        <Text style={s.sub}>{money(rec.base_amount)} matrah</Text>
                      </View>
                    </View>
                  </SwipeableRow>
                ))
            }
          </ScrollView>
      }

      {/* KDV Ekle Modal */}
      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>KDV Kaydı Ekle</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
              <Text style={s.mLbl}>Tür</Text>
              <View style={{ flexDirection: 'row', gap: 8, marginBottom: 14 }}>
                {(Object.entries(KDV_TYPES) as [string, string][]).map(([k, v]) => (
                  <TouchableOpacity key={k} style={[s.chip, kdvType === k && s.chipActive]} onPress={() => setKdvType(k as any)}>
                    <Text style={[s.chipTxt, kdvType === k && { color: C.white }]}>{v}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={s.mLbl}>KDV Oranı (%)</Text>
              <View style={{ flexDirection: 'row', gap: 8, marginBottom: 14 }}>
                {KDV_RATES.map(r => (
                  <TouchableOpacity key={r} style={[s.chip, rate === r && s.chipActive]} onPress={() => setRate(r)}>
                    <Text style={[s.chipTxt, rate === r && { color: C.white }]}>%{r}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={s.mLbl}>Matrah (KDV Hariç Tutar ₺) *</Text>
              <TextInput style={[s.mInput, { marginBottom: 14 }]} value={base} onChangeText={setBase}
                placeholder="10.000,00" placeholderTextColor={C.muted} keyboardType="decimal-pad" />

              {base ? (
                <View style={s.calcPreview}>
                  <Text style={s.calcTxt}>
                    KDV: {money(parseFloat(base.replace(',','.') || '0') * parseInt(rate) / 100)} ·
                    Toplam: {money(parseFloat(base.replace(',','.') || '0') * (1 + parseInt(rate) / 100))}
                  </Text>
                </View>
              ) : null}

              <Text style={s.mLbl}>Açıklama</Text>
              <TextInput style={[s.mInput, { marginBottom: 14 }]} value={desc} onChangeText={setDesc}
                placeholder="İşlem açıklaması" placeholderTextColor={C.muted} />

              <Text style={s.mLbl}>Tarih</Text>
              <TextInput style={[s.mInput, { marginBottom: 14 }]} value={txDate} onChangeText={setTxDate}
                placeholder="YYYY-MM-DD" placeholderTextColor={C.muted} />

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>🧾 Kaydet</Text>}
              </TouchableOpacity>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:         { flex: 1, backgroundColor: C.bg },
  center:     { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:     { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:       { fontSize: 24, color: C.txt },
  title:      { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  addBtn:     { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 7 },
  addTxt:     { fontSize: 14, fontWeight: '700', color: C.white },
  periodRow:  { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 12, gap: 20 },
  periodArrow:{ fontSize: 28, color: C.txt, paddingHorizontal: 8 },
  periodTxt:  { fontSize: 16, fontWeight: '700', color: C.txt, minWidth: 100, textAlign: 'center' },
  summaryGrid:{ flexDirection: 'row', flexWrap: 'wrap', marginHorizontal: 16, gap: 10, marginBottom: 8 },
  sumCard:    { flex: 1, minWidth: '45%', backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  sumVal:     { fontSize: 14, fontWeight: '800', color: C.txt },
  sumLbl:     { fontSize: 10, color: C.txt2, marginTop: 4, textAlign: 'center' },
  secTitle:   { fontSize: 11, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 1, paddingHorizontal: 16, marginTop: 16, marginBottom: 8 },
  card:       { flexDirection: 'row', alignItems: 'center', backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border, gap: 10 },
  typeDot:    { width: 8, height: 8, borderRadius: 4 },
  name:       { fontSize: 14, fontWeight: '700', color: C.txt },
  sub:        { fontSize: 12, color: C.txt2, marginTop: 2 },
  amount:     { fontSize: 14, fontWeight: '800' },
  empty:      { alignItems: 'center', paddingVertical: 48 },
  emptyIco:   { fontSize: 48, marginBottom: 12 },
  emptyTxt:   { fontSize: 15, color: C.txt2 },
  mHeader:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:     { fontSize: 20, fontWeight: '800', color: C.txt },
  close:      { fontSize: 20, color: C.muted },
  mLbl:       { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:     { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  saveBtn:    { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 15, alignItems: 'center', marginTop: 8 },
  saveTxt:    { fontSize: 15, fontWeight: '700', color: C.white },
  chip:       { paddingHorizontal: 12, paddingVertical: 8, backgroundColor: C.card, borderRadius: 20, borderWidth: 1, borderColor: C.border },
  chipActive: { backgroundColor: C.blue, borderColor: C.blue },
  chipTxt:    { fontSize: 13, color: C.txt2 },
  calcPreview:{ backgroundColor: '#0f1420', borderRadius: 10, padding: 10, marginBottom: 14, borderWidth: 1, borderColor: C.border },
  calcTxt:    { fontSize: 13, color: '#4ade80', fontWeight: '600' },
});
