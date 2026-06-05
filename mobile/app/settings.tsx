import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
  TextInput, Alert, ActivityIndicator, Switch,
} from 'react-native';
import { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { useAuthStore } from '../stores/authStore';
import { BASE_URL } from '../services/api';

export default function SettingsScreen() {
  const router = useRouter();
  const { user } = useAuthStore();

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={s.header}>
          <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
          <Text style={s.title}>Ayarlar</Text>
        </View>

        <View style={s.section}>
          <Text style={s.sLabel}>Hesap Bilgileri</Text>
          <View style={s.infoCard}>
            <Row label="Kullanıcı Adı" value={user?.username ?? '—'} />
            <View style={s.div} />
            <Row label="E-posta" value={user?.email ?? '—'} />
            <View style={s.div} />
            <Row label="Abonelik" value={user?.is_premium ? '✅ Premium' : '⏳ Deneme'} />
          </View>
        </View>

        <View style={s.section}>
          <Text style={s.sLabel}>Gelişmiş Ayarlar</Text>
          <View style={s.infoCard}>
            <TouchableOpacity style={s.linkRow} onPress={() => Alert.alert('Şifre Değiştir', 'Web uygulamasından şifrenizi değiştirebilirsiniz.')}>
              <Text style={s.linkTxt}>🔒 Şifre Değiştir</Text>
              <Text style={s.chevron}>›</Text>
            </TouchableOpacity>
            <View style={s.div} />
            <TouchableOpacity style={s.linkRow} onPress={() => Alert.alert('Profil Yönetimi', 'Web uygulamasından profil ekleyip düzenleyebilirsiniz.')}>
              <Text style={s.linkTxt}>👤 Profil Yönetimi</Text>
              <Text style={s.chevron}>›</Text>
            </TouchableOpacity>
            <View style={s.div} />
            <TouchableOpacity style={s.linkRow} onPress={() => Alert.alert('Veri Dışa Aktar', 'Web uygulamasından Excel/PDF olarak dışa aktarabilirsiniz.')}>
              <Text style={s.linkTxt}>📤 Veriyi Dışa Aktar</Text>
              <Text style={s.chevron}>›</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={s.section}>
          <Text style={s.sLabel}>Hakkında</Text>
          <View style={s.infoCard}>
            <Row label="Versiyon" value="1.0.0" />
            <View style={s.div} />
            <Row label="Sunucu" value={BASE_URL.replace('https://', '')} />
          </View>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

function Row({ label, value }: { label: string; value: string }) {
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
  infoCard:  { backgroundColor: C.card, borderRadius: 14, borderWidth: 1, borderColor: C.border, overflow: 'hidden' },
  div:       { height: 1, backgroundColor: C.border, marginHorizontal: 14 },
  linkRow:   { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 14 },
  linkTxt:   { fontSize: 14, fontWeight: '600', color: C.txt },
  chevron:   { fontSize: 18, color: C.muted },
});
