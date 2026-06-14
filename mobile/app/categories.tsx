import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { userCategories as catApi, misc as miscApi } from '../services/api';

const CAT_ICONS = ['🍔','🚗','🏠','💊','📚','🎮','✈️','👗','💻','🎵',
                   '⚽','🐶','🌱','🎁','💪','🎬','☕','🍺','🛍️','💰',
                   '🏋️','📱','🔧','🏥'];

const DEFAULT_GIDER = ['Yemek','Ulaşım','Kira','Sağlık','Eğitim','Eğlence','Market',
                       'Giyim','Teknoloji','Diğer'];
const DEFAULT_GELIR = ['Maaş','Freelance','Kira Geliri','Yatırım','Satış','Diğer'];

type Tab = 'gider' | 'gelir';

export default function CategoriesScreen() {
  const router = useRouter();
  const [tab,       setTab]     = useState<Tab>('gider');
  const [custom,    setCustom]  = useState<any[]>([]);
  const [loading,   setLoading] = useState(true);
  const [ref,       setRef]     = useState(false);
  const [modal,     setModal]   = useState(false);
  const [saving,    setSaving]  = useState(false);

  const [name,      setName]    = useState('');
  const [mType,     setMType]   = useState<Tab>('gider');
  const [icon,      setIcon]    = useState('📌');
  const [color,     setColor]   = useState('#10069F');

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setCustom((await catApi.list() as any[]) || []); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  function resetForm() { setName(''); setMType('gider'); setIcon('📌'); setColor('#10069F'); }

  async function save() {
    if (!name.trim()) { Alert.alert('Hata', 'Kategori adı zorunlu'); return; }
    setSaving(true);
    try {
      await catApi.create({ name: name.trim(), type: mType, icon, color });
      setModal(false); resetForm(); load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function del(id: number, nm: string) {
    Alert.alert('Sil', `"${nm}" silinsin mi?`, [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await catApi.delete(id); setCustom(p => p.filter(x => x.id !== id)); }
        catch (e: any) { Alert.alert('Hata', (e as any).message); }
      }},
    ]);
  }

  const defaults = tab === 'gider' ? DEFAULT_GIDER : DEFAULT_GELIR;
  const filtered = custom.filter(c => c.type === tab);

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Kategoriler</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => { resetForm(); setModal(true); }}>
          <Text style={s.addTxt}>+ Ekle</Text>
        </TouchableOpacity>
      </View>

      {/* Tab */}
      <View style={s.tabRow}>
        {(['gider','gelir'] as Tab[]).map(t => (
          <TouchableOpacity key={t} style={[s.tabBtn, tab===t && s.tabBtnActive]} onPress={() => setTab(t)}>
            <Text style={[s.tabTxt, tab===t && s.tabTxtActive]}>
              {t === 'gider' ? '↓ Gider' : '↑ Gelir'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>

            <Text style={s.sect}>Varsayılan</Text>
            <View style={s.chipWrap}>
              {defaults.map(d => (
                <View key={d} style={s.chip}><Text style={s.chipTxt}>{d}</Text></View>
              ))}
            </View>

            {filtered.length > 0 && (
              <>
                <Text style={s.sect}>Özel</Text>
                {filtered.map(c => (
                  <View key={c.id} style={s.catRow}>
                    <View style={[s.catDot, { backgroundColor: c.color || '#10069F' }]}>
                      <Text style={{ fontSize: 16 }}>{c.icon || '📌'}</Text>
                    </View>
                    <Text style={s.catName}>{c.name}</Text>
                    <TouchableOpacity onPress={() => del(c.id, c.name)}>
                      <Text style={{ color: C.muted, fontSize: 18 }}>✕</Text>
                    </TouchableOpacity>
                  </View>
                ))}
              </>
            )}

            <View style={{ height: 40 }} />
          </ScrollView>
      }

      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Kategori Ekle</Text>
              <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }}>
              <Text style={s.mLbl}>Tür</Text>
              <View style={{ flexDirection: 'row', gap: 10, marginBottom: 14 }}>
                {(['gider','gelir'] as Tab[]).map(t => (
                  <TouchableOpacity key={t} style={[s.typeBtn, mType===t && s.typeBtnA]} onPress={() => setMType(t)}>
                    <Text style={[s.typeBtnT, mType===t && { color: C.white }]}>
                      {t === 'gider' ? '↓ Gider' : '↑ Gelir'}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              <Text style={s.mLbl}>Ad *</Text>
              <TextInput style={s.mInput} value={name} onChangeText={setName}
                placeholder="Kategori adı" placeholderTextColor={C.muted} />

              <Text style={[s.mLbl, { marginTop: 14 }]}>İkon</Text>
              <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }}>
                {CAT_ICONS.map(ic => (
                  <TouchableOpacity key={ic} style={[s.iconBtn, icon===ic && s.iconBtnA]} onPress={() => setIcon(ic)}>
                    <Text style={{ fontSize: 20 }}>{ic}</Text>
                  </TouchableOpacity>
                ))}
              </View>

              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>🗂️ Kaydet</Text>}
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
  bg:         { flex: 1, backgroundColor: C.bg },
  center:     { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:     { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:       { fontSize: 24, color: C.txt },
  title:      { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  addBtn:     { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 7 },
  addTxt:     { fontSize: 14, fontWeight: '700', color: C.white },
  tabRow:     { flexDirection: 'row', marginHorizontal: 16, marginTop: 12, backgroundColor: C.input, borderRadius: 12, padding: 4, gap: 4 },
  tabBtn:     { flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: 'center' },
  tabBtnActive: { backgroundColor: C.card },
  tabTxt:     { fontSize: 14, fontWeight: '600', color: C.txt2 },
  tabTxtActive: { color: C.txt, fontWeight: '700' },
  sect:       { fontSize: 11, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 1.1, paddingHorizontal: 16, marginTop: 20, marginBottom: 10 },
  chipWrap:   { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 16, gap: 8 },
  chip:       { paddingHorizontal: 12, paddingVertical: 7, backgroundColor: C.card, borderRadius: 20, borderWidth: 1, borderColor: C.border },
  chipTxt:    { fontSize: 13, color: C.txt2 },
  catRow:     { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 8, backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border, gap: 12 },
  catDot:     { width: 36, height: 36, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  catName:    { fontSize: 15, fontWeight: '600', color: C.txt, flex: 1 },
  mHeader:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:     { fontSize: 20, fontWeight: '800', color: C.txt },
  close:      { fontSize: 20, color: C.muted },
  mLbl:       { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:     { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border, marginBottom: 4 },
  typeBtn:    { flex: 1, paddingVertical: 12, borderRadius: 12, backgroundColor: C.card, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  typeBtnA:   { backgroundColor: C.blue, borderColor: C.blue },
  typeBtnT:   { fontSize: 14, fontWeight: '700', color: C.txt2 },
  iconBtn:    { width: 44, height: 44, borderRadius: 10, backgroundColor: C.input, alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: 'transparent' },
  iconBtnA:   { borderColor: C.blue, backgroundColor: C.card },
  saveBtn:    { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 20 },
  saveTxt:    { fontSize: 16, fontWeight: '700', color: C.white },
});
