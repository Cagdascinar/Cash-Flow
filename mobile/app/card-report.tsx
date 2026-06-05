import {
  View, Text, StyleSheet, ActivityIndicator, TouchableOpacity,
  ScrollView, RefreshControl, TextInput, Alert,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { cards as cardsApi } from '../services/api';

export default function CardReportScreen() {
  const router = useRouter();
  const [report,  setReport]  = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [inputs,  setInputs]  = useState<Record<number, string>>({});
  const [saving,  setSaving]  = useState<number | null>(null);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const d = await cardsApi.dailyReport() as any;
      setReport(Array.isArray(d) ? d : (d.cards ?? []));
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function saveBalance(cardId: number) {
    const val = parseFloat((inputs[cardId] || '').replace(',', '.'));
    if (!val && val !== 0) { Alert.alert('Hata', 'Geçerli bakiye girin'); return; }
    setSaving(cardId);
    try {
      await cardsApi.addDailyBalance(cardId, val);
      Alert.alert('✅ Kaydedildi');
      load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(null); }
  }

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Günlük Kart Raporu</Text>
      </View>
      <Text style={s.info}>Her gün kartınızın güncel bakiyesini girin. Sistem otomatik olarak bir önceki günle karşılaştırır.</Text>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>
            {report.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>💳</Text><Text style={s.emptyTxt}>Kart bulunamadı</Text></View>
              : report.map((c: any) => {
                  const diff = c.today_balance != null && c.yesterday_balance != null
                    ? c.today_balance - c.yesterday_balance : null;
                  return (
                    <View key={c.card_id} style={s.card}>
                      <View style={s.cardTop}>
                        <Text style={s.bankName}>{c.bank_name}</Text>
                        <Text style={s.cardName}>{c.card_name}</Text>
                      </View>
                      <View style={s.balRow}>
                        <View style={s.balItem}>
                          <Text style={s.balLbl}>Dün</Text>
                          <Text style={s.balVal}>{c.yesterday_balance != null ? money(c.yesterday_balance) : '—'}</Text>
                        </View>
                        <View style={s.balItem}>
                          <Text style={s.balLbl}>Bugün</Text>
                          <Text style={s.balVal}>{c.today_balance != null ? money(c.today_balance) : '—'}</Text>
                        </View>
                        {diff != null && (
                          <View style={s.balItem}>
                            <Text style={s.balLbl}>Fark</Text>
                            <Text style={[s.balVal, { color: diff > 0 ? C.red : C.green }]}>
                              {diff > 0 ? '+' : ''}{money(diff)}
                            </Text>
                          </View>
                        )}
                      </View>
                      <View style={s.inputRow}>
                        <TextInput
                          style={s.input}
                          value={inputs[c.card_id] || ''}
                          onChangeText={v => setInputs(prev => ({ ...prev, [c.card_id]: v }))}
                          placeholder="Bugünkü bakiye"
                          placeholderTextColor={C.muted}
                          keyboardType="decimal-pad"
                        />
                        <TouchableOpacity
                          style={[s.saveBtn, saving === c.card_id && { opacity: 0.6 }]}
                          onPress={() => saveBalance(c.card_id)}
                          disabled={saving === c.card_id}
                        >
                          <Text style={s.saveTxt}>{saving === c.card_id ? '...' : 'Kaydet'}</Text>
                        </TouchableOpacity>
                      </View>
                    </View>
                  );
                })
            }
            <View style={{ height: 40 }} />
          </ScrollView>
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:       { flex: 1, backgroundColor: C.bg },
  center:   { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:   { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:     { fontSize: 24, color: C.txt },
  title:    { fontSize: 20, fontWeight: '800', color: C.txt },
  info:     { marginHorizontal: 16, marginTop: 8, marginBottom: 4, fontSize: 13, color: C.txt2, lineHeight: 20 },
  card:     { marginHorizontal: 16, marginTop: 12, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  cardTop:  { marginBottom: 10 },
  bankName: { fontSize: 15, fontWeight: '700', color: C.txt },
  cardName: { fontSize: 12, color: C.txt2, marginTop: 2 },
  balRow:   { flexDirection: 'row', gap: 8, marginBottom: 12 },
  balItem:  { flex: 1, backgroundColor: C.input, borderRadius: 10, padding: 10, alignItems: 'center' },
  balLbl:   { fontSize: 11, color: C.muted },
  balVal:   { fontSize: 14, fontWeight: '700', color: C.txt, marginTop: 3 },
  inputRow: { flexDirection: 'row', gap: 8 },
  input:    { flex: 1, backgroundColor: C.input, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10, fontSize: 14, color: C.txt, borderWidth: 1, borderColor: C.border },
  saveBtn:  { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 16, paddingVertical: 10, justifyContent: 'center' },
  saveTxt:  { fontSize: 13, fontWeight: '700', color: C.white },
  empty:    { alignItems: 'center', paddingVertical: 48 },
  emptyIco: { fontSize: 48, marginBottom: 12 },
  emptyTxt: { fontSize: 15, color: C.txt2 },
});
