import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Alert, ActivityIndicator, ScrollView, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { budgets } from '../services/api';

const CATS = [
  'Kira / Mortgage','Market / Gıda','Faturalar','Ulaşım','Yemek / Restoran',
  'Eğlence','Sağlık','Giyim','Eğitim','Abonelikler','Elektronik',
  'Sigorta','Vergi / Harç','Kredi Kartı Ödemesi','Yemek Kartı Ödemesi',
  'Diğer Gider',
];

export default function SetBudgetScreen() {
  const router = useRouter();
  const [limits,  setLimits]  = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  function setLimit(cat: string, val: string) {
    setLimits(prev => ({ ...prev, [cat]: val }));
  }

  async function save() {
    const data: Record<string, number> = {};
    Object.entries(limits).forEach(([cat, val]) => {
      const n = parseFloat(val.replace(',', '.'));
      if (n > 0) data[cat] = n;
    });
    if (Object.keys(data).length === 0) { Alert.alert('Hata', 'En az bir kategori için limit girin'); return; }
    setLoading(true);
    try {
      await budgets.save(data);
      Alert.alert('✅ Bütçe Limitleri Kaydedildi', '', [{ text: 'Tamam', onPress: () => router.back() }]);
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setLoading(false); }
  }

  const filledCount = Object.values(limits).filter(v => parseFloat(v) > 0).length;

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <View style={s.header}>
          <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
          <View style={{ flex: 1 }}>
            <Text style={s.title}>Bütçe Limitlerini Ayarla</Text>
            <Text style={s.sub}>{filledCount} kategori ayarlandı</Text>
          </View>
        </View>

        <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
          <Text style={s.info}>💡 Limit koyduğunuz kategoriler bütçe ekranında takip edilir. Boş bıraktıklarınız gösterilmez.</Text>
          {CATS.map(cat => (
            <View key={cat} style={s.row}>
              <Text style={s.catName}>{cat}</Text>
              <View style={s.inputWrap}>
                <Text style={s.prefix}>₺</Text>
                <TextInput
                  style={s.input}
                  value={limits[cat] || ''}
                  onChangeText={v => setLimit(cat, v)}
                  placeholder="Limit yok"
                  placeholderTextColor={C.muted}
                  keyboardType="decimal-pad"
                />
              </View>
            </View>
          ))}

          <TouchableOpacity style={[s.btn, loading && { opacity: 0.6 }]} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.btnTxt}>💾 Limitleri Kaydet</Text>}
          </TouchableOpacity>
          <View style={{ height: 40 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  header:    { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8, gap: 12 },
  back:      { fontSize: 24, color: C.txt },
  title:     { fontSize: 20, fontWeight: '800', color: C.txt },
  sub:       { fontSize: 12, color: C.txt2, marginTop: 2 },
  info:      { marginHorizontal: 16, marginTop: 8, marginBottom: 12, backgroundColor: 'rgba(0,122,255,.1)', borderRadius: 12, padding: 12, fontSize: 13, color: C.blue, lineHeight: 20 },
  row:       { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 10, gap: 12 },
  catName:   { flex: 1, fontSize: 14, color: C.txt },
  inputWrap: { flexDirection: 'row', alignItems: 'center', backgroundColor: C.card, borderRadius: 10, borderWidth: 1, borderColor: C.border, paddingHorizontal: 10 },
  prefix:    { fontSize: 14, color: C.txt2 },
  input:     { width: 90, paddingVertical: 9, fontSize: 14, color: C.txt },
  btn:       { marginHorizontal: 16, marginTop: 16, backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  btnTxt:    { fontSize: 16, fontWeight: '700', color: C.white },
});
