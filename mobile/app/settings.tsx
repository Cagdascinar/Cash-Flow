import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  TextInput, Alert, ActivityIndicator, Linking,
} from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { useAuthStore } from '../stores/authStore';
import { me as meApi, auth, getToken } from '../services/api';
import { BASE_URL } from '../services/api';

export default function SettingsScreen() {
  const router = useRouter();
  const { user, setUser, logout } = useAuthStore();

  const [displayName, setDisplayName] = useState(user?.username ?? '');
  const [savingName,  setSavingName]  = useState(false);

  const [oldPwd,  setOldPwd]  = useState('');
  const [newPwd,  setNewPwd]  = useState('');
  const [newPwd2, setNewPwd2] = useState('');
  const [savingPwd, setSavingPwd] = useState(false);

  async function saveName() {
    if (!displayName.trim()) { Alert.alert('Hata', 'İsim boş olamaz'); return; }
    setSavingName(true);
    try {
      await meApi.update({ display_name: displayName.trim() });
      const u = await auth.me();
      setUser(u);
      Alert.alert('✅ Kaydedildi');
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSavingName(false); }
  }

  async function changePassword() {
    if (!oldPwd || !newPwd) { Alert.alert('Hata', 'Tüm alanları doldurun'); return; }
    if (newPwd !== newPwd2) { Alert.alert('Hata', 'Yeni şifreler uyuşmuyor'); return; }
    if (newPwd.length < 6) { Alert.alert('Hata', 'Şifre en az 6 karakter olmalı'); return; }
    setSavingPwd(true);
    try {
      await meApi.changePassword({ old_password: oldPwd, new_password: newPwd });
      setOldPwd(''); setNewPwd(''); setNewPwd2('');
      Alert.alert('✅ Şifre değiştirildi');
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setSavingPwd(false); }
  }

  async function openExport(type: 'excel' | 'pdf') {
    try {
      const token = await getToken();
      const url = `${BASE_URL}/api/export/${type}?mobile_token=${token}`;
      await Linking.openURL(url);
    } catch { Alert.alert('Hata', 'Dışa aktarma açılamadı'); }
  }

  function deleteAccount() {
    Alert.alert(
      '⚠️ Hesabı Sil',
      'Hesabınız ve tüm verileriniz kalıcı olarak silinecek. Bu işlem geri alınamaz.',
      [
        { text: 'İptal', style: 'cancel' },
        { text: 'Sil', style: 'destructive', onPress: async () => {
          try {
            await meApi.delete();
            logout();
          } catch (e: any) { Alert.alert('Hata', e.message); }
        }},
      ]
    );
  }

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={s.header}>
          <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
          <Text style={s.title}>Ayarlar</Text>
        </View>

        {/* Hesap bilgileri */}
        <View style={s.section}>
          <Text style={s.sLabel}>Hesap Bilgileri</Text>
          <View style={s.card}>
            <InfoRow label="Kullanıcı Adı" value={user?.username ?? '—'} />
            <View style={s.div} />
            <InfoRow label="E-posta" value={user?.email ?? '—'} />
            <View style={s.div} />
            <InfoRow label="Abonelik" value={user?.is_premium ? '✅ Premium' : '⏳ Deneme'} />
          </View>
        </View>

        {/* Profil adı güncelle */}
        <View style={s.section}>
          <Text style={s.sLabel}>Görünen Ad</Text>
          <View style={s.card}>
            <View style={{ padding: 14, gap: 10 }}>
              <TextInput
                style={s.input}
                value={displayName}
                onChangeText={setDisplayName}
                placeholder="Görünen adınız"
                placeholderTextColor={C.muted}
              />
              <TouchableOpacity style={[s.btn, savingName && { opacity: 0.6 }]} onPress={saveName} disabled={savingName}>
                {savingName ? <ActivityIndicator color={C.white} size="small" /> : <Text style={s.btnTxt}>Kaydet</Text>}
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Şifre değiştir */}
        <View style={s.section}>
          <Text style={s.sLabel}>Şifre Değiştir</Text>
          <View style={s.card}>
            <View style={{ padding: 14, gap: 10 }}>
              <TextInput
                style={s.input} secureTextEntry
                value={oldPwd} onChangeText={setOldPwd}
                placeholder="Mevcut şifre" placeholderTextColor={C.muted}
              />
              <TextInput
                style={s.input} secureTextEntry
                value={newPwd} onChangeText={setNewPwd}
                placeholder="Yeni şifre" placeholderTextColor={C.muted}
              />
              <TextInput
                style={s.input} secureTextEntry
                value={newPwd2} onChangeText={setNewPwd2}
                placeholder="Yeni şifre (tekrar)" placeholderTextColor={C.muted}
              />
              <TouchableOpacity style={[s.btn, savingPwd && { opacity: 0.6 }]} onPress={changePassword} disabled={savingPwd}>
                {savingPwd ? <ActivityIndicator color={C.white} size="small" /> : <Text style={s.btnTxt}>Şifreyi Değiştir</Text>}
              </TouchableOpacity>
            </View>
          </View>
        </View>

        {/* Profil yönetimi */}
        <View style={s.section}>
          <Text style={s.sLabel}>Profiller</Text>
          <View style={s.card}>
            <TouchableOpacity style={s.linkRow} onPress={() => router.push('/profiles' as any)}>
              <Text style={s.linkTxt}>👤 Profil Yönetimi</Text>
              <Text style={s.chevron}>›</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Dışa aktar */}
        <View style={s.section}>
          <Text style={s.sLabel}>Veri</Text>
          <View style={s.card}>
            <TouchableOpacity style={s.linkRow} onPress={() => openExport('excel')}>
              <Text style={s.linkTxt}>📊 Excel Olarak İndir</Text>
              <Text style={s.chevron}>›</Text>
            </TouchableOpacity>
            <View style={s.div} />
            <TouchableOpacity style={s.linkRow} onPress={() => openExport('pdf')}>
              <Text style={s.linkTxt}>📄 PDF Olarak İndir</Text>
              <Text style={s.chevron}>›</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Hakkında */}
        <View style={s.section}>
          <Text style={s.sLabel}>Hakkında</Text>
          <View style={s.card}>
            <InfoRow label="Versiyon" value="1.0.0" />
            <View style={s.div} />
            <InfoRow label="Sunucu" value={BASE_URL.replace('https://', '')} />
          </View>
        </View>

        {/* Yasal */}
        <View style={s.section}>
          <Text style={s.sLabel}>Yasal</Text>
          <View style={s.card}>
            <TouchableOpacity style={s.linkRow} onPress={() => Linking.openURL('https://web-production-ba700.up.railway.app/gizlilik')}>
              <Text style={s.linkTxt}>🔒 Gizlilik Politikası</Text>
              <Text style={s.chevron}>›</Text>
            </TouchableOpacity>
            <View style={s.div} />
            <TouchableOpacity style={s.linkRow} onPress={() => Linking.openURL('https://web-production-ba700.up.railway.app/kullanim-kosullari')}>
              <Text style={s.linkTxt}>📃 Kullanım Koşulları</Text>
              <Text style={s.chevron}>›</Text>
            </TouchableOpacity>
            <View style={s.div} />
            <TouchableOpacity style={s.linkRow} onPress={() => Linking.openURL('https://web-production-ba700.up.railway.app/kvkk')}>
              <Text style={s.linkTxt}>📋 KVKK Aydınlatma Metni</Text>
              <Text style={s.chevron}>›</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Hesap sil */}
        <View style={s.section}>
          <View style={s.card}>
            <TouchableOpacity style={s.linkRow} onPress={deleteAccount}>
              <Text style={[s.linkTxt, { color: C.red }]}>🗑️ Hesabı Sil</Text>
              <Text style={s.chevron}>›</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={r.row}>
      <Text style={r.lbl}>{label}</Text>
      <Text style={r.val}>{value}</Text>
    </View>
  );
}

const r = StyleSheet.create({
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 14 },
  lbl: { fontSize: 14, color: C.txt2 },
  val: { fontSize: 14, fontWeight: '600', color: C.txt },
});

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  header:    { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:      { fontSize: 24, color: C.txt },
  title:     { fontSize: 22, fontWeight: '800', color: C.txt },
  section:   { marginHorizontal: 16, marginTop: 24 },
  sLabel:    { fontSize: 11, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 },
  card:      { backgroundColor: C.card, borderRadius: 14, borderWidth: 1, borderColor: C.border, overflow: 'hidden' },
  div:       { height: 1, backgroundColor: C.border, marginHorizontal: 14 },
  linkRow:   { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 14 },
  linkTxt:   { fontSize: 14, fontWeight: '600', color: C.txt },
  chevron:   { fontSize: 18, color: C.muted },
  input:     { backgroundColor: C.input, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 12, fontSize: 15, color: C.txt, borderWidth: 1, borderColor: C.border },
  btn:       { backgroundColor: C.blue, borderRadius: 10, paddingVertical: 13, alignItems: 'center' },
  btnTxt:    { fontSize: 15, fontWeight: '700', color: C.white },
});
