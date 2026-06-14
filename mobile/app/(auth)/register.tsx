import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ActivityIndicator, Alert,
  ScrollView, StatusBar,
} from 'react-native';
import { useState } from 'react';
import { useRouter } from 'expo-router';
import { auth } from '../../services/api';

const BLUE  = '#10069F';
const GREEN = '#d5fd73';
const BG    = '#0b0e11';
const CARD  = '#141820';

export default function RegisterScreen() {
  const [username, setUser]   = useState('');
  const [email,    setEmail]  = useState('');
  const [password, setPass]   = useState('');
  const [profType, setProfType] = useState<'sahis'|'sirket'>('sahis');
  const [loading,  setLoad]   = useState(false);
  const router = useRouter();

  async function register() {
    if (!username.trim() || !email.trim() || !password.trim()) {
      Alert.alert('Hata', 'Tüm alanlar gerekli');
      return;
    }
    setLoad(true);
    try {
      await auth.register(username.trim(), email.trim(), password, profType);
      Alert.alert('Kayıt Başarılı ✓', 'E-posta adresinize doğrulama bağlantısı gönderildi.', [
        { text: 'Giriş Yap', onPress: () => router.replace('/(auth)/login') },
      ]);
    } catch (e: any) {
      Alert.alert('Hata', e.message ?? 'Bir hata oluştu');
    } finally { setLoad(false); }
  }

  return (
    <KeyboardAvoidingView
      style={s.root}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <StatusBar barStyle="light-content" backgroundColor={BG} />
      <View style={s.blob1} />

      <ScrollView
        contentContainerStyle={s.scroll}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
      >
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Text style={s.backTxt}>← Geri</Text>
        </TouchableOpacity>

        <View style={s.logoRow}>
          <View style={s.logoCircle}><Text style={s.logoEmoji}>🦔</Text></View>
          <View>
            <Text style={s.brand}>Kirpi <Text style={s.brandGreen}>Finans</Text></Text>
            <Text style={s.tagline}>30 gün ücretsiz premium</Text>
          </View>
        </View>

        <View style={s.card}>
          <Text style={s.cardTitle}>Hesap Oluştur</Text>

          {/* Profil tipi */}
          <Text style={s.lbl}>Hesap Türü</Text>
          <View style={s.typeRow}>
            <TouchableOpacity
              style={[s.typeCard, profType === 'sahis' && s.typeCardActive]}
              onPress={() => setProfType('sahis')}
            >
              <Text style={s.typeIco}>👤</Text>
              <Text style={[s.typeLbl, profType === 'sahis' && { color: '#fff' }]}>Bireysel</Text>
              <Text style={[s.typeSub, profType === 'sahis' && { color: 'rgba(255,255,255,.6)' }]}>Şahıs hesabı</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[s.typeCard, profType === 'sirket' && s.typeCardActive]}
              onPress={() => setProfType('sirket')}
            >
              <Text style={s.typeIco}>🏢</Text>
              <Text style={[s.typeLbl, profType === 'sirket' && { color: '#fff' }]}>Ticari</Text>
              <Text style={[s.typeSub, profType === 'sirket' && { color: 'rgba(255,255,255,.6)' }]}>Şirket hesabı</Text>
            </TouchableOpacity>
          </View>

          {[
            { lbl: 'Kullanıcı Adı', val: username, set: setUser, ph: 'kullanici_adi', cap: 'none' as const },
            { lbl: 'E-posta',       val: email,    set: setEmail, ph: 'ornek@email.com', kb: 'email-address' as const, cap: 'none' as const },
            { lbl: 'Şifre',         val: password, set: setPass,  ph: 'En az 8 karakter', sec: true, cap: 'none' as const },
          ].map(({ lbl, val, set, ph, kb, sec, cap }) => (
            <View key={lbl} style={{ marginBottom: 14 }}>
              <Text style={s.lbl}>{lbl}</Text>
              <TextInput
                style={s.input}
                placeholder={ph}
                placeholderTextColor="#3a4050"
                value={val}
                onChangeText={set}
                autoCapitalize={cap}
                keyboardType={kb}
                secureTextEntry={sec}
              />
            </View>
          ))}

          <TouchableOpacity
            style={[s.btn, loading && s.disabled]}
            onPress={register}
            disabled={loading}
            activeOpacity={0.85}
          >
            {loading
              ? <ActivityIndicator color="#0b0e11" />
              : <Text style={s.btnTxt}>{profType === 'sahis' ? '👤 Bireysel Hesap Aç' : '🏢 Ticari Hesap Aç'}</Text>}
          </TouchableOpacity>

          <TouchableOpacity style={s.loginLink} onPress={() => router.push('/(auth)/login')}>
            <Text style={s.loginTxt}>
              Hesabın var mı?{'  '}
              <Text style={s.loginGreen}>Giriş Yap</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  root: { flex: 1, backgroundColor: BG },
  blob1: {
    position: 'absolute', top: -100, right: -80,
    width: 280, height: 280, borderRadius: 140,
    backgroundColor: BLUE, opacity: 0.2,
  },
  scroll: { paddingHorizontal: 24, paddingTop: 56, paddingBottom: 40 },
  backBtn: { marginBottom: 20 },
  backTxt: { fontSize: 15, color: '#7a8494', fontWeight: '600' },
  logoRow: { flexDirection: 'row', alignItems: 'center', gap: 14, marginBottom: 28 },
  logoCircle: {
    width: 56, height: 56, borderRadius: 28, backgroundColor: BLUE,
    alignItems: 'center', justifyContent: 'center',
    shadowColor: BLUE, shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.5, shadowRadius: 14, elevation: 8,
  },
  logoEmoji: { fontSize: 28 },
  brand: { fontSize: 24, fontWeight: '800', color: '#ffffff' },
  brandGreen: { color: GREEN },
  tagline: { fontSize: 12, color: '#4ade80', fontWeight: '600', marginTop: 2 },
  card: {
    backgroundColor: CARD, borderRadius: 24, padding: 24,
    borderWidth: 1, borderColor: '#1e2533',
  },
  cardTitle: { fontSize: 20, fontWeight: '800', color: '#fff', marginBottom: 18 },
  lbl: {
    fontSize: 11, fontWeight: '700', color: '#7a8494',
    textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 6,
  },
  typeRow: { flexDirection: 'row', gap: 10, marginBottom: 18 },
  typeCard: {
    flex: 1, backgroundColor: '#1a2030', borderRadius: 14, padding: 14,
    alignItems: 'center', borderWidth: 1.5, borderColor: '#242b3a',
  },
  typeCardActive: { borderColor: BLUE, backgroundColor: '#0d1045' },
  typeIco: { fontSize: 24, marginBottom: 4 },
  typeLbl: { fontSize: 13, fontWeight: '700', color: '#7a8494' },
  typeSub: { fontSize: 11, color: '#4a5568', marginTop: 2 },
  input: {
    backgroundColor: '#1a2030', borderRadius: 12,
    paddingHorizontal: 16, paddingVertical: 14,
    fontSize: 16, color: '#fff',
    borderWidth: 1, borderColor: '#242b3a',
  },
  btn: {
    backgroundColor: GREEN, borderRadius: 14, paddingVertical: 16,
    alignItems: 'center', marginTop: 6,
    shadowColor: GREEN, shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35, shadowRadius: 12, elevation: 8,
  },
  disabled: { opacity: 0.6 },
  btnTxt: { color: '#0b0e11', fontSize: 15, fontWeight: '800' },
  loginLink: { alignItems: 'center', paddingVertical: 12 },
  loginTxt: { fontSize: 14, color: '#7a8494' },
  loginGreen: { color: GREEN, fontWeight: '700' },
});
