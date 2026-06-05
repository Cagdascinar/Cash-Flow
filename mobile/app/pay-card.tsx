import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  Alert, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView,
} from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { C, money } from '../constants/Colors';
import { cards as cardsApi } from '../services/api';

export default function PayCardScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id: string; bank: string; name: string; used: string; min: string }>();
  const [amount,  setAmount]  = useState(params.min || '');
  const [date,    setDate]    = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);

  async function pay() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!amt || amt <= 0) { Alert.alert('Hata', 'Geçerli tutar girin'); return; }
    setLoading(true);
    try {
      await cardsApi.pay(parseInt(params.id), { amount: amt, date });
      Alert.alert('✅ Ödeme Yapıldı', `${money(amt)} ödeme kaydedildi`, [
        { text: 'Tamam', onPress: () => router.back() },
      ]);
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setLoading(false); }
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={s.header}>
            <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
            <Text style={s.title}>Kart Ödemesi</Text>
          </View>

          <View style={s.cardInfo}>
            <Text style={s.cardIco}>💳</Text>
            <Text style={s.cardName}>{params.bank} · {params.name}</Text>
            <Text style={s.cardDebt}>Mevcut borç: {money(parseFloat(params.used || '0'))}</Text>
            {params.min && parseFloat(params.min) > 0 && (
              <Text style={s.cardMin}>Asgari ödeme: {money(parseFloat(params.min))}</Text>
            )}
          </View>

          <View style={s.amtRow}>
            <Text style={s.curr}>₺</Text>
            <TextInput style={s.amtInput} placeholder="0,00" placeholderTextColor={C.muted} value={amount} onChangeText={setAmount} keyboardType="decimal-pad" autoFocus />
          </View>

          {/* Hızlı tutar butonları */}
          {params.min && (
            <View style={s.quickRow}>
              <TouchableOpacity style={s.quickBtn} onPress={() => setAmount(params.min)}>
                <Text style={s.quickTxt}>Asgari</Text>
                <Text style={s.quickVal}>{money(parseFloat(params.min))}</Text>
              </TouchableOpacity>
              <TouchableOpacity style={s.quickBtn} onPress={() => setAmount(params.used)}>
                <Text style={s.quickTxt}>Tamamı</Text>
                <Text style={s.quickVal}>{money(parseFloat(params.used))}</Text>
              </TouchableOpacity>
            </View>
          )}

          <View style={s.field}>
            <Text style={s.lbl}>Ödeme Tarihi</Text>
            <TextInput style={s.input} value={date} onChangeText={setDate} placeholder="YYYY-MM-DD" placeholderTextColor={C.muted} />
          </View>

          <TouchableOpacity style={[s.payBtn, loading && { opacity: 0.6 }]} onPress={pay} disabled={loading}>
            {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.payTxt}>💳 Ödemeyi Yap</Text>}
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
  cardInfo:  { margin: 16, backgroundColor: C.hero, borderRadius: 16, padding: 20, borderWidth: 1, borderColor: 'rgba(99,160,255,.15)', alignItems: 'center' },
  cardIco:   { fontSize: 36, marginBottom: 8 },
  cardName:  { fontSize: 16, fontWeight: '700', color: C.white, marginBottom: 4 },
  cardDebt:  { fontSize: 14, color: 'rgba(255,255,255,.6)' },
  cardMin:   { fontSize: 13, color: C.yellow, marginTop: 4 },
  amtRow:    { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, gap: 4 },
  curr:      { fontSize: 32, fontWeight: '800', color: C.txt2 },
  amtInput:  { flex: 1, fontSize: 48, fontWeight: '800', color: C.txt, padding: 0 },
  quickRow:  { flexDirection: 'row', marginHorizontal: 16, gap: 8, marginTop: 12 },
  quickBtn:  { flex: 1, backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  quickTxt:  { fontSize: 12, color: C.txt2 },
  quickVal:  { fontSize: 15, fontWeight: '700', color: C.txt, marginTop: 2 },
  field:     { marginHorizontal: 16, marginTop: 20, gap: 6 },
  lbl:       { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  input:     { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  payBtn:    { margin: 16, marginTop: 24, marginBottom: 40, backgroundColor: C.green, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  payTxt:    { fontSize: 16, fontWeight: '700', color: C.white },
});
