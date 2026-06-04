import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/Colors';
import { api } from '../../services/api';

const INCOME_CATS = [
  'Maaş','Serbest Meslek','Kira Geliri','Yatırım Geliri / Satış',
  'Yatırım / Temettü','Hediye / İkramiye','Diğer Gelir',
];
const EXPENSE_CATS = [
  'Kira / Mortgage','Market / Gıda','Faturalar','Ulaşım','Yemek / Restoran',
  'Eğlence','Sağlık','Giyim','Eğitim','Abonelikler','Elektronik',
  'Sigorta','Vergi / Harç','Kredi Kartı Ödemesi','Yatırım Fonu',
  'Hisse Senedi','Döviz Alımı','Altın Alımı','Diğer Gider',
];

export default function AddScreen() {
  const router = useRouter();
  const [type, setType]           = useState<'gider' | 'gelir'>('gider');
  const [amount, setAmount]       = useState('');
  const [description, setDesc]    = useState('');
  const [category, setCategory]   = useState('Kira / Mortgage');
  const [date, setDate]           = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading]     = useState(false);

  const cats = type === 'gelir' ? INCOME_CATS : EXPENSE_CATS;

  async function handleSave() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!amt || isNaN(amt) || amt <= 0) { Alert.alert('Hata', 'Geçerli bir tutar girin'); return; }
    if (!category)                       { Alert.alert('Hata', 'Kategori seçin'); return; }
    setLoading(true);
    try {
      await api.transactions.create({ type, amount: amt, description: description.trim(), category, date });
      setAmount(''); setDesc('');
      Alert.alert('Başarılı', 'İşlem eklendi', [
        { text: 'Tamam', onPress: () => router.replace('/(tabs)') },
      ]);
    } catch (e: any) {
      Alert.alert('Hata', e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={s.header}><Text style={s.title}>İşlem Ekle</Text></View>

          {/* Gelir / Gider toggle */}
          <View style={s.typeRow}>
            <TouchableOpacity
              style={[s.typeBtn, type === 'gider' && s.typeBtnRed]}
              onPress={() => { setType('gider'); setCategory(EXPENSE_CATS[0]); }}
            >
              <Text style={[s.typeText, type === 'gider' && s.typeTextActive]}>Gider</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[s.typeBtn, type === 'gelir' && s.typeBtnGreen]}
              onPress={() => { setType('gelir'); setCategory(INCOME_CATS[0]); }}
            >
              <Text style={[s.typeText, type === 'gelir' && s.typeTextActive]}>Gelir</Text>
            </TouchableOpacity>
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
              style={s.input} placeholder="İsteğe bağlı"
              placeholderTextColor={Colors.textMuted}
              value={description} onChangeText={setDesc}
            />
          </View>

          {/* Tarih */}
          <View style={s.field}>
            <Text style={s.label}>Tarih</Text>
            <TextInput
              style={s.input} placeholder="YYYY-MM-DD"
              placeholderTextColor={Colors.textMuted}
              value={date} onChangeText={setDate}
            />
          </View>

          {/* Kategori */}
          <View style={s.field}>
            <Text style={s.label}>Kategori</Text>
            <View style={s.catGrid}>
              {cats.map((c) => (
                <TouchableOpacity
                  key={c}
                  style={[s.catBtn, category === c && s.catBtnActive]}
                  onPress={() => setCategory(c)}
                >
                  <Text style={[s.catText, category === c && s.catTextActive]}>{c}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <TouchableOpacity
            style={[s.saveBtn, { backgroundColor: type === 'gelir' ? Colors.green : Colors.primary }, loading && s.disabled]}
            onPress={handleSave}
            disabled={loading}
          >
            {loading
              ? <ActivityIndicator color={Colors.white} />
              : <Text style={s.saveBtnText}>Kaydet</Text>
            }
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  header: { paddingHorizontal: 16, paddingTop: 8 },
  title: { fontSize: 24, fontWeight: '800', color: Colors.textPrimary },
  typeRow: {
    flexDirection: 'row', marginHorizontal: 16, marginTop: 16,
    backgroundColor: Colors.bgInput, borderRadius: 14, padding: 4, gap: 4,
  },
  typeBtn: { flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: 'center' },
  typeBtnRed: { backgroundColor: Colors.red },
  typeBtnGreen: { backgroundColor: Colors.green },
  typeText: { fontSize: 15, fontWeight: '600', color: Colors.textSecondary },
  typeTextActive: { color: Colors.white },
  amountRow: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginTop: 24, gap: 4 },
  currency: { fontSize: 32, fontWeight: '800', color: Colors.textSecondary },
  amountInput: { flex: 1, fontSize: 48, fontWeight: '800', color: Colors.textPrimary, padding: 0 },
  field: { marginHorizontal: 16, marginTop: 20 },
  label: {
    fontSize: 13, fontWeight: '600', color: Colors.textSecondary,
    textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8,
  },
  input: {
    backgroundColor: Colors.bgInput, borderRadius: 12,
    paddingHorizontal: 14, paddingVertical: 13, fontSize: 15,
    color: Colors.textPrimary, borderWidth: 1, borderColor: Colors.border,
  },
  catGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  catBtn: {
    paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20,
    backgroundColor: Colors.bgInput, borderWidth: 1, borderColor: Colors.border,
  },
  catBtnActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  catText: { fontSize: 13, color: Colors.textSecondary },
  catTextActive: { color: Colors.white, fontWeight: '600' },
  saveBtn: { marginHorizontal: 16, marginTop: 24, marginBottom: 40, paddingVertical: 16, borderRadius: 14, alignItems: 'center' },
  disabled: { opacity: 0.6 },
  saveBtnText: { fontSize: 16, fontWeight: '700', color: Colors.white },
});
