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

export default function SuppliersScreen() {
  const router = useRouter();
  const [list,    setList]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [modal,   setModal]   = useState(false);
  const [name,    setName]    = useState('');
  const [contact, setContact] = useState('');
  const [email,   setEmail]   = useState('');
  const [phone,   setPhone]   = useState('');
  const [saving,  setSaving]  = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setList(await suppApi.list() as any[]); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function save() {
    if (!name.trim()) { Alert.alert('Hata', 'Tedarikçi adı gerekli'); return; }
    setSaving(true);
    try {
      await suppApi.create({ name: name.trim(), contact_name: contact.trim(), email: email.trim(), phone: phone.trim() });
      setModal(false); setName(''); setContact(''); setEmail(''); setPhone('');
      load();
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
        <TouchableOpacity style={s.addBtn} onPress={() => setModal(true)}>
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
                        {sup.contact_name && <Text style={s.sub}>{sup.contact_name}</Text>}
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

      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.modal} edges={['top']}>
          <View style={s.mHeader}>
            <Text style={s.mTitle}>Tedarikçi Ekle</Text>
            <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
          </View>
          <ScrollView style={{ padding: 16 }}>
            {[
              { lbl: 'Tedarikçi Adı *', val: name, set: setName, ph: 'ABC Ltd.' },
              { lbl: 'Yetkili Kişi', val: contact, set: setContact, ph: 'Ahmet Yılmaz' },
              { lbl: 'E-posta', val: email, set: setEmail, ph: 'info@abc.com', kb: 'email-address' as const },
              { lbl: 'Telefon', val: phone, set: setPhone, ph: '0532 000 0000', kb: 'phone-pad' as const },
            ].map(({ lbl, val, set, ph, kb }) => (
              <View key={lbl} style={{ marginBottom: 14 }}>
                <Text style={s.mLbl}>{lbl}</Text>
                <TextInput style={s.mInput} value={val} onChangeText={set} placeholder={ph} placeholderTextColor={C.muted} keyboardType={kb} />
              </View>
            ))}
            <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
              {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>🏢 Ekle</Text>}
            </TouchableOpacity>
          </ScrollView>
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
  card:     { marginHorizontal: 16, marginBottom: 10, marginTop: 8, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  cardTop:  { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  ico:      { width: 40, height: 40, borderRadius: 12, backgroundColor: C.input, alignItems: 'center', justifyContent: 'center' },
  name:     { fontSize: 15, fontWeight: '700', color: C.txt },
  sub:      { fontSize: 12, color: C.txt2, marginTop: 3 },
  empty:    { alignItems: 'center', paddingVertical: 48 },
  emptyIco: { fontSize: 48, marginBottom: 12 },
  emptyTxt: { fontSize: 15, color: C.txt2 },
  modal:    { flex: 1, backgroundColor: C.bg },
  mHeader:  { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:   { fontSize: 20, fontWeight: '800', color: C.txt },
  close:    { fontSize: 20, color: C.muted },
  mLbl:     { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:   { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  saveBtn:  { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 8, marginBottom: 32 },
  saveTxt:  { fontSize: 16, fontWeight: '700', color: C.white },
});
