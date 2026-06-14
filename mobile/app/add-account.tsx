import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { accounts as accountsApi } from '../services/api';

const TYPES = [
  { key: 'vadesiz',     label: '🏦 Vadesiz' },
  { key: 'vadeli',      label: '📅 Vadeli' },
  { key: 'kredi_karti', label: '💳 Kredi Kartı' },
  { key: 'kmh',         label: '📉 KMH' },
  { key: 'diger',       label: '🔖 Diğer' },
];

const COLORS = ['#007aff','#0ecb81','#f6465d','#f0b90b','#af52de','#ff9f0a','#32ade6','#30d158'];

export default function AddAccountScreen() {
  const router = useRouter();
  const [name,    setName]    = useState('');
  const [bank,    setBank]    = useState('');
  const [type,    setType]    = useState('vadesiz');
  const [initial, setInitial] = useState('0');
  const [limit,   setLimit]   = useState('');
  const [color,   setColor]   = useState(COLORS[0]);
  const [loading, setLoading] = useState(false);

  async function save() {
    if (!name.trim() || !bank.trim()) { Alert.alert('Hata', 'Hesap adı ve banka gerekli'); return; }
    setLoading(true);
    try {
      await accountsApi.create({
        name:            name.trim(),
        bank:            bank.trim(),
        type,
        initial_balance: parseFloat(initial.replace(',', '.')) || 0,
        limit_:          parseFloat(limit.replace(',', '.')) || 0,
        color,
      });
      Alert.alert('✅ Hesap Eklendi', '', [
        { text: 'Hesaplara Dön', onPress: () => router.back() },
      ]);
    } catch (e: any) {
      Alert.alert('Hata', e.message);
    } finally { setLoading(false); }
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
          <View style={s.header}>
            <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
            <Text style={s.title}>Hesap Ekle</Text>
          </View>

          <View style={s.sec}>
            <Field label="Hesap Adı *" value={name} onChange={setName} placeholder="Vadesiz Hesap" />
            <Field label="Banka *" value={bank} onChange={setBank} placeholder="Garanti BBVA" />
          </View>

          <View style={s.sec}>
            <Text style={s.sLbl}>Hesap Tipi</Text>
            <View style={s.grid}>
              {TYPES.map(t => (
                <TouchableOpacity key={t.key} style={[s.tBtn, type === t.key && s.tA]} onPress={() => setType(t.key)}>
                  <Text style={[s.tTxt, type === t.key && s.tTxtA]}>{t.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <View style={s.sec}>
            <Field label="Başlangıç Bakiyesi (₺)" value={initial} onChange={setInitial} placeholder="0" keyboard="decimal-pad" />
            {['kredi_karti','kmh'].includes(type) && (
              <Field label="Limit (₺)" value={limit} onChange={setLimit} placeholder="10000" keyboard="decimal-pad" />
            )}
          </View>

          <View style={s.sec}>
            <Text style={s.sLbl}>Renk</Text>
            <View style={s.colorRow}>
              {COLORS.map(c => (
                <TouchableOpacity key={c} style={[s.colorDot, { backgroundColor: c }, color === c && s.colorSel]} onPress={() => setColor(c)} />
              ))}
            </View>
          </View>

          <TouchableOpacity style={[s.btn, loading && { opacity: 0.6 }]} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.btnTxt}>🏦 Hesabı Ekle</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function Field({ label, value, onChange, placeholder, keyboard }: any) {
  return (
    <View style={s.field}>
      <Text style={s.fLbl}>{label}</Text>
      <TextInput style={s.input} value={value} onChangeText={onChange} placeholder={placeholder}
        placeholderTextColor={C.muted} keyboardType={keyboard ?? 'default'} />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  header:    { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:      { fontSize: 24, color: C.txt },
  title:     { fontSize: 22, fontWeight: '800', color: C.txt },
  sec:       { marginHorizontal: 16, marginTop: 20, gap: 12 },
  sLbl:      { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 1 },
  field:     { gap: 6 },
  fLbl:      { fontSize: 12, fontWeight: '600', color: C.txt2 },
  input:     { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  grid:      { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  tBtn:      { paddingHorizontal: 14, paddingVertical: 9, borderRadius: 12, backgroundColor: C.card, borderWidth: 1, borderColor: C.border },
  tA:        { backgroundColor: C.blue, borderColor: C.blue },
  tTxt:      { fontSize: 14, color: C.txt2 },
  tTxtA:     { color: C.white, fontWeight: '600' },
  colorRow:  { flexDirection: 'row', gap: 10, flexWrap: 'wrap' },
  colorDot:  { width: 36, height: 36, borderRadius: 18 },
  colorSel:  { borderWidth: 3, borderColor: C.white },
  btn:       { margin: 16, marginTop: 24, marginBottom: 40, backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  btnTxt:    { fontSize: 16, fontWeight: '700', color: C.white },
});
