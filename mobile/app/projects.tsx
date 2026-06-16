import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { misc as miscApi } from '../services/api';
import { SwipeableRow } from '../components/SwipeableRow';

const COLORS = ['#007aff','#0ecb81','#f0b90b','#f6465d','#9b59b6','#ff6b35','#1abc9c'];

export default function ProjectsScreen() {
  const router = useRouter();
  const [list,    setList]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [modal,   setModal]   = useState(false);
  const [saving,  setSaving]  = useState(false);

  const [name,   setName]   = useState('');
  const [color,  setColor]  = useState('#007aff');
  const [budget, setBudget] = useState('');
  const [desc,   setDesc]   = useState('');

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setList((await miscApi.projects() as any[]) || []); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  function resetForm() { setName(''); setColor('#007aff'); setBudget(''); setDesc(''); }

  async function save() {
    if (!name.trim()) { Alert.alert('Hata', 'Ad zorunlu'); return; }
    setSaving(true);
    try {
      await miscApi.addProject({
        name: name.trim(), color, description: desc.trim(),
        budget: parseFloat(budget.replace(',', '.')) || 0,
      });
      setModal(false); resetForm(); load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function del(id: number) {
    Alert.alert('Sil', 'Bu proje silinsin mi? (İşlemler etkilenmez)', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await miscApi.deleteProject(id); setList(p => p.filter(x => x.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Projeler</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => { resetForm(); setModal(true); }}>
          <Text style={s.addTxt}>+ Ekle</Text>
        </TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>
            {list.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>📁</Text><Text style={s.emptyTxt}>Proje eklenmedi</Text></View>
              : list.map(p => {
                  const pct = p.budget > 0 ? Math.min(100, Math.round(p.spent / p.budget * 100)) : 0;
                  const barColor = pct > 90 ? C.red : pct > 70 ? C.yellow : C.green;
                  return (
                    <SwipeableRow
                      key={p.id}
                      style={{ marginHorizontal: 16, marginBottom: 10, marginTop: 8, borderRadius: 14 }}
                      actions={[{ label: 'Sil', icon: '🗑️', color: '#dc2626', onPress: () => del(p.id) }]}
                    >
                      <View style={s.card}>
                        <View style={s.cardTop}>
                          <View style={[s.dot, { backgroundColor: p.color }]} />
                          <Text style={s.name} numberOfLines={1}>{p.name}</Text>
                        </View>
                        {p.description ? <Text style={s.desc}>{p.description}</Text> : null}
                        <View style={s.stats}>
                          <Text style={s.statTxt}>Harcanan: <Text style={{ color: C.txt, fontWeight: '700' }}>{money(p.spent)}</Text></Text>
                          {p.budget > 0 && <Text style={s.statTxt}>Bütçe: <Text style={{ fontWeight: '700' }}>{money(p.budget)}</Text></Text>}
                        </View>
                        {p.budget > 0 && (
                          <View style={s.barBg}>
                            <View style={[s.barFill, { width: `${pct}%` as any, backgroundColor: barColor }]} />
                          </View>
                        )}
                      </View>
                    </SwipeableRow>
                  );
                })
            }
            <View style={{ height: 40 }} />
          </ScrollView>
      }

      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Proje Ekle</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }}>
              <Text style={s.mLbl}>Proje Adı *</Text>
              <TextInput style={s.mInput} value={name} onChangeText={setName} placeholder="Ofis Tadilat" placeholderTextColor={C.muted} />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Renk</Text>
              <View style={{ flexDirection: 'row', gap: 10, flexWrap: 'wrap' }}>
                {COLORS.map(c => (
                  <TouchableOpacity key={c} onPress={() => setColor(c)}
                    style={[s.colorDot, { backgroundColor: c }, color === c && s.colorDotActive]} />
                ))}
              </View>

              <Text style={[s.mLbl, { marginTop: 14 }]}>Bütçe (₺)</Text>
              <TextInput style={s.mInput} value={budget} onChangeText={setBudget} placeholder="50.000,00" placeholderTextColor={C.muted} keyboardType="decimal-pad" />

              <Text style={[s.mLbl, { marginTop: 14 }]}>Açıklama</Text>
              <TextInput style={s.mInput} value={desc} onChangeText={setDesc} placeholder="İsteğe bağlı" placeholderTextColor={C.muted} />

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>📁 Kaydet</Text>}
              </TouchableOpacity>
              <View style={{ height: 40 }} />
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:        { flex: 1, backgroundColor: C.bg },
  center:    { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:    { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:      { fontSize: 24, color: C.txt },
  title:     { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  addBtn:    { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 7 },
  addTxt:    { fontSize: 14, fontWeight: '700', color: C.white },
  card:      { backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  cardTop:   { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 6 },
  dot:       { width: 14, height: 14, borderRadius: 7, flexShrink: 0 },
  name:      { fontSize: 15, fontWeight: '700', color: C.txt, flex: 1 },
  desc:      { fontSize: 12, color: C.txt2, marginBottom: 8 },
  stats:     { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4, marginBottom: 8 },
  statTxt:   { fontSize: 12, color: C.txt2 },
  barBg:     { height: 6, backgroundColor: C.input, borderRadius: 3 },
  barFill:   { height: 6, borderRadius: 3 },
  colorDot:  { width: 32, height: 32, borderRadius: 16 },
  colorDotActive: { borderWidth: 3, borderColor: C.white, transform: [{ scale: 1.2 }] },
  empty:     { alignItems: 'center', paddingVertical: 48 },
  emptyIco:  { fontSize: 48, marginBottom: 12 },
  emptyTxt:  { fontSize: 15, color: C.txt2 },
  mHeader:   { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:    { fontSize: 20, fontWeight: '800', color: C.txt },
  close:     { fontSize: 20, color: C.muted },
  mLbl:      { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:    { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  saveBtn:   { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 16 },
  saveTxt:   { fontSize: 16, fontWeight: '700', color: C.white },
});
