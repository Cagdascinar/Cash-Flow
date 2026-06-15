import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { useRouter } from 'expo-router';
import { C, money, fmtDate } from '../constants/Colors';
import { customers as custApi } from '../services/api';
import { SwipeableRow } from '../components/SwipeableRow';

export default function CustomersScreen() {
  const router = useRouter();
  const [list,    setList]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [modal,   setModal]   = useState(false);
  const [invModal,setInvModal]= useState(false);
  const [saving,  setSaving]  = useState(false);
  const [selCust, setSelCust] = useState<any>(null);
  const [invoices,setInvoices]= useState<any[]>([]);

  // Müşteri form
  const [name,    setName]    = useState('');
  const [contact, setContact] = useState('');
  const [phone,   setPhone]   = useState('');
  const [email,   setEmail]   = useState('');
  const [taxId,   setTaxId]   = useState('');

  // Fatura form
  const [invNo,   setInvNo]   = useState('');
  const [invAmt,  setInvAmt]  = useState('');
  const [invDate, setInvDate] = useState(new Date().toISOString().slice(0, 10));
  const [dueDate, setDueDate] = useState('');
  const [invDesc, setInvDesc] = useState('');

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setList((await custApi.list()) || []); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  function resetForm() {
    setName(''); setContact(''); setPhone(''); setEmail(''); setTaxId('');
  }

  async function save() {
    if (!name.trim()) { Alert.alert('Hata', 'Müşteri adı zorunlu'); return; }
    setSaving(true);
    try {
      await custApi.create({
        name: name.trim(), contact_name: contact.trim(),
        phone: phone.trim(), email: email.trim(), tax_id: taxId.trim(),
      });
      setModal(false); resetForm(); load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function openInvoices(cust: any) {
    setSelCust(cust);
    setInvModal(true);
    try {
      const data = await custApi.invoices(cust.id);
      setInvoices(Array.isArray(data) ? data : []);
    } catch {}
  }

  async function addInvoice() {
    if (!invNo.trim() || !invAmt) { Alert.alert('Hata', 'Fatura no ve tutar zorunlu'); return; }
    setSaving(true);
    try {
      await custApi.addInvoice({
        customer_id: selCust.id,
        invoice_no: invNo.trim(),
        amount: parseFloat(invAmt.replace(',', '.')),
        invoice_date: invDate,
        due_date: dueDate || null,
        description: invDesc.trim(),
      });
      setInvNo(''); setInvAmt(''); setInvDesc('');
      setInvoices((await custApi.invoices(selCust.id)) || []);
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function payInvoice(id: number) {
    try {
      await custApi.payInvoice(id);
      setInvoices(p => p.map(x => x.id === id ? { ...x, status: 'odendi' } : x));
    } catch (e: any) { Alert.alert('Hata', e.message); }
  }

  async function delInvoice(id: number) {
    Alert.alert('Fatura Sil', 'Bu faturayı silmek istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try {
          await custApi.deleteInvoice(id);
          setInvoices(p => p.filter(x => x.id !== id));
          load();
        }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  async function del(id: number, nm: string) {
    Alert.alert('Sil', `"${nm}" silinsin mi?`, [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await custApi.delete(id); setList(p => p.filter(x => x.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  const totalReceivable = list.reduce((s, c) => s + (c.total_unpaid ?? 0), 0);

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Müşteriler</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => { resetForm(); setModal(true); }}>
          <Text style={s.addTxt}>+ Ekle</Text>
        </TouchableOpacity>
      </View>

      {/* Özet */}
      <View style={s.summaryRow}>
        <View style={s.sumCard}>
          <Text style={[s.sumVal, { color: '#f0b90b' }]}>{money(totalReceivable)}</Text>
          <Text style={s.sumLbl}>Toplam Alacak</Text>
        </View>
        <View style={s.sumCard}>
          <Text style={[s.sumVal, { color: '#4ade80' }]}>{list.length}</Text>
          <Text style={s.sumLbl}>Aktif Müşteri</Text>
        </View>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}
            contentContainerStyle={{ paddingBottom: 40 }}>
            {list.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>👥</Text><Text style={s.emptyTxt}>Müşteri eklenmedi</Text></View>
              : list.map(item => (
                  <SwipeableRow
                    key={item.id}
                    style={{ marginHorizontal: 16, marginTop: 8, borderRadius: 14 }}
                    actions={[{ label: 'Sil', icon: '🗑️', color: '#dc2626', onPress: () => del(item.id, item.name) }]}
                  >
                    <TouchableOpacity style={s.card} onPress={() => openInvoices(item)}>
                      <View style={s.cardLeft}>
                        <Text style={s.avatar}>{item.name[0]?.toUpperCase()}</Text>
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={s.name}>{item.name}</Text>
                        {item.contact_name && <Text style={s.sub}>{item.contact_name}</Text>}
                        {item.phone && <Text style={s.sub}>{item.phone}</Text>}
                      </View>
                      <View style={{ alignItems: 'flex-end' }}>
                        {(item.total_unpaid ?? 0) > 0
                          ? <Text style={[s.amount, { color: '#f0b90b' }]}>{money(item.total_unpaid)}</Text>
                          : <Text style={[s.amount, { color: '#4ade80' }]}>Temiz</Text>}
                      </View>
                    </TouchableOpacity>
                  </SwipeableRow>
                ))
            }
          </ScrollView>
      }

      {/* Müşteri Ekle Modal */}
      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Müşteri Ekle</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
              {[
                { lbl: 'Müşteri Adı *', val: name,    set: setName,    ph: 'ABC Şirketi' },
                { lbl: 'İletişim Kişisi', val: contact, set: setContact, ph: 'Ali Yılmaz' },
                { lbl: 'Telefon',         val: phone,   set: setPhone,   ph: '05xx xxx xxxx', kb: 'phone-pad' as const },
                { lbl: 'E-posta',         val: email,   set: setEmail,   ph: 'info@abc.com',  kb: 'email-address' as const },
                { lbl: 'Vergi No',        val: taxId,   set: setTaxId,   ph: '1234567890',   kb: 'numeric' as const },
              ].map(({ lbl, val, set, ph, kb }) => (
                <View key={lbl} style={{ marginBottom: 14 }}>
                  <Text style={s.mLbl}>{lbl}</Text>
                  <TextInput style={s.mInput} value={val} onChangeText={set}
                    placeholder={ph} placeholderTextColor={C.muted} keyboardType={kb} />
                </View>
              ))}
              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>👥 Kaydet</Text>}
              </TouchableOpacity>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>

      {/* Faturalar Modal */}
      <Modal visible={invModal} animationType="slide" presentationStyle="pageSheet">
        <GestureHandlerRootView style={{ flex: 1 }}>
          <SafeAreaView style={s.bg} edges={['top']}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>{selCust?.name}</Text>
              <TouchableOpacity onPress={() => setInvModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ flex: 1 }} contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
              {/* Yeni Fatura */}
              <View style={s.invForm}>
                <Text style={[s.mLbl, { marginBottom: 10 }]}>Yeni Fatura Ekle</Text>
                <View style={{ flexDirection: 'row', gap: 10, marginBottom: 8 }}>
                  <View style={{ flex: 1 }}>
                    <Text style={s.mLbl}>Fatura No *</Text>
                    <TextInput style={s.mInput} value={invNo} onChangeText={setInvNo} placeholder="F-001" placeholderTextColor={C.muted} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={s.mLbl}>Tutar (₺) *</Text>
                    <TextInput style={s.mInput} value={invAmt} onChangeText={setInvAmt} placeholder="0,00" placeholderTextColor={C.muted} keyboardType="decimal-pad" />
                  </View>
                </View>
                <View style={{ flexDirection: 'row', gap: 10, marginBottom: 8 }}>
                  <View style={{ flex: 1 }}>
                    <Text style={s.mLbl}>Tarih</Text>
                    <TextInput style={s.mInput} value={invDate} onChangeText={setInvDate} placeholder="YYYY-MM-DD" placeholderTextColor={C.muted} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={s.mLbl}>Vade</Text>
                    <TextInput style={s.mInput} value={dueDate} onChangeText={setDueDate} placeholder="YYYY-MM-DD" placeholderTextColor={C.muted} />
                  </View>
                </View>
                <TextInput style={s.mInput} value={invDesc} onChangeText={setInvDesc} placeholder="Açıklama" placeholderTextColor={C.muted} />
                <TouchableOpacity style={[s.saveBtn, { marginTop: 10 }, saving && { opacity: 0.6 }]} onPress={addInvoice} disabled={saving}>
                  <Text style={s.saveTxt}>+ Fatura Ekle</Text>
                </TouchableOpacity>
              </View>

              {/* Fatura Listesi */}
              <Text style={[s.mLbl, { marginTop: 20, marginBottom: 8 }]}>Faturalar</Text>
              {invoices.length === 0
                ? <Text style={{ color: C.muted, textAlign: 'center', paddingVertical: 20 }}>Fatura yok</Text>
                : invoices.map(inv => (
                    <SwipeableRow
                      key={inv.id}
                      style={{ marginBottom: 8, borderRadius: 12 }}
                      actions={[{ label: 'Sil', icon: '🗑️', color: '#dc2626', onPress: () => delInvoice(inv.id) }]}
                    >
                      <View style={[s.invCard, { marginBottom: 0 }]}>
                        <View style={{ flex: 1 }}>
                          <Text style={s.invNo}>{inv.invoice_no}</Text>
                          <Text style={s.sub}>{fmtDate(inv.invoice_date)}{inv.due_date ? ` · Vade: ${fmtDate(inv.due_date)}` : ''}</Text>
                        </View>
                        <View style={{ alignItems: 'flex-end', gap: 4 }}>
                          <Text style={[s.amount, { color: inv.status === 'odendi' ? '#4ade80' : '#f0b90b' }]}>
                            {money(inv.amount)}
                          </Text>
                          {inv.status !== 'odendi'
                            ? <TouchableOpacity onPress={() => payInvoice(inv.id)} style={s.payBtn}>
                                <Text style={s.payBtnTxt}>Tahsil Et</Text>
                              </TouchableOpacity>
                            : <Text style={{ color: '#4ade80', fontSize: 11 }}>✓ Ödendi</Text>
                          }
                        </View>
                      </View>
                    </SwipeableRow>
                  ))
              }
            </ScrollView>
          </SafeAreaView>
        </GestureHandlerRootView>
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
  summaryRow: { flexDirection: 'row', marginHorizontal: 16, marginTop: 12, gap: 10 },
  sumCard:    { flex: 1, backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  sumVal:     { fontSize: 15, fontWeight: '800', color: C.txt },
  sumLbl:     { fontSize: 10, color: C.txt2, marginTop: 4 },
  card:       { flexDirection: 'row', alignItems: 'center', backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border, gap: 12 },
  cardLeft:   { width: 42, height: 42, borderRadius: 21, backgroundColor: C.blue, alignItems: 'center', justifyContent: 'center' },
  avatar:     { fontSize: 18, fontWeight: '800', color: C.white },
  name:       { fontSize: 15, fontWeight: '700', color: C.txt },
  sub:        { fontSize: 12, color: C.txt2, marginTop: 2 },
  amount:     { fontSize: 14, fontWeight: '800' },
  empty:      { alignItems: 'center', paddingVertical: 48 },
  emptyIco:   { fontSize: 48, marginBottom: 12 },
  emptyTxt:   { fontSize: 15, color: C.txt2 },
  mHeader:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:     { fontSize: 20, fontWeight: '800', color: C.txt },
  close:      { fontSize: 20, color: C.muted },
  mLbl:       { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:     { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border, marginBottom: 4 },
  saveBtn:    { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 15, alignItems: 'center', marginTop: 8 },
  saveTxt:    { fontSize: 15, fontWeight: '700', color: C.white },
  invForm:    { backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  invCard:    { flexDirection: 'row', alignItems: 'center', backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border },
  invNo:      { fontSize: 14, fontWeight: '700', color: C.txt },
  payBtn:    { backgroundColor: '#166534', borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4 },
  payBtnTxt: { fontSize: 11, fontWeight: '700', color: '#4ade80' },
});
