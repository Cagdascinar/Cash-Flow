import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  Alert, Modal, TextInput, ActivityIndicator,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { profiles as profilesApi, auth } from '../services/api';
import { useAuthStore } from '../stores/authStore';

const TYPES = [
  { key: 'sahis', label: '👤 Şahıs' },
  { key: 'sirket', label: '🏢 Şirket' },
];

export default function ProfilesScreen() {
  const router = useRouter();
  const { user, setUser } = useAuthStore();
  const [list,    setList]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal,   setModal]   = useState(false);
  const [name,    setName]    = useState('');
  const [type,    setType]    = useState('sahis');
  const [saving,  setSaving]  = useState(false);
  const [switching, setSwitching] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setList(await profilesApi.list() as any[]); } catch {}
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function create() {
    if (!name.trim()) { Alert.alert('Hata', 'Profil adı gerekli'); return; }
    setSaving(true);
    try {
      await profilesApi.create({ name: name.trim(), type });
      setModal(false); setName('');
      load();
      const u = await auth.me();
      setUser(u);
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSaving(false); }
  }

  async function switchProfile(id: number) {
    setSwitching(id);
    try {
      await profilesApi.switch(id);
      const u = await auth.me();
      setUser(u);
      Alert.alert('✅', 'Profil değiştirildi');
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSwitching(null); }
  }

  async function del(id: number, name: string) {
    if (list.length <= 1) { Alert.alert('Hata', 'En az 1 profil gerekli'); return; }
    Alert.alert('Profili Sil', `"${name}" profilini ve tüm verilerini silmek istiyor musunuz?`, [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try {
          await profilesApi.delete(id);
          const u = await auth.me();
          setUser(u);
          load();
        } catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  const activeId = user?.active_profile_id;

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Profiller</Text>
        <TouchableOpacity style={s.addBtn} onPress={() => setModal(true)}>
          <Text style={s.addTxt}>+ Yeni</Text>
        </TouchableOpacity>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}>
            <Text style={s.hint}>Her profilin verileri birbirinden bağımsızdır.</Text>
            <View style={s.group}>
              {list.map((p, i) => {
                const isActive = p.id === activeId;
                return (
                  <View key={p.id}>
                    {i > 0 && <View style={s.sep} />}
                    <View style={s.row}>
                      <View style={[s.avatar, isActive && { backgroundColor: C.blue }]}>
                        <Text style={s.avatarTxt}>{p.name[0]?.toUpperCase()}</Text>
                      </View>
                      <View style={{ flex: 1 }}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                          <Text style={s.pName}>{p.name}</Text>
                          {isActive && <View style={s.activeBadge}><Text style={s.activeTxt}>Aktif</Text></View>}
                        </View>
                        <Text style={s.pType}>{p.type === 'sirket' ? '🏢 Şirket' : '👤 Şahıs'}</Text>
                      </View>
                      <View style={{ flexDirection: 'row', gap: 8 }}>
                        {!isActive && (
                          <TouchableOpacity style={s.switchBtn} onPress={() => switchProfile(p.id)} disabled={switching === p.id}>
                            {switching === p.id
                              ? <ActivityIndicator size="small" color={C.blue} />
                              : <Text style={s.switchTxt}>Geç</Text>}
                          </TouchableOpacity>
                        )}
                        {!isActive && (
                          <TouchableOpacity onPress={() => del(p.id, p.name)} style={s.delBtn}>
                            <Text style={s.delTxt}>✕</Text>
                          </TouchableOpacity>
                        )}
                      </View>
                    </View>
                  </View>
                );
              })}
            </View>
            <View style={{ height: 40 }} />
          </ScrollView>
      }

      <Modal visible={modal} animationType="slide" presentationStyle="pageSheet">
        <SafeAreaView style={s.modal} edges={['top']}>
          <View style={s.mHeader}>
            <Text style={s.mTitle}>Yeni Profil</Text>
            <TouchableOpacity onPress={() => setModal(false)}><Text style={s.close}>✕</Text></TouchableOpacity>
          </View>
          <View style={{ padding: 16 }}>
            <Text style={s.mLbl}>Profil Adı</Text>
            <TextInput
              style={s.mInput} value={name} onChangeText={setName}
              placeholder="Kişisel, Şirket..." placeholderTextColor={C.muted}
              autoFocus
            />
            <Text style={[s.mLbl, { marginTop: 16 }]}>Profil Tipi</Text>
            <View style={{ flexDirection: 'row', gap: 10, marginTop: 8 }}>
              {TYPES.map(t => (
                <TouchableOpacity key={t.key} style={[s.typeBtn, type === t.key && s.typeA]} onPress={() => setType(t.key)}>
                  <Text style={[s.typeTxt, type === t.key && { color: C.white }]}>{t.label}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <TouchableOpacity style={[s.saveBtn, saving && { opacity: 0.6 }]} onPress={create} disabled={saving}>
              {saving ? <ActivityIndicator color={C.white} /> : <Text style={s.saveTxt}>Oluştur</Text>}
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: C.bg },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:      { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:        { fontSize: 24, color: C.txt },
  title:       { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  addBtn:      { backgroundColor: C.blue, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 7 },
  addTxt:      { fontSize: 14, fontWeight: '700', color: C.white },
  hint:        { fontSize: 13, color: C.txt2, marginHorizontal: 16, marginTop: 12, marginBottom: 12 },
  group:       { marginHorizontal: 16, backgroundColor: C.card, borderRadius: 16, borderWidth: 1, borderColor: C.border, overflow: 'hidden' },
  sep:         { height: 1, backgroundColor: C.border, marginLeft: 62 },
  row:         { flexDirection: 'row', alignItems: 'center', padding: 14, gap: 12 },
  avatar:      { width: 40, height: 40, borderRadius: 20, backgroundColor: C.input, alignItems: 'center', justifyContent: 'center' },
  avatarTxt:   { fontSize: 16, fontWeight: '700', color: C.white },
  pName:       { fontSize: 15, fontWeight: '700', color: C.txt },
  pType:       { fontSize: 12, color: C.txt2, marginTop: 2 },
  activeBadge: { backgroundColor: 'rgba(0,122,255,.15)', borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2 },
  activeTxt:   { fontSize: 11, fontWeight: '700', color: C.blue },
  switchBtn:   { borderWidth: 1, borderColor: C.blue, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 6 },
  switchTxt:   { fontSize: 13, fontWeight: '700', color: C.blue },
  delBtn:      { width: 28, height: 28, alignItems: 'center', justifyContent: 'center' },
  delTxt:      { fontSize: 16, color: C.muted },
  modal:       { flex: 1, backgroundColor: C.bg },
  mHeader:     { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16 },
  mTitle:      { fontSize: 20, fontWeight: '800', color: C.txt },
  close:       { fontSize: 20, color: C.muted },
  mLbl:        { fontSize: 11, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 8 },
  mInput:      { backgroundColor: C.card, borderRadius: 12, paddingHorizontal: 14, paddingVertical: 13, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  typeBtn:     { flex: 1, paddingVertical: 12, borderRadius: 12, backgroundColor: C.input, borderWidth: 1, borderColor: C.border, alignItems: 'center' },
  typeA:       { backgroundColor: C.blue, borderColor: C.blue },
  typeTxt:     { fontSize: 14, fontWeight: '600', color: C.txt2 },
  saveBtn:     { marginTop: 24, backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center' },
  saveTxt:     { fontSize: 16, fontWeight: '700', color: C.white },
});
