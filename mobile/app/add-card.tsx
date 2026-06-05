import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { C } from '../constants/Colors';
import { cards as cardsApi } from '../services/api';

const CARD_TYPES = [
  { key: 'kredi', label: '💳 Kredi Kartı' },
  { key: 'banka', label: '🏦 Banka Kartı' },
  { key: 'yemek', label: '🍽️ Yemek Kartı' },
  { key: 'hediye', label: '🎁 Hediye Kartı' },
];

export default function AddCardScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id?: string }>();
  const isEdit = !!params.id;

  const [bankName,     setBankName]     = useState('');
  const [cardName,     setCardName]     = useState('');
  const [limit,        setLimit]        = useState('');
  const [used,         setUsed]         = useState('0');
  const [dueDay,       setDueDay]       = useState('1');
  const [stmtDay,      setStmtDay]      = useState('20');
  const [minPct,       setMinPct]       = useState('25');
  const [cardType,     setCardType]     = useState('kredi');
  const [loading,      setLoading]      = useState(false);

  async function save() {
    if (!bankName.trim()) { Alert.alert('Hata', 'Banka adı gerekli'); return; }
    const lim = parseFloat(limit.replace(',', '.'));
    if (cardType !== 'yemek' && cardType !== 'hediye' && (!lim || lim <= 0)) {
      Alert.alert('Hata', 'Geçerli bir limit girin'); return;
    }
    setLoading(true);
    try {
      await cardsApi.create({
        bank_name:     bankName.trim(),
        card_name:     cardName.trim(),
        limit_:        lim || 0,
        used_:         parseFloat(used.replace(',', '.')) || 0,
        due_day:       parseInt(dueDay) || 1,
        statement_day: parseInt(stmtDay) || 20,
        min_pct:       parseFloat(minPct) || 25,
        card_type:     cardType,
      });
      Alert.alert('✅ Kart Eklendi', '', [
        { text: 'Kartlara Dön', onPress: () => router.back() },
        { text: 'Yeni Kart Ekle', onPress: () => {
          setBankName(''); setCardName(''); setLimit(''); setUsed('0');
        }},
      ]);
    } catch (e: any) {
      Alert.alert('Hata', e.message);
    } finally { setLoading(false); }
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView showsVerticalScrollIndicator={false}>
          <View style={s.header}>
            <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
            <Text style={s.title}>Kart Ekle</Text>
          </View>

          {/* Kart Tipi */}
          <View style={s.section}>
            <Text style={s.sLabel}>Kart Tipi</Text>
            <View style={s.typeGrid}>
              {CARD_TYPES.map(t => (
                <TouchableOpacity key={t.key} style={[s.typeBtn, cardType === t.key && s.typeActive]} onPress={() => setCardType(t.key)}>
                  <Text style={[s.typeTxt, cardType === t.key && s.typeTxtA]}>{t.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Banka ve Kart Adı */}
          <View style={s.section}>
            <Field label="Banka Adı *" value={bankName} onChange={setBankName} placeholder="Garanti BBVA" />
            <Field label="Kart Adı" value={cardName} onChange={setCardName} placeholder="Bonus Card" />
          </View>

          {/* Limitler */}
          <View style={s.section}>
            <Text style={s.sLabel}>Tutar Bilgileri</Text>
            <Field label="Limit (₺)" value={limit} onChange={setLimit} placeholder="10000" keyboard="decimal-pad" />
            <Field label="Mevcut Borç (₺)" value={used} onChange={setUsed} placeholder="0" keyboard="decimal-pad" />
          </View>

          {/* Tarihler */}
          <View style={s.section}>
            <Text style={s.sLabel}>Ödeme Bilgileri</Text>
            <View style={s.row2}>
              <View style={{ flex: 1 }}>
                <Field label="Ekstre Günü" value={stmtDay} onChange={setStmtDay} placeholder="20" keyboard="number-pad" />
              </View>
              <View style={{ flex: 1 }}>
                <Field label="Son Ödeme Günü" value={dueDay} onChange={setDueDay} placeholder="1" keyboard="number-pad" />
              </View>
            </View>
            <Field label="Asgari Ödeme (%)" value={minPct} onChange={setMinPct} placeholder="25" keyboard="decimal-pad" />
          </View>

          <TouchableOpacity style={[s.saveBtn, loading && { opacity: 0.6 }]} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>💳 Kartı Ekle</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

function Field({ label, value, onChange, placeholder, keyboard }: any) {
  return (
    <View style={s.field}>
      <Text style={s.fLabel}>{label}</Text>
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
  section:   { marginHorizontal: 16, marginTop: 20, gap: 12 },
  sLabel:    { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 1 },
  typeGrid:  { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  typeBtn:   { paddingHorizontal: 14, paddingVertical: 9, borderRadius: 12, backgroundColor: C.card, borderWidth: 1, borderColor: C.border },
  typeActive:{ backgroundColor: C.blue, borderColor: C.blue },
  typeTxt:   { fontSize: 14, color: C.txt2 },
  typeTxtA:  { color: C.white, fontWeight: '600' },
  field:     { gap: 6 },
  fLabel:    { fontSize: 12, fontWeight: '600', color: C.txt2 },
  input:     { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  row2:      { flexDirection: 'row', gap: 12 },
  saveBtn:   { margin: 16, marginTop: 24, marginBottom: 40, backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  saveTxt:   { fontSize: 16, fontWeight: '700', color: C.white },
});
