import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ScrollView, Alert, ActivityIndicator, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../../constants/Colors';
import { transactions, accounts as accountsApi, cards as cardsApi, misc as miscApi } from '../../services/api';

const GELIR = ['Maaş','Serbest Meslek','Kira Geliri','Yatırım Geliri / Satış','Yatırım / Temettü','Hediye / İkramiye','Hesaplar Arası Transfer','Diğer Gelir'];
const GIDER = ['Kira / Mortgage','Market / Gıda','Faturalar','Ulaşım','Yemek / Restoran','Eğlence','Sağlık','Giyim','Eğitim','Abonelikler','Elektronik','Sigorta','Vergi / Harç','Kredi Kartı Ödemesi','Yemek Kartı Ödemesi','Döviz Alımı','Altın Alımı','Yatırım Fonu','Hisse Senedi','Hesaplar Arası Transfer','Diğer Gider'];

type PayMethod = 'nakit' | 'hesap' | 'kart';

export default function AddScreen() {
  const router = useRouter();
  const [type,      setType]      = useState<'gider'|'gelir'>('gider');
  const [amount,    setAmount]    = useState('');
  const [desc,      setDesc]      = useState('');
  const [cat,       setCat]       = useState(GIDER[0]);
  const [date,      setDate]      = useState(new Date().toISOString().split('T')[0]);
  const [payMethod, setPayMethod] = useState<PayMethod>('nakit');
  const [accountId, setAccountId] = useState<number|null>(null);
  const [cardId,    setCardId]    = useState<number|null>(null);
  const [projectId, setProjectId] = useState<number|null>(null);
  const [accounts,  setAccounts]  = useState<any[]>([]);
  const [cards,     setCards]     = useState<any[]>([]);
  const [projects,  setProjects]  = useState<any[]>([]);
  const [loading,   setLoading]   = useState(false);

  useEffect(() => {
    Promise.all([accountsApi.list(), cardsApi.list(), miscApi.projects()])
      .then(([acc, crd, prj]) => {
        setAccounts(Array.isArray(acc) ? acc.filter((a:any) => !['kredi_karti','kmh'].includes(a.type)) : []);
        setCards(Array.isArray(crd) ? crd : []);
        setProjects(Array.isArray(prj) ? prj : []);
      }).catch(() => {});
  }, []);

  const cats = type === 'gelir' ? GELIR : GIDER;

  async function save() {
    const amt = parseFloat(amount.replace(',', '.'));
    if (!amt || isNaN(amt) || amt <= 0) { Alert.alert('Hata', 'Geçerli tutar girin'); return; }
    const payload: Record<string, unknown> = { type, amount: amt, description: desc.trim(), category: cat, date };
    if (payMethod === 'hesap' && accountId) payload.account_id = accountId;
    if (payMethod === 'kart'  && cardId)    payload.card_id    = cardId;
    if (type === 'gider' && projectId)      payload.project_id  = projectId;

    setLoading(true);
    try {
      await transactions.create(payload);
      Alert.alert('✅ Kaydedildi', '', [
        { text: 'Ana Sayfa', onPress: () => router.replace('/(tabs)') },
        { text: 'Yeni Ekle', onPress: () => { setAmount(''); setDesc(''); setProjectId(null); } },
      ]);
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setLoading(false); }
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView showsVerticalScrollIndicator={false}>

          <View style={s.header}><Text style={s.title}>İşlem Ekle</Text></View>

          {/* Gelir / Gider */}
          <View style={s.toggle}>
            {(['gider','gelir'] as const).map(t => (
              <TouchableOpacity key={t} style={[s.tBtn, type === t && (t === 'gelir' ? s.tGreen : s.tRed)]}
                onPress={() => { setType(t); setCat(t === 'gelir' ? GELIR[0] : GIDER[0]); setProjectId(null); }}>
                <Text style={[s.tTxt, type === t && { color: C.white }]}>{t === 'gelir' ? '↑  Gelir' : '↓  Gider'}</Text>
              </TouchableOpacity>
            ))}
          </View>

          {/* Tutar */}
          <View style={s.amtRow}>
            <Text style={s.curr}>₺</Text>
            <TextInput style={s.amtInput} placeholder="0,00" placeholderTextColor={C.muted} value={amount} onChangeText={setAmount} keyboardType="decimal-pad" autoFocus />
          </View>

          {/* Ödeme Yöntemi */}
          <View style={s.field}>
            <Text style={s.lbl}>Ödeme Yöntemi</Text>
            <View style={s.methods}>
              {([['nakit','💵 Nakit'],['hesap','🏦 Hesap'],['kart','💳 Kart']] as [PayMethod,string][]).map(([k,l]) => (
                <TouchableOpacity key={k} style={[s.methBtn, payMethod === k && s.methA]} onPress={() => setPayMethod(k)}>
                  <Text style={[s.methTxt, payMethod === k && { color: C.white }]}>{l}</Text>
                </TouchableOpacity>
              ))}
            </View>

            {payMethod === 'hesap' && accounts.length > 0 && (
              <View style={s.subList}>
                {accounts.map(a => (
                  <TouchableOpacity key={a.id} style={[s.subBtn, accountId === a.id && s.subA]} onPress={() => setAccountId(a.id)}>
                    <View style={[s.subDot, { backgroundColor: a.color ?? C.blue }]} />
                    <Text style={[s.subTxt, accountId === a.id && { color: C.white }]}>{a.name}</Text>
                    <Text style={[s.subVal, accountId === a.id && { color: 'rgba(255,255,255,.6)' }]}>{money(a.computed_balance ?? 0)}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {payMethod === 'kart' && cards.length > 0 && (
              <View style={s.subList}>
                {cards.map(c => (
                  <TouchableOpacity key={c.id} style={[s.subBtn, cardId === c.id && s.subA]} onPress={() => setCardId(c.id)}>
                    <Text style={[s.subTxt, cardId === c.id && { color: C.white }]}>💳 {c.bank_name} {c.card_name}</Text>
                    <Text style={[s.subVal, cardId === c.id && { color: 'rgba(255,255,255,.6)' }]}>{money(c.used_)} borç</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Açıklama</Text>
            <TextInput style={s.input} placeholder="İsteğe bağlı" placeholderTextColor={C.muted} value={desc} onChangeText={setDesc} />
          </View>

          <View style={s.field}>
            <Text style={s.lbl}>Tarih</Text>
            <TextInput style={s.input} placeholder="YYYY-MM-DD" placeholderTextColor={C.muted} value={date} onChangeText={setDate} />
          </View>

          {/* Proje — gider türünde proje varsa göster */}
          {type === 'gider' && projects.length > 0 && (
            <View style={s.field}>
              <Text style={s.lbl}>Proje <Text style={s.optional}>(isteğe bağlı)</Text></Text>
              <View style={s.projectList}>
                {/* Proje seçimini kaldır */}
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
                    <View style={{ flex: 1 }}>
                      <Text style={[s.projTxt, projectId === p.id && { color: C.white, fontWeight: '700' }]} numberOfLines={1}>
                        {p.name}
                      </Text>
                      {p.budget > 0 && (
                        <Text style={[s.projSub, projectId === p.id && { color: 'rgba(255,255,255,.6)' }]}>
                          {money(p.spent)} / {money(p.budget)}
                        </Text>
                      )}
                    </View>
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

          <TouchableOpacity style={[s.saveBtn, { backgroundColor: type === 'gelir' ? C.green : C.blue }, loading && { opacity: 0.6 }]} onPress={save} disabled={loading}>
            {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>Kaydet</Text>}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: C.bg },
  header:      { paddingHorizontal: 16, paddingTop: 8 },
  title:       { fontSize: 24, fontWeight: '800', color: C.txt },
  toggle:      { flexDirection: 'row', margin: 16, backgroundColor: C.input, borderRadius: 14, padding: 4, gap: 4 },
  tBtn:        { flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: 'center' },
  tGreen:      { backgroundColor: C.green },
  tRed:        { backgroundColor: C.red },
  tTxt:        { fontSize: 15, fontWeight: '600', color: C.txt2 },
  amtRow:      { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, gap: 4 },
  curr:        { fontSize: 32, fontWeight: '800', color: C.txt2 },
  amtInput:    { flex: 1, fontSize: 48, fontWeight: '800', color: C.txt, padding: 0 },
  field:       { marginHorizontal: 16, marginTop: 20, gap: 8 },
  lbl:         { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  optional:    { fontWeight: '400', textTransform: 'none', letterSpacing: 0, fontSize: 11, color: C.muted },
  methods:     { flexDirection: 'row', gap: 8 },
  methBtn:     { flex: 1, paddingVertical: 9, borderRadius: 10, backgroundColor: C.card, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  methA:       { backgroundColor: C.blue, borderColor: C.blue },
  methTxt:     { fontSize: 13, fontWeight: '600', color: C.txt2 },
  subList:     { gap: 8, marginTop: 4 },
  subBtn:      { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: C.card, borderRadius: 10, padding: 10, borderWidth: 1, borderColor: C.border },
  subA:        { backgroundColor: C.blue, borderColor: C.blue },
  subDot:      { width: 10, height: 10, borderRadius: 5 },
  subTxt:      { flex: 1, fontSize: 13, fontWeight: '600', color: C.txt },
  subVal:      { fontSize: 12, color: C.txt2 },
  input:       { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  projectList: { gap: 8 },
  projBtn:     { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border },
  projBtnNone: { borderColor: C.muted },
  projBtnActive:{ backgroundColor: C.blue, borderColor: C.blue },
  projDot:     { width: 12, height: 12, borderRadius: 6, flexShrink: 0 },
  projTxt:     { fontSize: 14, color: C.txt2, flex: 1 },
  projSub:     { fontSize: 11, color: C.txt2, marginTop: 2 },
  catGrid:     { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  catBtn:      { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: C.input, borderWidth: 1, borderColor: C.border },
  catA:        { backgroundColor: C.blue, borderColor: C.blue },
  catTxt:      { fontSize: 13, color: C.txt2 },
  saveBtn:     { marginHorizontal: 16, marginTop: 24, marginBottom: 40, paddingVertical: 16, borderRadius: 14, alignItems: 'center' },
  saveTxt:     { fontSize: 16, fontWeight: '700', color: C.white },
});
