import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money, fmtDate } from '../constants/Colors';
import { suppliers as suppApi, misc } from '../services/api';

export default function InvoicesScreen() {
  const router = useRouter();
  const [invoices, setInvoices] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [tab,     setTab]     = useState<'bekleyen'|'odendi'>('bekleyen');
  const [modal,   setModal]   = useState(false);
  const [aging,   setAging]   = useState<any>(null);

  // Form
  const [suppId,  setSuppId]  = useState<number | null>(null);
  const [amount,  setAmount]  = useState('');
  const [due,     setDue]     = useState('');
  const [desc,    setDesc]    = useState('');
  const [invNo,   setInvNo]   = useState('');
  const [saving,  setSaving]  = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const [inv, sup, ag] = await Promise.all([
        misc.supplierInvoices(tab),
        suppApi.list(),
        tab === 'bekleyen' ? misc.supplierInvoiceAging().catch(() => null) : Promise.resolve(null),
      ]);
      setInvoices(Array.isArray(inv) ? inv : (inv as any).invoices ?? []);
      setSuppliers(Array.isArray(sup) ? sup : []);
      setAging(ag);
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, [tab]);

  useEffect(() => { load(); }, [load]);

  async function addInvoice() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!suppId) { Alert.alert('Hata', 'Tedarikçi seçin'); return; }
    if (!amt || amt <= 0) { Alert.alert('Hata', 'Geçerli tutar girin'); return; }
    if (!due) { Alert.alert('Hata', 'Vade tarihi girin'); return; }
    setSaving(true);
    try {
      await misc.addSupplierInvoice({ supplier_id: suppId, amount: amt, due_date: due, description: desc.trim(), invoice_no: invNo.trim() });
      setModal(false); setAmount(''); setDesc(''); setInvNo(''); setDue('');
      load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function payInvoice(id: number) {
    Alert.alert('Faturayı Öde', 'Bu faturayı ödenmiş olarak işaretlemek istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Öde', style: 'default', onPress: async () => {
        try { await misc.paySupplierInvoice(id); load(); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  async function delInvoice(id: number) {
    Alert.alert('Sil', 'Bu faturayı silmek istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await misc.deleteSupplierInvoice(id); setInvoices(p => p.filter(i => i.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Tedarikçi Faturaları</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => setModal(true)}><Text style={s.addTxt}>+ Ekle</Text></TouchableOpacity>
      </View>

      <View style={s.tabs}>
        {(['bekleyen','odendi'] as const).map(t => (
          <TouchableOpacity key={t} style={[s.tab, tab === t && s.tabA]} onPress={() => setTab(t)}>
            <Text style={[s.tabTxt, tab === t && { color: C.white }]}>{t === 'bekleyen' ? '⏳ Bekleyen' : '✅ Ödendi'}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>

            {/* Aging özeti */}
            {tab === 'bekleyen' && aging?.buckets && (
              <View style={s.agingCard}>
                <Text style={s.agingTitle}>Vade Analizi</Text>
                <View style={{ flexDirection: 'row', justifyContent: 'space-around', marginTop: 8 }}>
                  {(aging.buckets as any[]).map((b: any, i: number) => (
                    <View key={i} style={{ alignItems: 'center' }}>
                      <Text style={[s.agingAmt, { color: b.total > 0 ? (i === 0 ? C.green : i === 1 ? C.yellow : C.red) : C.muted }]}>
                        {b.total > 0 ? money(b.total) : '—'}
                      </Text>
                      <Text style={s.agingLbl}>{b.label}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {invoices.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>📄</Text><Text style={s.emptyTxt}>Fatura yok</Text></View>
              : invoices.map(inv => {
                  const daysLeft = inv.due_date ? Math.ceil((new Date(inv.due_date).getTime() - Date.now()) / 86400000) : 0;
                  const isOverdue = daysLeft < 0 && tab === 'bekleyen';
                  return (
                    <View key={inv.id} style={[s.card, isOverdue && { borderColor: C.red }]}>
                      <View style={s.cardTop}>
                        <View style={{ flex: 1 }}>
                          <Text style={s.invName}>{inv.supplier_name || '—'}</Text>
                          {inv.invoice_no && <Text style={s.invSub}>Fatura No: {inv.invoice_no}</Text>}
                          {inv.description && <Text style={s.invSub}>{inv.description}</Text>}
                        </View>
                        <Text style={[s.invAmt, isOverdue && { color: C.red }]}>{money(inv.amount)}</Text>
                      </View>
                      <View style={s.cardBot}>
                        <Text style={[s.dueDate, isOverdue && { color: C.red }]}>
                          {isOverdue ? `⚠️ ${Math.abs(daysLeft)} gün geçti` : inv.due_date ? `Vade: ${fmtDate(inv.due_date)}` : ''}
                        </Text>
                        <View style={s.actions}>
                          {tab === 'bekleyen' && (
                            <TouchableOpacity style={s.payBtn} onPress={() => payInvoice(inv.id)}>
                              <Text style={s.payTxt}>Öde</Text>
                            </TouchableOpacity>
                          )}
                          <TouchableOpacity onPress={() => delInvoice(inv.id)}>
                            <Text style={{ color: C.muted, fontSize: 18 }}>✕</Text>
                          </TouchableOpacity>
                        </View>
                      </View>
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
              <Text style={s.mTitle}>Fatura Ekle</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }}>
              <Text style={s.mLbl}>Tedarikçi *</Text>
              <View style={s.suppList}>
                {suppliers.map(sup => (
                  <TouchableOpacity key={sup.id} style={[s.suppBtn, suppId === sup.id && s.suppA]} onPress={() => setSuppId(sup.id)}>
                    <Text style={[s.suppTxt, suppId === sup.id && { color: C.white }]}>{sup.name}</Text>
                  </TouchableOpacity>
                ))}
                {suppliers.length === 0 && <Text style={{ color: C.txt2, fontSize: 13 }}>Önce tedarikçi ekleyin</Text>}
              </View>

              {[
                { lbl: 'Tutar (₺) *', val: amount, set: setAmount, ph: '1000', kb: 'decimal-pad' as const },
                { lbl: 'Vade Tarihi *', val: due, set: setDue, ph: 'YYYY-MM-DD' },
                { lbl: 'Fatura No', val: invNo, set: setInvNo, ph: 'INV-001' },
                { lbl: 'Açıklama', val: desc, set: setDesc, ph: 'İsteğe bağlı' },
              ].map(({ lbl, val, set, ph, kb }) => (
                <View key={lbl} style={{ marginTop: 14 }}>
                  <Text style={s.mLbl}>{lbl}</Text>
                  <TextInput style={s.mInput} value={val} onChangeText={set} placeholder={ph} placeholderTextColor={C.muted} keyboardType={kb} />
                </View>
              ))}

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={addInvoice} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>📄 Faturayı Ekle</Text>}
              </TouchableOpacity>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:       { flex: 1, backgroundColor: C.bg },
  center:   { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:   { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:     { fontSize: 24, color: C.txt },
  title:    { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  addBtn:   { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 7 },
  addTxt:   { fontSize: 14, fontWeight: '700', color: C.white },
  tabs:     { flexDirection: 'row', marginHorizontal: 16, marginTop: 10, backgroundColor: C.card, borderRadius: 12, padding: 4, gap: 4, borderWidth: 1, borderColor: C.border },
  tab:      { flex: 1, paddingVertical: 8, borderRadius: 8, alignItems: 'center' },
  tabA:     { backgroundColor: C.blue },
  tabTxt:   { fontSize: 14, fontWeight: '600', color: C.txt2 },
  card:     { marginHorizontal: 16, marginTop: 10, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  cardTop:  { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  invName:  { fontSize: 15, fontWeight: '700', color: C.txt },
  invSub:   { fontSize: 12, color: C.txt2, marginTop: 2 },
  invAmt:   { fontSize: 16, fontWeight: '800', color: C.txt },
  cardBot:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 10 },
  dueDate:  { fontSize: 13, color: C.txt2 },
  actions:  { flexDirection: 'row', alignItems: 'center', gap: 10 },
  payBtn:   { backgroundColor: C.green, borderRadius: 8, paddingHorizontal: 14, paddingVertical: 6 },
  payTxt:   { fontSize: 13, fontWeight: '700', color: C.white },
  empty:    { alignItems: 'center', paddingVertical: 48 },
  emptyIco: { fontSize: 48, marginBottom: 12 },
  emptyTxt: { fontSize: 15, color: C.txt2 },
  mHeader:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:   { fontSize: 20, fontWeight: '800', color: C.txt },
  close:    { fontSize: 20, color: C.muted },
  mLbl:     { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:   { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  suppList: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 6 },
  suppBtn:  { paddingHorizontal: 14, paddingVertical: 9, borderRadius: 12, backgroundColor: C.card, borderWidth: 1, borderColor: C.border },
  suppA:    { backgroundColor: C.blue, borderColor: C.blue },
  suppTxt:  { fontSize: 13, color: C.txt2 },
  saveBtn:   { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 16, marginBottom: 32 },
  saveTxt:   { fontSize: 16, fontWeight: '700', color: C.white },
  agingCard: { marginHorizontal: 16, marginTop: 10, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  agingTitle: { fontSize: 12, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  agingAmt:  { fontSize: 14, fontWeight: '800', marginBottom: 2 },
  agingLbl:  { fontSize: 11, color: C.muted },
});
