import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Alert, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView,
} from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { goals as goalsApi } from '../services/api';

const GOAL_TYPES = [
  { key: 'dolar',      label: '💵 Dolar (USD)' },
  { key: 'euro',       label: '💶 Euro (EUR)' },
  { key: 'altin',      label: '🥇 Altın' },
  { key: 'bitcoin',    label: '₿ Bitcoin' },
  { key: 'arsa',       label: '🏗️ Arsa/Gayrimenkul' },
  { key: 'emeklilik',  label: '👴 Emeklilik' },
  { key: 'diger',      label: '🎯 Diğer' },
];

export default function AddGoalScreen() {
  const router = useRouter();
  const [name,    setName]    = useState('');
  const [gtype,   setGtype]   = useState('diger');
  const [monthly, setMonthly] = useState('');
  const [note,    setNote]    = useState('');
  const [loading, setLoading] = useState(false);

  async function save() {
    if (!name.trim()) { Alert.alert('Hata', 'Hedef adı gerekli'); return; }
    const m = parseFloat(monthly.replace(',', '.'));
    if (!m || m <= 0) { Alert.alert('Hata', 'Geçerli aylık hedef girin'); return; }
    setLoading(true);
    try {
      await goalsApi.create({ name: name.trim(), goal_type: gtype, monthly_target: m, note: note.trim() });
      Alert.alert('✅ Hedef Eklendi', '', [{ text: 'Tamam', onPress: () => router.back() }]);
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setLoading(false); }
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
          <View style={s.header}>
            <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
            <Text style={s.title}>Hedef Ekle</Text>
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Hedef Adı *</Text>
            <TextInput style={s.input} value={name} onChangeText={setName} placeholder="Ev için birikim..." placeholderTextColor={C.muted} />
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Aylık Hedef (₺) *</Text>
            <View style={s.amtRow}>
              <Text style={s.curr}>₺</Text>
              <TextInput style={s.amtInput} value={monthly} onChangeText={setMonthly} placeholder="5000" placeholderTextColor={C.muted} keyboardType="decimal-pad" />
            </View>
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Hedef Türü</Text>
            <View style={s.grid}>
              {GOAL_TYPES.map(t => (
                <TouchableOpacity key={t.key} style={[s.tBtn, gtype === t.key && s.tA]} onPress={() => setGtype(t.key)}>
                  <Text style={[s.tTxt, gtype === t.key && { color: C.white }]}>{t.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Not</Text>
            <TextInput style={[s.input, { height: 80, textAlignVertical: 'top' }]} value={note} onChangeText={setNote} placeholder="İsteğe bağlı..." placeholderTextColor={C.muted} multiline />
          </View>

          <TouchableOpacity style={[s.btn, loading && { opacity: 0.6 }]} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.btnTxt}>🎯 Hedefi Kaydet</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  header:    { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:      { fontSize: 24, color: C.txt },
  title:     { fontSize: 22, fontWeight: '800', color: C.txt },
  field:     { marginHorizontal: 16, marginTop: 20, gap: 8 },
  lbl:       { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  input:     { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  amtRow:    { flexDirection: 'row', alignItems: 'center', gap: 4 },
  curr:      { fontSize: 28, fontWeight: '800', color: C.txt2 },
  amtInput:  { flex: 1, fontSize: 40, fontWeight: '800', color: C.txt, padding: 0, backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 10, borderWidth: 1, borderColor: C.border },
  grid:      { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  tBtn:      { paddingHorizontal: 14, paddingVertical: 9, borderRadius: 12, backgroundColor: C.card, borderWidth: 1, borderColor: C.border },
  tA:        { backgroundColor: C.blue, borderColor: C.blue },
  tTxt:      { fontSize: 13, color: C.txt2 },
  btn:       { margin: 16, marginTop: 24, marginBottom: 40, backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  btnTxt:    { fontSize: 16, fontWeight: '700', color: C.white },
});
