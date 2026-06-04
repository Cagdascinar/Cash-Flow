import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../../constants/Colors';
import { transactions } from '../../services/api';

const GELIR = ['Maaş','Serbest Meslek','Kira Geliri','Yatırım Geliri / Satış','Yatırım / Temettü','Hediye / İkramiye','Hesaplar Arası Transfer','Diğer Gelir'];
const GIDER = ['Kira / Mortgage','Market / Gıda','Faturalar','Ulaşım','Yemek / Restoran','Eğlence','Sağlık','Giyim','Eğitim','Abonelikler','Elektronik','Sigorta','Vergi / Harç','Kredi Kartı Ödemesi','Yemek Kartı Ödemesi','Döviz Alımı','Altın Alımı','Yatırım Fonu','Hisse Senedi','Hesaplar Arası Transfer','Diğer Gider'];

export default function AddScreen() {
  const router = useRouter();
  const [type,    setType]   = useState<'gider' | 'gelir'>('gider');
  const [amount,  setAmount] = useState('');
  const [desc,    setDesc]   = useState('');
  const [cat,     setCat]    = useState(GIDER[0]);
  const [date,    setDate]   = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoad]   = useState(false);

  const cats = type === 'gelir' ? GELIR : GIDER;

  async function save() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!amt || isNaN(amt) || amt <= 0) { Alert.alert('Hata', 'Geçerli tutar girin'); return; }
    setLoad(true);
    try {
      await transactions.create({ type, amount: amt, description: desc.trim(), category: cat, date });
      Alert.alert('✅ Kaydedildi', '', [
        { text: 'Ana Sayfa', onPress: () => router.replace('/(tabs)') },
        { text: 'Yeni Ekle', onPress: () => { setAmount(''); setDesc(''); } },
      ]);
    } catch (e: any) {
      Alert.alert('Hata', e.message);
    } finally { setLoad(false); }
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView showsVerticalScrollIndicator={false}>

          <View style={s.header}><Text style={s.title}>İşlem Ekle</Text></View>

          {/* Toggle */}
          <View style={s.toggle}>
            {(['gider', 'gelir'] as const).map(t => (
              <TouchableOpacity key={t} style={[s.tBtn, type === t && (t === 'gelir' ? s.tGreen : s.tRed)]}
                onPress={() => { setType(t); setCat(t === 'gelir' ? GELIR[0] : GIDER[0]); }}>
                <Text style={[s.tTxt, type === t && s.tTxtA]}>{t === 'gelir' ? '↑  Gelir' : '↓  Gider'}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Tutar */}
          <View style={s.amtRow}>
            <Text style={s.curr}>₺</Text>
            <TextInput style={s.amtInput} placeholder="0,00" placeholderTextColor={C.muted} value={amount} onChangeText={setAmount} keyboardType="decimal-pad" autoFocus />
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Açıklama</Text>
            <TextInput style={s.input} placeholder="İsteğe bağlı" placeholderTextColor={C.muted} value={desc} onChangeText={setDesc} />
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Tarih</Text>
            <TextInput style={s.input} placeholder="YYYY-MM-DD" placeholderTextColor={C.muted} value={date} onChangeText={setDate} />
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Kategori</Text>
            <View style={s.catGrid}>
              {cats.map(c => (
                <TouchableOpacity key={c} style={[s.catBtn, cat === c && s.catA]} onPress={() => setCat(c)}>
                  <Text style={[s.catTxt, cat === c && s.catTxtA]}>{c}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <TouchableOpacity style={[s.save, { backgroundColor: type === 'gelir' ? C.green : C.blue }, loading && { opacity: 0.6 }]} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>Kaydet</Text>}
          </TouchableOpacity>

        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  header:    { paddingHorizontal: 16, paddingTop: 8 },
  title:     { fontSize: 24, fontWeight: '800', color: C.txt },
  toggle:    { flexDirection: 'row', margin: 16, backgroundColor: C.input, borderRadius: 14, padding: 4, gap: 4 },
  tBtn:      { flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: 'center' },
  tGreen:    { backgroundColor: C.green },
  tRed:      { backgroundColor: C.red },
  tTxt:      { fontSize: 15, fontWeight: '600', color: C.txt2 },
  tTxtA:     { color: C.white },
  amtRow:    { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, gap: 4 },
  curr:      { fontSize: 32, fontWeight: '800', color: C.txt2 },
  amtInput:  { flex: 1, fontSize: 48, fontWeight: '800', color: C.txt, padding: 0 },
  field:     { marginHorizontal: 16, marginTop: 20 },
  lbl:       { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 },
  input:     { backgroundColor: C.input, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  catGrid:   { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  catBtn:    { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: C.input, borderWidth: 1, borderColor: C.border },
  catA:      { backgroundColor: C.blue, borderColor: C.blue },
  catTxt:    { fontSize: 13, color: C.txt2 },
  catTxtA:   { color: C.white, fontWeight: '600' },
  save:      { marginHorizontal: 16, marginTop: 24, marginBottom: 40, paddingVertical: 16, borderRadius: 14, alignItems: 'center' },
  saveTxt:   { fontSize: 16, fontWeight: '700', color: C.white },
});
