import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money, fmtDate } from '../constants/Colors';
import { suppliers as suppApi, misc, accounts as accApi } from '../services/api';

export default function InvoicesScreen() {
  const router = useRouter();
  const [invoices,  setInvoices]  = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [accounts,  setAccounts]  = useState<any[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [ref,       setRef]       = useState(false);
  const [tab,       setTab]       = useState<'bekleyen'|'odendi'>('bekleyen');
  const [invType,   setInvType]   = useState<'alis'|'satis'>('alis');
  const [modal,     setModal]     = useState(false);
  const [aging,     setAging]     = useState<any>(null);

  // Ödeme modal
  const [payModal,  setPayModal]  = useState(false);
  const [payingId,  setPayingId]  = useState<number|null>(null);
  const [payMethod, setPayMethod] = useState<'havale'|'kart'|'nakit'>('havale');
  const [payAccId,  setPayAccId]  = useState<number|null>(null);
  const [accPicker, setAccPicker] = useState(false);
  const [paying,    setPaying]    = useState(false);

  // Form
  const [suppId,      setSuppId]      = useState<number | null>(null);
  const [amount,      setAmount]      = useState('');
  const [due,         setDue]         = useState('');
  const [invDate,     setInvDate]     = useState('');
  const [desc,        setDesc]        = useState('');
  const [invNo,       setInvNo]       = useState('');
  const [saving,      setSaving]      = useState(false);
  const [suppPicker,  setSuppPicker]  = useState(false);
  const [suppSearch,  setSuppSearch]  = useState('');

  const selectedAcc = accounts.find(a => a.id === payAccId);

  const selectedSupp = suppliers.find(s => s.id === suppId);
  const filteredSupp = suppliers.filter(s =>
    s.name.toLowerCase().includes(suppSearch.toLowerCase())
  );

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const [inv, sup, ag, acc] = await Promise.all([
        misc.supplierInvoices(tab),
        suppApi.list(),
        tab === 'bekleyen' ? misc.supplierInvoiceAging().catch(() => null) : Promise.resolve(null),
        accApi.list().catch(() => []),
      ]);
      const all = Array.isArray(inv) ? inv : (inv as any).invoices ?? [];
      setInvoices(all.filter((i: any) => i.invoice_type === invType || !i.invoice_type));
      setSuppliers(Array.isArray(sup) ? sup : []);
      setAging(ag);
      setAccounts(Array.isArray(acc) ? acc : []);
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, [tab, invType]);

  useEffect(() => { load(); }, [load]);

  async function addInvoice() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!suppId) { Alert.alert('Hata', 'Tedarikçi seçin'); return; }
    if (!amt || amt <= 0) { Alert.alert('Hata', 'Geçerli tutar girin'); return; }
    if (!due) { Alert.alert('Hata', 'Vade tarihi girin'); return; }
    const sup = suppliers.find(s => s.id === suppId);
    setSaving(true);
    try {
      await misc.addSupplierInvoice({
        supplier_id: suppId,
        supplier_name: sup?.name ?? '',
        amount: amt,
        invoice_date: invDate || new Date().toISOString().split('T')[0],
        due_date: due,
        description: desc.trim(),
        invoice_no: invNo.trim(),
        invoice_type: invType,
      });
      setModal(false); setAmount(''); setDesc(''); setInvNo(''); setDue(''); setInvDate('');
      load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  function openPayModal(id: number) {
    setPayingId(id); setPayMethod('havale'); setPayAccId(null); setPayModal(true);
  }

  async function confirmPay() {
    if (!payingId) return;
    if (payMethod !== 'nakit' && !payAccId) {
      Alert.alert('Hata', 'Ödeme yapılan hesabı seçin'); return;
    }
    setPaying(true);
    try {
      const acc = accounts.find(a => a.id === payAccId);
      await misc.paySupplierInvoice(payingId, {
        payment_method: payMethod,
        payment_account_id: payAccId,
        payment_account_name: acc ? `${acc.name}${acc.last4 ? ` ****${acc.last4}` : ''}` : '',
      });
      setPayModal(false); load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setPaying(false); }
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

      {/* Alış / Satış */}
      <View style={s.tabs}>
        {(['alis','satis'] as const).map(t => (
          <TouchableOpacity key={t} style={[s.tab, invType === t && s.tabA]} onPress={() => setInvType(t)}>
            <Text style={[s.tabTxt, invType === t && { color: C.white }]}>{t === 'alis' ? '📥 Alış' : '📤 Satış'}</Text>
          </TouchableOpacity>
        ))}
      </View>
      {/* Bekleyen / Ödendi */}
      <View style={[s.tabs, { marginTop: 6 }]}>
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
                            <TouchableOpacity style={s.payBtn} onPress={() => openPayModal(inv.id)}>
                              <Text style={s.payTxt}>💳 Öde</Text>
                            </TouchableOpacity>
                          )}
                          {tab === 'odendi' && inv.payment_method && (
                            <Text style={s.payInfo}>
                              {inv.payment_method === 'havale' ? '🏦' : inv.payment_method === 'kart' ? '💳' : '💵'} {inv.payment_account_name || inv.payment_method}
                            </Text>
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

      {/* Ödeme Yöntemi Modalı */}
      <Modal visible={payModal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <View style={s.mHeader}>
            <Text style={s.mTitle}>Ödeme Yöntemi</Text>
            <TouchableOpacity onPress={() => setPayModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
          </View>
          <ScrollView style={{ padding: 16 }}>
            <Text style={s.mLbl}>Ödeme Şekli</Text>
            <View style={{ flexDirection: 'row', gap: 10, marginTop: 8 }}>
              {([
                { key: 'havale', label: '🏦 Havale/EFT' },
                { key: 'kart',   label: '💳 Kart' },
                { key: 'nakit',  label: '💵 Nakit' },
              ] as const).map(m => (
                <TouchableOpacity key={m.key}
                  style={[s.methodBtn, payMethod === m.key && s.methodBtnA]}
                  onPress={() => setPayMethod(m.key)}>
                  <Text style={[s.methodTxt, payMethod === m.key && { color: C.white }]}>{m.label}</Text>
                </TouchableOpacity>
              ))}
            </View>

            {payMethod !== 'nakit' && (
              <>
                <Text style={[s.mLbl, { marginTop: 16 }]}>
                  {payMethod === 'kart' ? 'Hangi Karttan' : 'Hangi Hesaptan'}
                </Text>
                <TouchableOpacity style={[s.dropdown, payAccId && s.dropdownSelected]}
                  onPress={() => setAccPicker(true)}>
                  <Text style={[s.dropdownTxt, !payAccId && { color: C.muted }]}>
                    {selectedAcc ? `${selectedAcc.name}${selectedAcc.last4 ? ` ****${selectedAcc.last4}` : ''}` : 'Hesap / Kart seçin...'}
                  </Text>
                  <Text style={{ color: C.muted }}>▾</Text>
                </TouchableOpacity>
              </>
            )}

            <TouchableOpacity
              style={[s.saveBtn, { marginTop: 24 }, paying && { opacity: 0.6 }]}
              onPress={confirmPay} disabled={paying}>
              {paying ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>✅ Ödendi Olarak İşaretle</Text>}
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Hesap Seçim Picker */}
      <Modal visible={accPicker} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <View style={s.mHeader}>
            <Text style={s.mTitle}>Hesap Seç</Text>
            <TouchableOpacity onPress={() => setAccPicker(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
          </View>
          <ScrollView>
            {accounts.length === 0
              ? <View style={s.empty}><Text style={s.emptyTxt}>Hesap bulunamadı</Text></View>
              : accounts.map(acc => (
                <TouchableOpacity key={acc.id}
                  style={[s.pickerRow, payAccId === acc.id && s.pickerRowActive]}
                  onPress={() => { setPayAccId(acc.id); setAccPicker(false); }}>
                  <View style={s.pickerIco}><Text style={{ fontSize: 18 }}>🏦</Text></View>
                  <View style={{ flex: 1 }}>
                    <Text style={[s.pickerName, payAccId === acc.id && { color: C.blue }]}>{acc.name}</Text>
                    {acc.last4 && <Text style={s.pickerSub}>****{acc.last4}</Text>}
                  </View>
                  {payAccId === acc.id && <Text style={{ color: C.blue, fontSize: 18 }}>✓</Text>}
                </TouchableOpacity>
              ))
            }
            <View style={{ height: 40 }} />
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Tedarikçi seçim picker */}
      <Modal visible={suppPicker} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <View style={s.mHeader}>
            <Text style={s.mTitle}>Tedarikçi Seç</Text>
            <TouchableOpacity onPress={() => setSuppPicker(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
          </View>
          <View style={{ paddingHorizontal: 16, paddingBottom: 8 }}>
            <TextInput
              style={s.searchInput}
              value={suppSearch}
              onChangeText={setSuppSearch}
              placeholder="Ara..."
              placeholderTextColor={C.muted}
              autoFocus
            />
          </View>
          <ScrollView>
            {filteredSupp.length === 0
              ? <View style={s.empty}><Text style={s.emptyTxt}>Tedarikçi bulunamadı</Text></View>
              : filteredSupp.map(sup => (
                <TouchableOpacity
                  key={sup.id}
                  style={[s.pickerRow, suppId === sup.id && s.pickerRowActive]}
                  onPress={() => { setSuppId(sup.id); setSuppPicker(false); }}
                >
                  <View style={s.pickerIco}><Text style={{ fontSize: 18 }}>🏢</Text></View>
                  <View style={{ flex: 1 }}>
                    <Text style={[s.pickerName, suppId === sup.id && { color: C.blue }]}>{sup.name}</Text>
                    {sup.contact_name && <Text style={s.pickerSub}>{sup.contact_name}</Text>}
                  </View>
                  {suppId === sup.id && <Text style={{ color: C.blue, fontSize: 18 }}>✓</Text>}
                </TouchableOpacity>
              ))
            }
            <View style={{ height: 40 }} />
          </ScrollView>
        </SafeAreaView>
      </Modal>

      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Fatura Ekle</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }}>
              <Text style={s.mLbl}>Tedarikçi *</Text>
              <TouchableOpacity
                style={[s.dropdown, suppId && s.dropdownSelected]}
                onPress={() => { setSuppSearch(''); setSuppPicker(true); }}
              >
                <Text style={[s.dropdownTxt, !suppId && { color: C.muted }]}>
                  {selectedSupp ? `🏢 ${selectedSupp.name}` : 'Tedarikçi seçin...'}
                </Text>
                <Text style={{ color: C.muted, fontSize: 16 }}>▾</Text>
              </TouchableOpacity>

              {[
                { lbl: 'Tutar (₺) *', val: amount, set: setAmount, ph: '1000', kb: 'decimal-pad' as const },
                { lbl: 'Fatura Tarihi', val: invDate, set: setInvDate, ph: 'YYYY-MM-DD' },
                { lbl: 'Vade Tarihi *', val: due, set: setDue, ph: 'YYYY-MM-DD' },
                { lbl: 'Fatura No', val: invNo, set: setInvNo, ph: 'INV-001' },
                { lbl: 'Açıklama / Mal/Hizmet', val: desc, set: setDesc, ph: 'İsteğe bağlı' },
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
  payInfo:  { fontSize: 12, color: C.txt2, fontWeight: '500' },
  methodBtn:  { flex: 1, paddingVertical: 12, borderRadius: 12, backgroundColor: C.card, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  methodBtnA: { backgroundColor: C.blue, borderColor: C.blue },
  methodTxt:  { fontSize: 13, fontWeight: '600', color: C.txt2 },
  empty:    { alignItems: 'center', paddingVertical: 48 },
  emptyIco: { fontSize: 48, marginBottom: 12 },
  emptyTxt: { fontSize: 15, color: C.txt2 },
  mHeader:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:   { fontSize: 20, fontWeight: '800', color: C.txt },
  close:    { fontSize: 20, color: C.muted },
  mLbl:     { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:   { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  dropdown:         { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 14, borderWidth: 1, borderColor: C.border, marginTop: 6 },
  dropdownSelected: { borderColor: C.blue },
  dropdownTxt:      { fontSize: 15, color: C.txt, fontWeight: '500' },
  searchInput:      { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  pickerRow:        { flexDirection: 'row', alignItems: 'center', padding: 14, marginHorizontal: 16, marginBottom: 8, backgroundColor: C.card, borderRadius: 14, borderWidth: 1, borderColor: C.border, gap: 12 },
  pickerRowActive:  { borderColor: C.blue, backgroundColor: 'rgba(0,122,255,0.06)' },
  pickerIco:        { width: 40, height: 40, borderRadius: 12, backgroundColor: C.input, alignItems: 'center', justifyContent: 'center' },
  pickerName:       { fontSize: 15, fontWeight: '700', color: C.txt },
  pickerSub:        { fontSize: 12, color: C.txt2, marginTop: 2 },
  saveBtn:   { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 16, marginBottom: 32 },
  saveTxt:   { fontSize: 16, fontWeight: '700', color: C.white },
  agingCard: { marginHorizontal: 16, marginTop: 10, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  agingTitle: { fontSize: 12, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  agingAmt:  { fontSize: 14, fontWeight: '800', marginBottom: 2 },
  agingLbl:  { fontSize: 11, color: C.muted },
});
