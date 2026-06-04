import {
  View, Text, TextInput, TouchableOpacity,
  StyleSheet, ScrollView, Alert, ActivityIndicator,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/Colors';
import { api } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

const INCOME_CATS = [
  'Maaş', 'Serbest Meslek', 'Kira Geliri', 'Yatırım Getirisi',
  'Satış Geliri', 'İkramiye', 'Hediye', 'Diğer Gelir',
];

const EXPENSE_CATS = [
  'Market', 'Fatura', 'Ulaşım', 'Sağlık', 'Eğlence',
  'Yemek/Restoran', 'Kira', 'Eğitim', 'Giyim', 'Abonelik',
  'Yakıt', 'Sigorta', 'Vergi', 'Kredi Kartı Ödemesi',
  'Ev Giderleri', 'Elektronik', 'Spor', 'Bakım/Kişisel',
  'Çocuk Giderleri', 'Diğer Gider',
];

export default function AddScreen() {
  const { activeProfile } = useAuthStore();
  const router = useRouter();
  const [type, setType] = useState<'gelir' | 'gider'>('gider');
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);

  const cats = type === 'gelir' ? INCOME_CATS : EXPENSE_CATS;

  useEffect(() => {
    setCategory(cats[0]);
  }, [type]);

  async function handleSave() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!amt || isNaN(amt) || amt <= 0) {
      Alert.alert('Hata', 'Geçerli bir tutar girin');
      return;
    }
    if (!category) {
      Alert.alert('Hata', 'Kategori seçin');
      return;
    }
    setLoading(true);
    try {
      await api.transactions.create({
        profile_id: activeProfile!.id,
        type,
        amount: amt,
        description: description.trim(),
        category,
        date,
      });
      setAmount('');
      setDescription('');
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
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={styles.header}>
            <Text style={styles.title}>İşlem Ekle</Text>
          </View>

          {/* Type Toggle */}
          <View style={styles.typeRow}>
            <TouchableOpacity
              style={[styles.typeBtn, type === 'gider' && styles.typeBtnActiveRed]}
              onPress={() => setType('gider')}
            >
              <Text style={[styles.typeText, type === 'gider' && styles.typeTextActive]}>
                Gider
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.typeBtn, type === 'gelir' && styles.typeBtnActiveGreen]}
              onPress={() => setType('gelir')}
            >
              <Text style={[styles.typeText, type === 'gelir' && styles.typeTextActive]}>
                Gelir
              </Text>
            </TouchableOpacity>
          </View>

          {/* Amount */}
          <View style={styles.amountBox}>
            <Text style={styles.currency}>₺</Text>
            <TextInput
              style={styles.amountInput}
              placeholder="0,00"
              placeholderTextColor={Colors.textMuted}
              value={amount}
              onChangeText={setAmount}
              keyboardType="decimal-pad"
              autoFocus
            />
          </View>

          {/* Description */}
          <View style={styles.field}>
            <Text style={styles.fieldLabel}>Açıklama</Text>
            <TextInput
              style={styles.input}
              placeholder="İsteğe bağlı"
              placeholderTextColor={Colors.textMuted}
              value={description}
              onChangeText={setDescription}
            />
          </View>

          {/* Date */}
          <View style={styles.field}>
            <Text style={styles.fieldLabel}>Tarih</Text>
            <TextInput
              style={styles.input}
              placeholder="YYYY-MM-DD"
              placeholderTextColor={Colors.textMuted}
              value={date}
              onChangeText={setDate}
            />
          </View>

          {/* Category */}
          <View style={styles.field}>
            <Text style={styles.fieldLabel}>Kategori</Text>
            <View style={styles.catGrid}>
              {cats.map((c) => (
                <TouchableOpacity
                  key={c}
                  style={[styles.catBtn, category === c && styles.catBtnActive]}
                  onPress={() => setCategory(c)}
                >
                  <Text style={[styles.catText, category === c && styles.catTextActive]}>
                    {c}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <TouchableOpacity
            style={[
              styles.saveBtn,
              { backgroundColor: type === 'gelir' ? Colors.green : Colors.primary },
              loading && styles.saveBtnDisabled,
            ]}
            onPress={handleSave}
            disabled={loading}
          >
            {loading
              ? <ActivityIndicator color={Colors.white} />
              : <Text style={styles.saveBtnText}>Kaydet</Text>
            }
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  header: { paddingHorizontal: 16, paddingTop: 8, paddingBottom: 4 },
  title: { fontSize: 24, fontWeight: '800', color: Colors.textPrimary },
  typeRow: {
    flexDirection: 'row',
    marginHorizontal: 16,
    marginTop: 16,
    backgroundColor: Colors.bgInput,
    borderRadius: 14,
    padding: 4,
    gap: 4,
  },
  typeBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: 'center',
  },
  typeBtnActiveRed: { backgroundColor: Colors.red },
  typeBtnActiveGreen: { backgroundColor: Colors.green },
  typeText: { fontSize: 15, fontWeight: '600', color: Colors.textSecondary },
  typeTextActive: { color: Colors.white },
  amountBox: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginTop: 24,
    gap: 4,
  },
  currency: {
    fontSize: 32,
    fontWeight: '800',
    color: Colors.textSecondary,
  },
  amountInput: {
    flex: 1,
    fontSize: 48,
    fontWeight: '800',
    color: Colors.textPrimary,
    padding: 0,
  },
  field: { marginHorizontal: 16, marginTop: 20 },
  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  input: {
    backgroundColor: Colors.bgInput,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 13,
    fontSize: 15,
    color: Colors.textPrimary,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  catGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  catBtn: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor: Colors.bgInput,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  catBtnActive: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },
  catText: { fontSize: 13, color: Colors.textSecondary },
  catTextActive: { color: Colors.white, fontWeight: '600' },
  saveBtn: {
    marginHorizontal: 16,
    marginTop: 24,
    marginBottom: 40,
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
  },
  saveBtnDisabled: { opacity: 0.6 },
  saveBtnText: { fontSize: 16, fontWeight: '700', color: Colors.white },
});
