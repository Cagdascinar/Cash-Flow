import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ActivityIndicator, Alert,
  StatusBar,
} from 'react-native';
import { useState } from 'react';
import { useRouter } from 'expo-router';
import { auth } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

export default function LoginScreen() {
  const [username, setUser] = useState('');
  const [password, setPass] = useState('');
  const [loading,  setLoad] = useState(false);
  const router = useRouter();
  const { setUser: storeSetUser } = useAuthStore();

  async function login() {
    if (!username.trim() || !password.trim()) {
      Alert.alert('Hata', 'Kullanıcı adı ve şifre gerekli');
      return;
    }
    setLoad(true);
    try {
      const me = await auth.login(username.trim(), password);
      storeSetUser(me);
    } catch (e: any) {
      Alert.alert('Giriş Başarısız', e.message ?? 'Bir hata oluştu');
    } finally { setLoad(false); }
  }

  return (
    <KeyboardAvoidingView
      style={s.root}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <StatusBar barStyle="light-content" backgroundColor="#0b0e11" />

      {/* Arka plan dekorasyon */}
      <View style={s.blob1} />
      <View style={s.blob2} />

      {/* Logo */}
      <View style={s.logoArea}>
        <View style={s.logoCircle}>
          <Text style={s.logoEmoji}>🦔</Text>
        </View>
        <Text style={s.brand}>Kirpi <Text style={s.brandGreen}>Finans</Text></Text>
        <Text style={s.tagline}>Paranızın tam kontrolü sizde</Text>
      </View>

      {/* Form */}
      <View style={s.card}>
        <Text style={s.cardTitle}>Giriş Yap</Text>

        <View style={s.field}>
          <Text style={s.lbl}>Kullanıcı Adı</Text>
          <TextInput
            style={s.input}
            placeholder="kullanici_adi"
            placeholderTextColor="#3a4050"
            value={username}
            onChangeText={setUser}
            autoCapitalize="none"
            autoCorrect={false}
            returnKeyType="next"
          />
        </View>

        <View style={s.field}>
          <Text style={s.lbl}>Şifre</Text>
          <TextInput
            style={s.input}
            placeholder="••••••••"
            placeholderTextColor="#3a4050"
            value={password}
            onChangeText={setPass}
            secureTextEntry
            returnKeyType="done"
            onSubmitEditing={login}
          />
        </View>

        <TouchableOpacity
          style={[s.btn, loading && s.disabled]}
          onPress={login}
          disabled={loading}
          activeOpacity={0.85}
        >
          {loading
            ? <ActivityIndicator color="#0b0e11" />
            : <Text style={s.btnTxt}>Giriş Yap →</Text>}
        </TouchableOpacity>

        <TouchableOpacity style={s.register} onPress={() => router.push('/(auth)/register')}>
          <Text style={s.registerTxt}>
            Hesabın yok mu?{'  '}
            <Text style={s.registerLink}>Ücretsiz Kayıt Ol</Text>
          </Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const BLUE  = '#10069F';
const GREEN = '#d5fd73';
const BG    = '#0b0e11';
const CARD  = '#141820';

const s = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: BG,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  blob1: {
    position: 'absolute', top: -80, right: -80,
    width: 260, height: 260, borderRadius: 130,
    backgroundColor: BLUE, opacity: 0.18,
  },
  blob2: {
    position: 'absolute', bottom: -60, left: -60,
    width: 200, height: 200, borderRadius: 100,
    backgroundColor: GREEN, opacity: 0.10,
  },

  logoArea: { alignItems: 'center', marginBottom: 36 },
  logoCircle: {
    width: 88, height: 88, borderRadius: 44,
    backgroundColor: BLUE,
    alignItems: 'center', justifyContent: 'center',
    marginBottom: 16,
    shadowColor: BLUE, shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.6, shadowRadius: 20, elevation: 12,
  },
  logoEmoji: { fontSize: 44 },
  brand: {
    fontSize: 34, fontWeight: '800', color: '#ffffff',
    letterSpacing: 0.5,
  },
  brandGreen: { color: GREEN },
  tagline: { fontSize: 13, color: '#7a8494', marginTop: 4 },

  card: {
    backgroundColor: CARD,
    borderRadius: 24,
    padding: 24,
    borderWidth: 1,
    borderColor: '#1e2533',
  },
  cardTitle: {
    fontSize: 20, fontWeight: '800', color: '#ffffff',
    marginBottom: 20,
  },

  field: { marginBottom: 14 },
  lbl: {
    fontSize: 11, fontWeight: '700', color: '#7a8494',
    textTransform: 'uppercase', letterSpacing: 0.9, marginBottom: 6,
  },
  input: {
    backgroundColor: '#1a2030',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 16,
    color: '#ffffff',
    borderWidth: 1,
    borderColor: '#242b3a',
  },

  btn: {
    backgroundColor: GREEN,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
    shadowColor: GREEN,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 12,
    elevation: 8,
  },
  disabled: { opacity: 0.6 },
  btnTxt: { color: '#0b0e11', fontSize: 16, fontWeight: '800' },

  register: { alignItems: 'center', paddingVertical: 12 },
  registerTxt: { fontSize: 14, color: '#7a8494' },
  registerLink: { color: GREEN, fontWeight: '700' },
});
