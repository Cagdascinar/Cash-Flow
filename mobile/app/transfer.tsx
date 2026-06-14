import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { accounts as accountsApi, misc } from '../services/api';

export default function TransferScreen() {
  const router = useRouter();
  const [accs,    setAccs]    = useState<any[]>([]);
  const [fromId,  setFromId]  = useState<number | null>(null);
  const [toId,    setToId]    = useState<number | null>(null);
  const [amount,  setAmount]  = useState('');
  const [desc,    setDesc]    = useState('');
  const [date,    setDate]    = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    accountsApi.list().then(d => setAccs(Array.isArray(d) ? d.filter((a:any) => !['kredi_karti','kmh'].includes(a.type)) : [])).catch(() => {});
  }, []);

  async function save() {
    const amt = parseFloat(amount.replace(',','.'));
    if (!fromId || !toId) { Alert.alert('Hata', 'Kaynak ve hedef hesap seçin'); return; }
    if (fromId === toId) { Alert.alert('Hata', 'Aynı hesabı seçemezsiniz'); return; }
    if (!amt || amt <= 0) { Alert.alert('Hata', 'Geçerli tutar girin'); return; }
    setLoading(true);
    try {
      await misc.transfer({ from_account_id: fromId, to_account_id: toId, amount: amt, description: desc.trim() || 'Hesaplar Arası Transfer', date });
      Alert.alert('✅ Transfer Yapıldı', '', [{ text: 'Tamam', onPress: () => router.back() }]);
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setLoading(false); }
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
        <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingBottom: 40 }}>
          <View style={s.header}>
            <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
            <Text style={s.title}>Hesaplar Arası Transfer</Text>
          </View>

          <View style={s.amtRow}>
            <Text style={s.curr}>₺</Text>
            <TextInput style={s.amtInput} placeholder="0,00" placeholderTextColor={C.muted} value={amount} onChangeText={setAmount} keyboardType="decimal-pad" autoFocus />
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Kaynak Hesap (Çıkan)</Text>
            <View style={s.accList}>
              {accs.map(a => (
                <TouchableOpacity key={a.id} style={[s.accBtn, fromId === a.id && s.accActive]} onPress={() => setFromId(a.id)}>
                  <View style={[s.accDot, { backgroundColor: a.color ?? C.blue }]} />
                  <View style={{ flex: 1 }}>
                    <Text style={[s.accName, fromId === a.id && { color: C.white }]}>{a.name}</Text>
                    <Text style={[s.accBank, fromId === a.id && { color: 'rgba(255,255,255,.6)' }]}>{a.bank} · {money(a.computed_balance ?? 0)}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <View style={s.arrow}><Text style={s.arrowTxt}>↓</Text></View>

          <View style={s.field}>
            <Text style={s.lbl}>Hedef Hesap (Giren)</Text>
            <View style={s.accList}>
              {accs.filter(a => a.id !== fromId).map(a => (
                <TouchableOpacity key={a.id} style={[s.accBtn, toId === a.id && s.accActive]} onPress={() => setToId(a.id)}>
                  <View style={[s.accDot, { backgroundColor: a.color ?? C.blue }]} />
                  <View style={{ flex: 1 }}>
                    <Text style={[s.accName, toId === a.id && { color: C.white }]}>{a.name}</Text>
                    <Text style={[s.accBank, toId === a.id && { color: 'rgba(255,255,255,.6)' }]}>{a.bank} · {money(a.computed_balance ?? 0)}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Açıklama</Text>
            <TextInput style={s.input} placeholder="İsteğe bağlı" placeholderTextColor={C.muted} value={desc} onChangeText={setDesc} />
          </View>
          <View style={s.field}>
            <Text style={s.lbl}>Tarih</Text>
            <TextInput style={s.input} placeholder="YYYY-MM-DD" placeholderTextColor={C.muted} value={date} onChangeText={setDate} />
          </View>

          <TouchableOpacity style={[s.saveBtn, loading && { opacity: 0.6 }]} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>🔄 Transferi Yap</Text>}
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
  title:     { fontSize: 20, fontWeight: '800', color: C.txt },
  amtRow:    { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginTop: 16, gap: 4 },
  curr:      { fontSize: 32, fontWeight: '800', color: C.txt2 },
  amtInput:  { flex: 1, fontSize: 48, fontWeight: '800', color: C.txt, padding: 0 },
  field:     { marginHorizontal: 16, marginTop: 20, gap: 8 },
  lbl:       { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  accList:   { gap: 8 },
  accBtn:    { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border },
  accActive: { backgroundColor: C.blue, borderColor: C.blue },
  accDot:    { width: 12, height: 12, borderRadius: 6 },
  accName:   { fontSize: 14, fontWeight: '600', color: C.txt },
  accBank:   { fontSize: 12, color: C.txt2, marginTop: 2 },
  arrow:     { alignItems: 'center', paddingVertical: 8 },
  arrowTxt:  { fontSize: 28, color: C.txt2 },
  input:     { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  saveBtn:   { margin: 16, marginTop: 24, marginBottom: 40, backgroundColor: C.green, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  saveTxt:   { fontSize: 16, fontWeight: '700', color: C.white },
});
