import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { C } from '../constants/Colors';
import { transactions, misc as miscApi } from '../services/api';

const GELIR = ['Maaş','Serbest Meslek','Kira Geliri','Yatırım Geliri / Satış','Yatırım / Temettü','Hediye / İkramiye','Hesaplar Arası Transfer','Diğer Gelir'];
const GIDER = ['Kira / Mortgage','Market / Gıda','Faturalar','Ulaşım','Yemek / Restoran','Eğlence','Sağlık','Giyim','Eğitim','Abonelikler','Elektronik','Sigorta','Vergi / Harç','Kredi Kartı Ödemesi','Yemek Kartı Ödemesi','Döviz Alımı','Altın Alımı','Yatırım Fonu','Hisse Senedi','Hesaplar Arası Transfer','Diğer Gider'];

export default function EditTxScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ id: string; type: string; amount: string; category: string; description: string; date: string; project_id: string }>();

  const [type,      setType]      = useState<'gelir'|'gider'>((params.type as any) || 'gider');
  const [amount,    setAmount]    = useState(params.amount || '');
  const [desc,      setDesc]      = useState(params.description || '');
  const [cat,       setCat]       = useState(params.category || '');
  const [date,      setDate]      = useState(params.date || '');
  const [projectId, setProjectId] = useState<number|null>(params.project_id ? parseInt(params.project_id) : null);
  const [projects,  setProjects]  = useState<any[]>([]);
  const [loading,   setLoading]   = useState(false);

  useEffect(() => {
    miscApi.projects().then((p: any) => setProjects(Array.isArray(p) ? p : [])).catch(() => {});
  }, []);

  const cats = type === 'gelir' ? GELIR : GIDER;

  async function save() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!amt || amt <= 0) { Alert.alert('Hata', 'Geçerli tutar girin'); return; }
    setLoading(true);
    const payload: Record<string, unknown> = { type, amount: amt, description: desc.trim(), category: cat, date };
    if (type === 'gider') payload.project_id = projectId ?? null;
    try {
      await transactions.update(parseInt(params.id), payload);
      Alert.alert('✅ Güncellendi', '', [{ text: 'Tamam', onPress: () => router.back() }]);
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
            <Text style={s.title}>İşlemi Düzenle</Text>
          </View>

          <View style={s.toggle}>
            {(['gider','gelir'] as const).map(t => (
              <TouchableOpacity key={t} style={[s.tBtn, type === t && (t === 'gelir' ? s.tGreen : s.tRed)]}
                onPress={() => { setType(t); if (!cats.includes(cat)) setCat(t === 'gelir' ? GELIR[0] : GIDER[0]); setProjectId(null); }}>
                <Text style={[s.tTxt, type === t && { color: C.white }]}>{t === 'gelir' ? '↑ Gelir' : '↓ Gider'}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={s.amtRow}>
            <Text style={s.curr}>₺</Text>
            <TextInput style={s.amtInput} placeholder="0,00" placeholderTextColor={C.muted} value={amount} onChangeText={setAmount} keyboardType="decimal-pad" />
          </View>

          <View style={s.field}><Text style={s.lbl}>Açıklama</Text>
            <TextInput style={s.input} placeholder="İsteğe bağlı" placeholderTextColor={C.muted} value={desc} onChangeText={setDesc} />
          </View>
          <View style={s.field}><Text style={s.lbl}>Tarih</Text>
            <TextInput style={s.input} placeholder="YYYY-MM-DD" placeholderTextColor={C.muted} value={date} onChangeText={setDate} />
          </View>

          {/* Proje seçici — gider türünde, proje varsa göster */}
          {type === 'gider' && projects.length > 0 && (
            <View style={s.field}>
              <Text style={s.lbl}>Proje <Text style={s.optional}>(isteğe bağlı)</Text></Text>
              <View style={s.projectList}>
                <TouchableOpacity
                  style={[s.projBtn, projectId === null && s.projBtnNone]}
                  onPress={() => setProjectId(null)}>
                  <Text style={[s.projTxt, projectId === null && { color: C.txt, fontWeight: '700' }]}>— Proje Yok</Text>
                </TouchableOpacity>
                {projects.map(p => (
                  <TouchableOpacity key={p.id}
                    style={[s.projBtn, projectId === p.id && s.projBtnActive]}
                    onPress={() => setProjectId(p.id)}>
                    <View style={[s.projDot, { backgroundColor: p.color ?? C.blue }]} />
                    <Text style={[s.projTxt, projectId === p.id && { color: C.white, fontWeight: '700' }]} numberOfLines={1}>
                      {p.name}
                    </Text>
                    {projectId === p.id && <Text style={{ color: C.white, fontSize: 16 }}>✓</Text>}
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          <View style={s.field}>
            <Text style={s.lbl}>Kategori</Text>
            <View style={s.catGrid}>
              {cats.map(c => (
                <TouchableOpacity key={c} style={[s.catBtn, cat === c && s.catA]} onPress={() => setCat(c)}>
                  <Text style={[s.catTxt, cat === c && { color: C.white, fontWeight: '600' }]}>{c}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <TouchableOpacity style={[s.saveBtn, loading && { opacity: 0.6 }]} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>💾 Güncelle</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:    { flex: 1, backgroundColor: C.bg },
  header:       { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:         { fontSize: 24, color: C.txt },
  title:        { fontSize: 22, fontWeight: '800', color: C.txt },
  toggle:       { flexDirection: 'row', margin: 16, backgroundColor: C.input, borderRadius: 14, padding: 4, gap: 4 },
  tBtn:         { flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: 'center' },
  tGreen:       { backgroundColor: C.green },
  tRed:         { backgroundColor: C.red },
  tTxt:         { fontSize: 15, fontWeight: '600', color: C.txt2 },
  amtRow:       { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, gap: 4 },
  curr:         { fontSize: 32, fontWeight: '800', color: C.txt2 },
  amtInput:     { flex: 1, fontSize: 48, fontWeight: '800', color: C.txt, padding: 0 },
  field:        { marginHorizontal: 16, marginTop: 20, gap: 6 },
  lbl:          { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  optional:     { fontWeight: '400', textTransform: 'none', letterSpacing: 0, fontSize: 11, color: C.muted },
  input:        { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  projectList:  { gap: 8 },
  projBtn:      { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border },
  projBtnNone:  { borderColor: C.muted },
  projBtnActive:{ backgroundColor: C.blue, borderColor: C.blue },
  projDot:      { width: 12, height: 12, borderRadius: 6, flexShrink: 0 },
  projTxt:      { fontSize: 14, color: C.txt2, flex: 1 },
  catGrid:      { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  catBtn:       { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: C.input, borderWidth: 1, borderColor: C.border },
  catA:         { backgroundColor: C.blue, borderColor: C.blue },
  catTxt:       { fontSize: 13, color: C.txt2 },
  saveBtn:      { margin: 16, marginTop: 24, marginBottom: 40, backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  saveTxt:      { fontSize: 16, fontWeight: '700', color: C.white },
});
