import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { employees as empApi } from '../services/api';

const EMP_TYPES: Record<string, string> = {
  tam: 'Tam Zamanlı', yarim: 'Yarı Zamanlı', donemsel: 'Dönemsel',
};

export default function EmployeesScreen() {
  const router = useRouter();
  const [list,    setList]    = useState<any[]>([]);
  const [payroll, setPayroll] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [tab,     setTab]     = useState<'calisanlar'|'bordro'>('calisanlar');
  const [modal,   setModal]   = useState(false);
  const [prModal, setPrModal] = useState(false);
  const [saving,  setSaving]  = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [salType, setSalType] = useState<'brut'|'net'>('brut');

  // Çalışan form
  const [name,    setName]    = useState('');
  const [title,   setTitle]   = useState('');
  const [phone,   setPhone]   = useState('');
  const [email,   setEmail]   = useState('');
  const [gross,   setGross]   = useState('');
  const [netSal,  setNetSal]  = useState('');
  const [empType, setEmpType] = useState('tam');

  // Bordro form
  const [prEmpId, setPrEmpId] = useState<number|null>(null);
  const [prMonth, setPrMonth] = useState(new Date().toISOString().slice(0, 7));
  const [prGross, setPrGross] = useState('');
  const [prNet,   setPrNet]   = useState('');
  const [prType,  setPrType]  = useState<'brut'|'net'>('brut');
  const [prPrev,  setPrPrev]  = useState<any>(null);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const [e, p] = await Promise.all([empApi.list(), empApi.payroll()]);
      setList(Array.isArray(e) ? e : []);
      setPayroll(Array.isArray(p) ? p : []);
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  function resetEmpForm() {
    setName(''); setTitle(''); setPhone(''); setEmail('');
    setGross(''); setNetSal(''); setEmpType('tam'); setSalType('brut'); setPreview(null);
  }

  async function calcPreview() {
    const val = salType === 'brut' ? gross : netSal;
    if (!val) return;
    try {
      const d = salType === 'brut'
        ? await empApi.calculate({ gross_salary: parseFloat(val.replace(',', '.')) })
        : await empApi.calculate({ net_salary:   parseFloat(val.replace(',', '.')) });
      setPreview(d);
    } catch {}
  }

  async function saveEmp() {
    if (!name.trim()) { Alert.alert('Hata', 'İsim zorunlu'); return; }
    const salVal = salType === 'brut' ? gross : netSal;
    if (!salVal) { Alert.alert('Hata', 'Maaş zorunlu'); return; }
    setSaving(true);
    try {
      let grossSal: number;
      if (salType === 'net') {
        const calc = await empApi.calculate({ net_salary: parseFloat(salVal.replace(',', '.')) });
        grossSal = calc.gross_salary;
      } else {
        grossSal = parseFloat(salVal.replace(',', '.'));
      }
      await empApi.create({
        name: name.trim(), title: title.trim(), phone: phone.trim(),
        email: email.trim(), gross_salary: grossSal, employment_type: empType,
      });
      setModal(false); resetEmpForm(); load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function calcPrPreview() {
    const val = prType === 'brut' ? prGross : prNet;
    if (!val) return;
    try {
      const d = prType === 'brut'
        ? await empApi.calculate({ gross_salary: parseFloat(val.replace(',', '.')) })
        : await empApi.calculate({ net_salary:   parseFloat(val.replace(',', '.')) });
      setPrPrev(d);
    } catch {}
  }

  async function savePayroll() {
    if (!prEmpId) { Alert.alert('Hata', 'Çalışan seçin'); return; }
    const val = prType === 'brut' ? prGross : prNet;
    if (!val) { Alert.alert('Hata', 'Maaş zorunlu'); return; }
    setSaving(true);
    try {
      let calc: any;
      if (prType === 'net') {
        calc = await empApi.calculate({ net_salary: parseFloat(val.replace(',', '.')) });
      } else {
        calc = await empApi.calculate({ gross_salary: parseFloat(val.replace(',', '.')) });
      }
      await empApi.addPayroll({
        employee_id: prEmpId,
        period: prMonth,
        gross_salary: calc.gross_salary,
        net_salary: calc.net_salary,
        sgk_employee: calc.sgk_employee + calc.isizlik,
        gelir_vergisi: calc.gelir_vergisi,
        damga_vergisi: calc.damga_vergisi,
        sgk_employer: calc.sgk_employer + calc.isizlik_employer,
        total_cost: calc.total_cost,
      });
      setPrModal(false);
      setPrGross(''); setPrNet(''); setPrPrev(null); setPrEmpId(null);
      load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function delEmp(id: number, nm: string) {
    Alert.alert('Sil', `"${nm}" silinsin mi?`, [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await empApi.delete(id); setList(p => p.filter(x => x.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  const totalCost = payroll.reduce((s, p) => s + (p.total_cost ?? 0), 0);

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Çalışanlar</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => tab === 'calisanlar' ? (resetEmpForm(), setModal(true)) : (setPrEmpId(null), setPrPrev(null), setPrGross(''), setPrNet(''), setPrModal(true))}>
          <Text style={s.addTxt}>+ {tab === 'calisanlar' ? 'Çalışan' : 'Bordro'}</Text>
        </TouchableOpacity>
      </View>

      {/* Tab */}
      <View style={s.tabs}>
        {(['calisanlar', 'bordro'] as const).map(t => (
          <TouchableOpacity key={t} style={[s.tab, tab === t && s.tabActive]} onPress={() => setTab(t)}>
            <Text style={[s.tabTxt, tab === t && s.tabTxtActive]}>
              {t === 'calisanlar' ? '👷 Çalışanlar' : '📋 Bordro'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}
            contentContainerStyle={{ paddingBottom: 40 }}>

            {tab === 'calisanlar' ? (
              list.length === 0
                ? <View style={s.empty}><Text style={s.emptyIco}>👷</Text><Text style={s.emptyTxt}>Çalışan eklenmedi</Text></View>
                : list.map(emp => (
                    <View key={emp.id} style={s.card}>
                      <View style={s.empAvatar}>
                        <Text style={s.empAvatarTxt}>{emp.name[0]?.toUpperCase()}</Text>
                      </View>
                      <View style={{ flex: 1 }}>
                        <Text style={s.name}>{emp.name}</Text>
                        <Text style={s.sub}>{emp.title ?? ''} · {EMP_TYPES[emp.employment_type] ?? ''}</Text>
                      </View>
                      <View style={{ alignItems: 'flex-end' }}>
                        <Text style={s.salary}>{money(emp.gross_salary)}</Text>
                        <Text style={s.salLbl}>Brüt</Text>
                      </View>
                      <TouchableOpacity onPress={() => delEmp(emp.id, emp.name)} style={{ paddingLeft: 8 }}>
                        <Text style={{ color: C.muted, fontSize: 16 }}>✕</Text>
                      </TouchableOpacity>
                    </View>
                  ))
            ) : (
              <>
                <View style={s.summaryRow}>
                  <View style={s.sumCard}>
                    <Text style={[s.sumVal, { color: C.red }]}>{money(totalCost)}</Text>
                    <Text style={s.sumLbl}>Toplam İşveren Maliyeti</Text>
                  </View>
                  <View style={s.sumCard}>
                    <Text style={[s.sumVal, { color: '#4ade80' }]}>{payroll.length}</Text>
                    <Text style={s.sumLbl}>Bordro Kaydı</Text>
                  </View>
                </View>
                {payroll.length === 0
                  ? <View style={s.empty}><Text style={s.emptyIco}>📋</Text><Text style={s.emptyTxt}>Bordro kaydı yok</Text></View>
                  : payroll.map(pr => (
                      <View key={pr.id} style={s.card}>
                        <View style={{ flex: 1 }}>
                          <Text style={s.name}>{pr.employee_name ?? `Çalışan #${pr.employee_id}`}</Text>
                          <Text style={s.sub}>{pr.period}</Text>
                        </View>
                        <View style={{ alignItems: 'flex-end' }}>
                          <Text style={s.salary}>{money(pr.net_salary)}</Text>
                          <Text style={s.salLbl}>Net</Text>
                        </View>
                      </View>
                    ))
                }
              </>
            )}
          </ScrollView>
      }

      {/* Çalışan Ekle Modal */}
      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Çalışan Ekle</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
              {[
                { lbl: 'Ad Soyad *', val: name,  set: setName,  ph: 'Ahmet Yılmaz' },
                { lbl: 'Unvan',      val: title,  set: setTitle, ph: 'Yazılım Geliştirici' },
                { lbl: 'Telefon',    val: phone,  set: setPhone, ph: '05xx xxx xxxx', kb: 'phone-pad' as const },
                { lbl: 'E-posta',    val: email,  set: setEmail, ph: 'ahmet@sirket.com', kb: 'email-address' as const },
              ].map(({ lbl, val, set, ph, kb }) => (
                <View key={lbl} style={{ marginBottom: 12 }}>
                  <Text style={s.mLbl}>{lbl}</Text>
                  <TextInput style={s.mInput} value={val} onChangeText={set}
                    placeholder={ph} placeholderTextColor={C.muted} keyboardType={kb} />
                </View>
              ))}

              <Text style={s.mLbl}>İstihdam Tipi</Text>
              <View style={{ flexDirection: 'row', gap: 8, marginBottom: 12 }}>
                {Object.entries(EMP_TYPES).map(([k, v]) => (
                  <TouchableOpacity key={k} style={[s.chip, empType === k && s.chipActive]} onPress={() => setEmpType(k)}>
                    <Text style={[s.chipTxt, empType === k && { color: C.white }]}>{v}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={s.mLbl}>Maaş Türü</Text>
              <View style={{ flexDirection: 'row', gap: 8, marginBottom: 12 }}>
                {(['brut', 'net'] as const).map(t => (
                  <TouchableOpacity key={t} style={[s.chip, salType === t && s.chipActive]}
                    onPress={() => { setSalType(t); setPreview(null); }}>
                    <Text style={[s.chipTxt, salType === t && { color: C.white }]}>{t === 'brut' ? 'Brüt Gir' : 'Net Gir'}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={s.mLbl}>{salType === 'brut' ? 'Brüt Maaş (₺)' : 'Net Maaş (₺)'}</Text>
              <View style={{ flexDirection: 'row', gap: 8, marginBottom: 12 }}>
                <TextInput style={[s.mInput, { flex: 1 }]}
                  value={salType === 'brut' ? gross : netSal}
                  onChangeText={salType === 'brut' ? setGross : setNetSal}
                  placeholder="0,00" placeholderTextColor={C.muted} keyboardType="decimal-pad" />
                <TouchableOpacity style={s.calcBtn} onPress={calcPreview}>
                  <Text style={s.calcBtnTxt}>Hesapla</Text>
                </TouchableOpacity>
              </View>

              {preview && (
                <View style={s.prevBox}>
                  {[
                    { l: 'Brüt Maaş',    v: preview.gross_salary,              c: C.txt },
                    { l: 'SGK İşçi',     v: -preview.sgk_employee,             c: C.red },
                    { l: 'İşsizlik',     v: -preview.isizlik,                   c: C.red },
                    { l: 'Gelir Vergisi',v: -preview.gelir_vergisi,             c: C.red },
                    { l: 'Damga Vergisi',v: -preview.damga_vergisi,             c: C.red },
                    { l: 'Net Maaş',     v: preview.net_salary,                 c: '#4ade80' },
                    { l: 'SGK İşveren',  v: preview.sgk_employer,               c: '#f0b90b' },
                    { l: 'Toplam Maliyet',v: preview.total_cost,                c: C.red },
                  ].map(({ l, v, c }) => (
                    <View key={l} style={s.prevRow}>
                      <Text style={s.prevL}>{l}</Text>
                      <Text style={[s.prevV, { color: c }]}>{money(Math.abs(v))}</Text>
                    </View>
                  ))}
                </View>
              )}

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={saveEmp} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>👷 Kaydet</Text>}
              </TouchableOpacity>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>

      {/* Bordro Ekle Modal */}
      <Modal visible={prModal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Bordro Oluştur</Text>
              <TouchableOpacity onPress={() => setPrModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
              <Text style={s.mLbl}>Çalışan</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8, marginBottom: 12 }}>
                {list.map(emp => (
                  <TouchableOpacity key={emp.id}
                    style={[s.chip, prEmpId === emp.id && s.chipActive]}
                    onPress={() => { setPrEmpId(emp.id); setPrGross(String(emp.gross_salary)); setPrPrev(null); }}>
                    <Text style={[s.chipTxt, prEmpId === emp.id && { color: C.white }]}>{emp.name}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>

              <Text style={s.mLbl}>Dönem (YYYY-MM)</Text>
              <TextInput style={[s.mInput, { marginBottom: 12 }]} value={prMonth} onChangeText={setPrMonth}
                placeholder="2025-01" placeholderTextColor={C.muted} />

              <Text style={s.mLbl}>Maaş Türü</Text>
              <View style={{ flexDirection: 'row', gap: 8, marginBottom: 12 }}>
                {(['brut', 'net'] as const).map(t => (
                  <TouchableOpacity key={t} style={[s.chip, prType === t && s.chipActive]}
                    onPress={() => { setPrType(t); setPrPrev(null); }}>
                    <Text style={[s.chipTxt, prType === t && { color: C.white }]}>{t === 'brut' ? 'Brüt Gir' : 'Net Gir'}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={s.mLbl}>{prType === 'brut' ? 'Brüt Maaş (₺)' : 'Net Maaş (₺)'}</Text>
              <View style={{ flexDirection: 'row', gap: 8, marginBottom: 12 }}>
                <TextInput style={[s.mInput, { flex: 1 }]}
                  value={prType === 'brut' ? prGross : prNet}
                  onChangeText={prType === 'brut' ? setPrGross : setPrNet}
                  placeholder="0,00" placeholderTextColor={C.muted} keyboardType="decimal-pad" />
                <TouchableOpacity style={s.calcBtn} onPress={calcPrPreview}>
                  <Text style={s.calcBtnTxt}>Hesapla</Text>
                </TouchableOpacity>
              </View>

              {prPrev && (
                <View style={s.prevBox}>
                  {[
                    { l: 'Brüt Maaş',    v: prPrev.gross_salary,   c: C.txt },
                    { l: 'SGK + İşsizlik', v: -(prPrev.sgk_employee + prPrev.isizlik), c: C.red },
                    { l: 'Gelir Vergisi', v: -prPrev.gelir_vergisi,  c: C.red },
                    { l: 'Damga Vergisi', v: -prPrev.damga_vergisi,  c: C.red },
                    { l: 'Net Maaş',      v: prPrev.net_salary,      c: '#4ade80' },
                    { l: 'İşveren SGK',   v: prPrev.sgk_employer,    c: '#f0b90b' },
                    { l: 'Toplam Maliyet',v: prPrev.total_cost,      c: C.red },
                  ].map(({ l, v, c }) => (
                    <View key={l} style={s.prevRow}>
                      <Text style={s.prevL}>{l}</Text>
                      <Text style={[s.prevV, { color: c }]}>{money(Math.abs(v))}</Text>
                    </View>
                  ))}
                </View>
              )}

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={savePayroll} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>📋 Bordroyu Kaydet</Text>}
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
  tabs:       { flexDirection: 'row', marginHorizontal: 16, marginTop: 12, backgroundColor: C.card, borderRadius: 12, borderWidth: 1, borderColor: C.border, padding: 4 },
  tab:        { flex: 1, alignItems: 'center', paddingVertical: 8, borderRadius: 10 },
  tabActive:  { backgroundColor: C.blue },
  tabTxt:     { fontSize: 13, fontWeight: '600', color: C.txt2 },
  tabTxtActive: { color: C.white },
  summaryRow: { flexDirection: 'row', marginHorizontal: 16, marginTop: 12, gap: 10 },
  sumCard:    { flex: 1, backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  sumVal:     { fontSize: 14, fontWeight: '800', color: C.txt },
  sumLbl:     { fontSize: 10, color: C.txt2, marginTop: 4, textAlign: 'center' },
  card:       { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginTop: 8, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border, gap: 10 },
  empAvatar:  { width: 42, height: 42, borderRadius: 21, backgroundColor: '#1e2533', alignItems: 'center', justifyContent: 'center' },
  empAvatarTxt: { fontSize: 18, fontWeight: '800', color: C.txt },
  name:       { fontSize: 15, fontWeight: '700', color: C.txt },
  sub:        { fontSize: 12, color: C.txt2, marginTop: 2 },
  salary:     { fontSize: 14, fontWeight: '800', color: '#4ade80' },
  salLbl:     { fontSize: 10, color: C.muted },
  empty:      { alignItems: 'center', paddingVertical: 48 },
  emptyIco:   { fontSize: 48, marginBottom: 12 },
  emptyTxt:   { fontSize: 15, color: C.txt2 },
  mHeader:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:     { fontSize: 20, fontWeight: '800', color: C.txt },
  close:      { fontSize: 20, color: C.muted },
  mLbl:       { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:     { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  saveBtn:    { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 15, alignItems: 'center', marginTop: 12 },
  saveTxt:    { fontSize: 15, fontWeight: '700', color: C.white },
  chip:       { paddingHorizontal: 12, paddingVertical: 8, backgroundColor: C.card, borderRadius: 20, borderWidth: 1, borderColor: C.border },
  chipActive: { backgroundColor: C.blue, borderColor: C.blue },
  chipTxt:    { fontSize: 13, color: C.txt2 },
  calcBtn:    { backgroundColor: '#1e2533', borderRadius: 12, paddingHorizontal: 14, justifyContent: 'center', borderWidth: 1, borderColor: C.border },
  calcBtnTxt: { fontSize: 13, fontWeight: '700', color: C.txt },
  prevBox:    { backgroundColor: '#0f1420', borderRadius: 12, padding: 12, marginBottom: 4, borderWidth: 1, borderColor: C.border },
  prevRow:    { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 5, borderBottomWidth: 1, borderBottomColor: '#1a2030' },
  prevL:      { fontSize: 13, color: C.txt2 },
  prevV:      { fontSize: 13, fontWeight: '700' },
});
