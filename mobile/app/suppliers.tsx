import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { suppliers as suppApi } from '../services/api';

const VERGI_DAIRELERI = [
  'Büyük Mükellefler VD','Ankara VD','İstanbul VD','İzmir VD',
  'Bursa VD','Adana VD','Antalya VD','Konya VD','Kocaeli VD',
  'Mersin VD','Gaziantep VD','Şanlıurfa VD','Diyarbakır VD',
  'Samsun VD','Trabzon VD','Erzurum VD','Malatya VD','Kayseri VD',
  'Eskişehir VD','Denizli VD','Diğer',
];

export default function SuppliersScreen() {
  const router = useRouter();
  const [list,       setList]       = useState<any[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [ref,        setRef]        = useState(false);
  const [modal,      setModal]      = useState(false);
  const [saving,     setSaving]     = useState(false);
  const [vdPicker,   setVdPicker]   = useState(false);
  const [vdSearch,   setVdSearch]   = useState('');

  // Form
  const [name,      setName]      = useState('');
  const [unvan,     setUnvan]     = useState('');
  const [vkn,       setVkn]       = useState('');
  const [vergiD,    setVergiD]    = useState('');
  const [contact,   setContact]   = useState('');
  const [email,     setEmail]     = useState('');
  const [phone,     setPhone]     = useState('');
  const [address,   setAddress]   = useState('');

  const filteredVD = VERGI_DAIRELERI.filter(v =>
    v.toLowerCase().includes(vdSearch.toLowerCase())
  );

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setList(await suppApi.list() as any[]); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  function resetForm() {
    setName(''); setUnvan(''); setVkn(''); setVergiD('');
    setContact(''); setEmail(''); setPhone(''); setAddress('');
  }

  async function save() {
    if (!name.trim()) { Alert.alert('Hata', 'Tedarikçi adı gerekli'); return; }
    setSaving(true);
    try {
      await suppApi.create({
        name: name.trim(),
        unvan: unvan.trim(),
        vkn: vkn.trim(),
        vergi_dairesi: vergiD,
        contact_name: contact.trim(),
        email: email.trim(),
        phone: phone.trim(),
        address: address.trim(),
      });
      setModal(false); resetForm(); load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function del(id: number) {
    Alert.alert('Sil', 'Bu tedarikçiyi silmek istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await suppApi.delete(id); setList(p => p.filter(s => s.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Tedarikçiler</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => { resetForm(); setModal(true); }}>
          <Text style={s.addTxt}>+ Ekle</Text>
        </TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>
            {list.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>🏢</Text><Text style={s.emptyTxt}>Tedarikçi eklenmedi</Text></View>
              : list.map(sup => (
                  <View key={sup.id} style={s.card}>
                    <View style={s.cardTop}>
                      <View style={s.ico}><Text style={{ fontSize: 20 }}>🏢</Text></View>
                      <View style={{ flex: 1 }}>
                        <Text style={s.name}>{sup.name}</Text>
                        {sup.unvan && <Text style={s.sub}>{sup.unvan}</Text>}
                        {sup.vkn && <Text style={s.sub}>VKN: {sup.vkn}{sup.vergi_dairesi ? ` · ${sup.vergi_dairesi}` : ''}</Text>}
                        {sup.contact_name && <Text style={s.sub}>👤 {sup.contact_name}</Text>}
                        {sup.email && <Text style={s.sub}>📧 {sup.email}</Text>}
                        {sup.phone && <Text style={s.sub}>📞 {sup.phone}</Text>}
                      </View>
                      <TouchableOpacity onPress={() => del(sup.id)}><Text style={{ color: C.muted, fontSize: 16 }}>✕</Text></TouchableOpacity>
                    </View>
                  </View>
                ))
            }
            <View style={{ height: 40 }} />
          </ScrollView>
      }

      {/* Vergi Dairesi Picker */}
      <Modal visible={vdPicker} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <View style={s.mHeader}>
            <Text style={s.mTitle}>Vergi Dairesi</Text>
            <TouchableOpacity onPress={() => setVdPicker(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
          </View>
          <View style={{ paddingHorizontal: 16, paddingBottom: 8 }}>
            <TextInput
              style={s.search} value={vdSearch} onChangeText={setVdSearch}
              placeholder="Ara..." placeholderTextColor={C.muted} autoFocus
            />
          </View>
          <ScrollView>
            {filteredVD.map(vd => (
              <TouchableOpacity key={vd} style={[s.pickerRow, vergiD === vd && s.pickerActive]}
                onPress={() => { setVergiD(vd); setVdPicker(false); }}>
                <Text style={[s.pickerTxt, vergiD === vd && { color: C.blue, fontWeight: '700' }]}>{vd}</Text>
                {vergiD === vd && <Text style={{ color: C.blue }}>✓</Text>}
              </TouchableOpacity>
            ))}
            <View style={{ height: 40 }} />
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Tedarikçi Ekle Modal */}
      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Tedarikçi Ekle</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }}>

              <Text style={s.section}>Cari Hesap Bilgileri</Text>

              <Text style={s.mLbl}>Ünvan *</Text>
              <TextInput style={s.mInput} value={name} onChangeText={setName} placeholder="ABC Ticaret Limited Şirketi" placeholderTextColor={C.muted} />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Kısa Kod / Sicil</Text>
              <TextInput style={s.mInput} value={unvan} onChangeText={setUnvan} placeholder="ABC-001" placeholderTextColor={C.muted} />

              <View style={{ flexDirection: 'row', gap: 10, marginTop: 14 }}>
                <View style={{ flex: 1 }}>
                  <Text style={s.mLbl}>VKN / TCKN</Text>
                  <TextInput style={s.mInput} value={vkn} onChangeText={setVkn} placeholder="1234567890" placeholderTextColor={C.muted} keyboardType="numeric" maxLength={11} />
                </View>
              </View>

              <Text style={[s.mLbl, { marginTop: 14 }]}>Vergi Dairesi</Text>
              <TouchableOpacity style={[s.dropdown, vergiD && s.dropdownSel]} onPress={() => { setVdSearch(''); setVdPicker(true); }}>
                <Text style={[s.dropdownTxt, !vergiD && { color: C.muted }]}>{vergiD || 'Vergi dairesi seçin...'}</Text>
                <Text style={{ color: C.muted }}>▾</Text>
              </TouchableOpacity>

              <Text style={[s.section, { marginTop: 20 }]}>İletişim Bilgileri</Text>

              <Text style={s.mLbl}>Yetkili / Muhatap</Text>
              <TextInput style={s.mInput} value={contact} onChangeText={setContact} placeholder="Ahmet Yılmaz" placeholderTextColor={C.muted} />

              <Text style={[s.mLbl, { marginTop: 14 }]}>E-posta</Text>
              <TextInput style={s.mInput} value={email} onChangeText={setEmail} placeholder="info@abc.com" placeholderTextColor={C.muted} keyboardType="email-address" autoCapitalize="none" />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Telefon</Text>
              <TextInput style={s.mInput} value={phone} onChangeText={setPhone} placeholder="0532 000 0000" placeholderTextColor={C.muted} keyboardType="phone-pad" />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Adres</Text>
              <TextInput style={[s.mInput, { height: 72, textAlignVertical: 'top' }]} value={address} onChangeText={setAddress} placeholder="Açık adres..." placeholderTextColor={C.muted} multiline />

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>🏢 Tedarikçiyi Kaydet</Text>}
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
  card:        { marginHorizontal: 16, marginBottom: 10, marginTop: 8, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  cardTop:     { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  ico:         { width: 40, height: 40, borderRadius: 12, backgroundColor: C.input, alignItems: 'center', justifyContent: 'center' },
  name:        { fontSize: 15, fontWeight: '700', color: C.txt },
  sub:         { fontSize: 12, color: C.txt2, marginTop: 3 },
  empty:       { alignItems: 'center', paddingVertical: 48 },
  emptyIco:    { fontSize: 48, marginBottom: 12 },
  emptyTxt:    { fontSize: 15, color: C.txt2 },
  mHeader:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:      { fontSize: 20, fontWeight: '800', color: C.txt },
  close:       { fontSize: 20, color: C.muted },
  section:     { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12, marginTop: 4 },
  mLbl:        { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:      { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  dropdown:    { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 14, borderWidth: 1, borderColor: C.border },
  dropdownSel: { borderColor: C.blue },
  dropdownTxt: { fontSize: 15, color: C.txt },
  search:      { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 12, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  pickerRow:   { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: C.border },
  pickerActive:{ backgroundColor: 'rgba(0,122,255,0.06)' },
  pickerTxt:   { fontSize: 15, color: C.txt },
  saveBtn:     { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 16 },
  saveTxt:     { fontSize: 16, fontWeight: '700', color: C.white },
});
