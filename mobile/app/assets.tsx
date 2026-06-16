import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity, Alert, Modal, TextInput,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { GestureHandlerRootView, ScrollView as GHScrollView } from 'react-native-gesture-handler';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { assets as assetsApi } from '../services/api';
import { SwipeableRow } from '../components/SwipeableRow';

const TYPES = ['Araç','Gayrimenkul','Elektronik','Makine','Ofis Ekipmanı','Diğer'];

export default function AssetsScreen() {
  const router = useRouter();
  const [list,        setList]        = useState<any[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [ref,         setRef]         = useState(false);
  const [addModal,    setAddModal]    = useState(false);
  const [maintModal,  setMaintModal]  = useState(false);
  const [selAsset,    setSelAsset]    = useState<any>(null);
  const [maintList,   setMaintList]   = useState<any[]>([]);
  const [maintLoad,   setMaintLoad]   = useState(false);

  // Yeni varlık formu
  const [name,    setName]    = useState('');
  const [type,    setType]    = useState(TYPES[0]);
  const [cost,    setCost]    = useState('');
  const [date,    setDate]    = useState(new Date().toISOString().split('T')[0]);
  const [depRate, setDepRate] = useState('20');
  const [saving,  setSaving]  = useState(false);

  // Bakım formu
  const [mDesc,    setMDesc]    = useState('');
  const [mCost,    setMCost]    = useState('');
  const [mDate,    setMDate]    = useState(new Date().toISOString().split('T')[0]);
  const [savingM,  setSavingM]  = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try { setList(await assetsApi.list() as any[]); } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function openMaint(asset: any) {
    setSelAsset(asset); setMaintModal(true); setMaintLoad(true);
    try { setMaintList(await assetsApi.maintenance(asset.id) as any[]); } catch {}
    finally { setMaintLoad(false); }
  }

  async function save() {
    if (!name.trim() || !cost) { Alert.alert('Hata', 'İsim ve maliyet gerekli'); return; }
    setSaving(true);
    try {
      await assetsApi.create({ name: name.trim(), asset_type: type, purchase_price: parseFloat(cost.replace(',','.')), purchase_date: date, depreciation_rate: parseFloat(depRate) || 20 });
      setAddModal(false); setName(''); setCost('');
      load();
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function saveMaint() {
    if (!mDesc.trim() || !mCost) { Alert.alert('Hata', 'Açıklama ve maliyet gerekli'); return; }
    setSavingM(true);
    try {
      const newM = await assetsApi.addMaintenance(selAsset.id, { description: mDesc.trim(), cost: parseFloat(mCost.replace(',','.')), date: mDate });
      setMaintList(p => [newM, ...p]);
      setMDesc(''); setMCost('');
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSavingM(false); }
  }

  async function delMaint(mid: number) {
    try { await assetsApi.delMaintenance(mid); setMaintList(p => p.filter(m => m.id !== mid)); }
    catch (e: any) { Alert.alert('Hata', e.message); }
  }

  async function del(id: number) {
    Alert.alert('Sil', 'Bu varlığı ve tüm bakım kayıtlarını silmek istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await assetsApi.delete(id); setList(p => p.filter(a => a.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  const totalCost = list.reduce((s, a) => s + (a.purchase_price ?? 0), 0);
  const totalMaint = list.reduce((s, a) => s + (a.total_maintenance ?? 0), 0);

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Varlıklar</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => setAddModal(true)}><Text style={s.addTxt}>+ Ekle</Text></TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>
            {list.length > 0 && (
              <View style={s.totalCard}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-around' }}>
                  <View style={{ alignItems: 'center' }}>
                    <Text style={s.totalLbl}>Toplam Maliyet</Text>
                    <Text style={[s.totalVal, { color: C.blue }]}>{money(totalCost)}</Text>
                  </View>
                  {totalMaint > 0 && (
                    <View style={{ alignItems: 'center' }}>
                      <Text style={s.totalLbl}>Bakım Toplam</Text>
                      <Text style={[s.totalVal, { color: C.yellow }]}>{money(totalMaint)}</Text>
                    </View>
                  )}
                </View>
              </View>
            )}
            {list.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>🏗️</Text><Text style={s.emptyTxt}>Varlık eklenmedi</Text></View>
              : list.map(a => (
                  <SwipeableRow
                    key={a.id}
                    style={{ marginHorizontal: 16, marginBottom: 10, marginTop: 4, borderRadius: 14 }}
                    actions={[{ label: 'Sil', icon: '🗑️', color: '#dc2626', onPress: () => del(a.id) }]}
                  >
                    <View style={s.card}>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <View style={{ flex: 1 }}>
                          <Text style={s.aName}>{a.name}</Text>
                          <Text style={s.aSub}>{a.asset_type} · {a.purchase_date?.split('T')[0]}</Text>
                        </View>
                      </View>
                      <View style={s.aRow}>
                        <View><Text style={s.aLbl}>Maliyet</Text><Text style={s.aVal}>{money(a.purchase_price)}</Text></View>
                        <View><Text style={s.aLbl}>Amortisman</Text><Text style={s.aVal}>%{a.depreciation_rate}/yıl</Text></View>
                        {a.total_maintenance > 0 && (
                          <View><Text style={s.aLbl}>Bakım</Text><Text style={[s.aVal, { color: C.yellow }]}>{money(a.total_maintenance)}</Text></View>
                        )}
                      </View>
                      <TouchableOpacity style={s.maintBtn} onPress={() => openMaint(a)}>
                        <Text style={s.maintTxt}>🔧 Bakım Kayıtları {a.total_maintenance > 0 ? `· ${money(a.total_maintenance)}` : ''}</Text>
                      </TouchableOpacity>
                    </View>
                  </SwipeableRow>
                ))
            }
            <View style={{ height: 40 }} />
          </ScrollView>
      }

      {/* Varlık Ekle Modal */}
      <Modal visible={addModal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>Varlık Ekle</Text>
              <TouchableOpacity onPress={() => setAddModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <ScrollView style={{ padding: 16 }}>
              {[
                { lbl: 'Varlık Adı *', val: name, set: setName, ph: 'Toyota Corolla' },
                { lbl: 'Maliyet (₺) *', val: cost, set: setCost, ph: '500000', kb: 'decimal-pad' as const },
                { lbl: 'Satın Alma Tarihi', val: date, set: setDate, ph: 'YYYY-MM-DD' },
                { lbl: 'Yıllık Amortisman (%)', val: depRate, set: setDepRate, ph: '20', kb: 'decimal-pad' as const },
              ].map(({ lbl, val, set, ph, kb }) => (
                <View key={lbl} style={{ marginBottom: 14 }}>
                  <Text style={s.mLbl}>{lbl}</Text>
                  <TextInput style={s.mInput} value={val} onChangeText={set} placeholder={ph} placeholderTextColor={C.muted} keyboardType={kb} />
                </View>
              ))}
              <View style={{ marginBottom: 14 }}>
                <Text style={s.mLbl}>Varlık Tipi</Text>
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 6 }}>
                  {TYPES.map(t => (
                    <TouchableOpacity key={t} style={[s.tBtn, type === t && { backgroundColor: C.blue, borderColor: C.blue }]} onPress={() => setType(t)}>
                      <Text style={[{ fontSize: 13, color: C.txt2 }, type === t && { color: C.white }]}>{t}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>
              <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={save} disabled={saving}>
                {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>🏗️ Varlığı Ekle</Text>}
              </TouchableOpacity>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      </Modal>

      {/* Bakım Kayıtları Modal */}
      <Modal visible={maintModal} animationType="slide" presentationStyle="pageSheet">
        <GestureHandlerRootView style={{ flex: 1 }}>
        <SafeAreaView style={s.bg} edges={['top']}>
          <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
            <View style={s.mHeader}>
              <Text style={s.mTitle}>🔧 {selAsset?.name}</Text>
              <TouchableOpacity onPress={() => setMaintModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
            </View>
            <GHScrollView style={{ padding: 16 }}>
              {/* Yeni bakım ekle */}
              <Text style={[s.mLbl, { marginBottom: 6 }]}>Yeni Bakım Kaydı</Text>
              <TextInput style={[s.mInput, { marginBottom: 8 }]} value={mDesc} onChangeText={setMDesc} placeholder="Bakım açıklaması" placeholderTextColor={C.muted} />
              <View style={{ flexDirection: 'row', gap: 8, marginBottom: 8 }}>
                <TextInput style={[s.mInput, { flex: 1 }]} value={mCost} onChangeText={setMCost} placeholder="Maliyet ₺" placeholderTextColor={C.muted} keyboardType="decimal-pad" />
                <TextInput style={[s.mInput, { flex: 1 }]} value={mDate} onChangeText={setMDate} placeholder="YYYY-MM-DD" placeholderTextColor={C.muted} />
              </View>
              <TouchableOpacity style={[s.saveBtn, { marginBottom: 24 }, savingM && { opacity: 0.6 }]} onPress={saveMaint} disabled={savingM}>
                {savingM ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>+ Kaydet</Text>}
              </TouchableOpacity>

              {/* Bakım listesi */}
              {maintLoad
                ? <ActivityIndicator color={C.blue} />
                : maintList.length === 0
                  ? <View style={s.empty}><Text style={s.emptyTxt}>Bakım kaydı yok</Text></View>
                  : <>
                      <Text style={[s.mLbl, { marginBottom: 10 }]}>Geçmiş Bakımlar</Text>
                      {maintList.map(m => (
                        <SwipeableRow
                          key={m.id}
                          style={{ marginBottom: 8, borderRadius: 14 }}
                          actions={[{ label: 'Sil', icon: '🗑️', color: '#dc2626', onPress: () => delMaint(m.id) }]}
                        >
                          <View style={s.card}>
                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                              <View style={{ flex: 1 }}>
                                <Text style={s.aName}>{m.description}</Text>
                                <Text style={s.aSub}>{m.date?.split('T')[0]}</Text>
                              </View>
                              <Text style={[s.aVal, { color: C.yellow }]}>{money(m.cost)}</Text>
                            </View>
                          </View>
                        </SwipeableRow>
                      ))}
                    </>
              }
              <View style={{ height: 40 }} />
            </GHScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
        </GestureHandlerRootView>
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
  totalCard: { margin: 16, backgroundColor: C.hero, borderRadius: 14, padding: 16, borderWidth: 1, borderColor: 'rgba(99,160,255,.15)' },
  totalLbl:  { fontSize: 12, color: 'rgba(255,255,255,.45)', marginBottom: 4 },
  totalVal:  { fontSize: 20, fontWeight: '800' },
  card:      { backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border },
  aName:     { fontSize: 15, fontWeight: '700', color: C.txt },
  aSub:      { fontSize: 12, color: C.txt2, marginTop: 2 },
  aRow:      { flexDirection: 'row', justifyContent: 'space-between', marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: C.border },
  aLbl:      { fontSize: 11, color: C.muted },
  aVal:      { fontSize: 14, fontWeight: '700', color: C.txt, marginTop: 2 },
  maintBtn:  { marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: C.border },
  maintTxt:  { fontSize: 13, fontWeight: '600', color: C.blue },
  empty:     { alignItems: 'center', paddingVertical: 32 },
  emptyIco:  { fontSize: 48, marginBottom: 12 },
  emptyTxt:  { fontSize: 15, color: C.txt2 },
  mHeader:   { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:    { fontSize: 20, fontWeight: '800', color: C.txt },
  close:     { fontSize: 20, color: C.muted },
  mLbl:      { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6 },
  mInput:    { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  tBtn:      { paddingHorizontal: 12, paddingVertical: 7, borderRadius: 20, backgroundColor: C.input, borderWidth: 1, borderColor: C.border },
  saveBtn:   { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 8 },
  saveTxt:   { fontSize: 16, fontWeight: '700', color: C.white },
});
