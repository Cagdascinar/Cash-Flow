import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/Colors';
import { transactions } from '../../services/api';

// Backend ile birebir eşleştirilmiş kategori listeleri
const GELIR_CATS = [
  'Maaş', 'Serbest Meslek', 'Kira Geliri',
  'Yatırım Geliri / Satış', 'Yatırım / Temettü',
  'Hediye / İkramiye', 'Hesaplar Arası Transfer', 'Diğer Gelir',
];
const GIDER_CATS = [
  'Kira / Mortgage', 'Market / Gıda', 'Faturalar', 'Ulaşım',
  'Yemek / Restoran', 'Eğlence', 'Sağlık', 'Giyim', 'Eğitim',
  'Abonelikler', 'Elektronik', 'Sigorta', 'Vergi / Harç',
  'Kredi Kartı Ödemesi', 'Yemek Kartı Ödemesi',
  'Döviz Alımı', 'Altın Alımı', 'Yatırım Fonu', 'Hisse Senedi',
  'Hesaplar Arası Transfer', 'Diğer Gider',
];

export default function AddScreen() {
  const router = useRouter();
  const [type,     setType]    = useState<'gider' | 'gelir'>('gider');
  const [amount,   setAmount]  = useState('');
  const [desc,     setDesc]    = useState('');
  const [category, setCat]     = useState(GIDER_CATS[0]);
  const [date,     setDate]    = useState(new Date().toISOString().split('T')[0]);
  const [loading,  setLoading] = useState(false);

  const cats = type === 'gelir' ? GELIR_CATS : GIDER_CATS;

  async function save() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!amt || isNaN(amt) || amt <= 0) { Alert.alert('Hata', 'Geçerli tutar girin'); return; }
    setLoading(true);
    try {
      await transactions.create({ type, amount: amt, description: desc.trim(), category, date });
      setAmount(''); setDesc('');
      Alert.alert('Kaydedildi', `${type === 'gelir' ? 'Gelir' : 'Gider'} eklendi`, [
        { text: 'Tamam', onPress: () => router.replace('/(tabs)') },
        { text: 'Yeni Ekle' },
      ]);
    } catch (e: any) {
      Alert.alert('Hata', e.message);
    } finally { setLoading(false); }
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView showsVerticalScrollIndicator={false}>

          <View style={s.header}><Text style={s.title}>İşlem Ekle</Text></View>

          {/* Gelir / Gider */}
          <View style={s.toggle}>
            {(['gider', 'gelir'] as const).map(t => (
              <TouchableOpacity
                key={t}
                style={[s.toggleBtn, type === t && (t === 'gelir' ? s.toggleGreen : s.toggleRed)]}
                onPress={() => { setType(t); setCat(t === 'gelir' ? GELIR_CATS[0] : GIDER_CATS[0]); }}
              >
                <Text style={[s.toggleTxt, type === t && s.toggleTxtActive]}>
                  {t === 'gelir' ? '↑ Gelir' : '↓ Gider'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Tutar */}
          <View style={s.amountRow}>
            <Text style={s.currency}>₺</Text>
            <TextInput
              style={s.amountInput}
              placeholder="0,00"
              placeholderTextColor={Colors.textMuted}
              value={amount}
              onChangeText={setAmount}
              keyboardType="decimal-pad"
              autoFocus
            />
          </View>

          {/* Açıklama */}
          <View style={s.field}>
            <Text style={s.label}>Açıklama</Text>
            <TextInput
              style={s.input}
              placeholder="İsteğe bağlı"
              placeholderTextColor={Colors.textMuted}
              value={desc}
              onChangeText={setDesc}
            />
          </View>

          {/* Tarih */}
          <View style={s.field}>
            <Text style={s.label}>Tarih</Text>
            <TextInput
              style={s.input}
              placeholder="YYYY-MM-DD"
              placeholderTextColor={Colors.textMuted}
              value={date}
              onChangeText={setDate}
            />
          </View>

          {/* Kategori */}
          <View style={s.field}>
            <Text style={s.label}>Kategori</Text>
            <View style={s.catGrid}>
              {cats.map(c => (
                <TouchableOpacity
                  key={c}
                  style={[s.catBtn, category === c && s.catActive]}
                  onPress={() => setCat(c)}
                >
                  <Text style={[s.catTxt, category === c && s.catTxtActive]}>{c}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <TouchableOpacity
            style={[s.saveBtn, { backgroundColor: type === 'gelir' ? Colors.green : Colors.blue }, loading && s.disabled]}
            onPress={save}
            disabled={loading}
          >
            {loading
              ? <ActivityIndicator color={Colors.white} />
              : <Text style={s.saveTxt}>Kaydet</Text>
            }
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:    { flex: 1, backgroundColor: Colors.bg },
  header:       { paddingHorizontal: 16, paddingTop: 8 },
  title:        { fontSize: 24, fontWeight: '800', color: Colors.textPrimary },
  toggle:       { flexDirection: 'row', margin: 16, backgroundColor: Colors.bgInput, borderRadius: 14, padding: 4, gap: 4 },
  toggleBtn:    { flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: 'center' },
  toggleGreen:  { backgroundColor: Colors.green },
  toggleRed:    { backgroundColor: Colors.red },
  toggleTxt:    { fontSize: 15, fontWeight: '600', color: Colors.textSecondary },
  toggleTxtActive: { color: Colors.white },
  amountRow:    { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, gap: 4 },
  currency:     { fontSize: 32, fontWeight: '800', color: Colors.textSecondary },
  amountInput:  { flex: 1, fontSize: 48, fontWeight: '800', color: Colors.textPrimary, padding: 0 },
  field:        { marginHorizontal: 16, marginTop: 20 },
  label:        { fontSize: 12, fontWeight: '700', color: Colors.textSecondary, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 },
  input:        { backgroundColor: Colors.bgInput, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: Colors.textPrimary, borderWidth: 1, borderColor: Colors.border },
  catGrid:      { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  catBtn:       { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: Colors.bgInput, borderWidth: 1, borderColor: Colors.border },
  catActive:    { backgroundColor: Colors.blue, borderColor: Colors.blue },
  catTxt:       { fontSize: 13, color: Colors.textSecondary },
  catTxtActive: { color: Colors.white, fontWeight: '600' },
  saveBtn:      { marginHorizontal: 16, marginTop: 24, marginBottom: 40, paddingVertical: 16, borderRadius: 14, alignItems: 'center' },
  disabled:     { opacity: 0.6 },
  saveTxt:      { fontSize: 16, fontWeight: '700', color: Colors.white },
});
