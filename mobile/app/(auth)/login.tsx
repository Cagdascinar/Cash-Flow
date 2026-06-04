import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator, Alert } from 'react-native';
import { useState } from 'react';
import { useRouter } from 'expo-router';
import { C } from '../../constants/Colors';
import { auth } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

export default function LoginScreen() {
  const [username, setUser] = useState('');
  const [password, setPass] = useState('');
  const [loading,  setLoad] = useState(false);
  const router = useRouter();
  const { setUser: storeSetUser } = useAuthStore();

  async function login() {
    if (!username.trim() || !password.trim()) { Alert.alert('Hata', 'Kullanıcı adı ve şifre gerekli'); return; }
    setLoad(true);
    try {
      const me = await auth.login(username.trim(), password);
      storeSetUser(me);
    } catch (e: any) {
      Alert.alert('Giriş Başarısız', e.message ?? 'Bir hata oluştu');
    } finally { setLoad(false); }
  }

  return (
    <KeyboardAvoidingView style={s.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={s.logo}>
        <Text style={s.logoIco}>🦔</Text>
        <Text style={s.logoTxt}>Kirpi</Text>
        <Text style={s.logoSub}>Nakit akışını kontrol et</Text>
      </View>

      <View style={s.form}>
        <View style={s.field}>
          <Text style={s.lbl}>Kullanıcı Adı</Text>
          <TextInput style={s.input} placeholder="kullanici_adi" placeholderTextColor={C.muted} value={username} onChangeText={setUser} autoCapitalize="none" autoCorrect={false} returnKeyType="next" />
        </View>
        <View style={s.field}>
          <Text style={s.lbl}>Şifre</Text>
          <TextInput style={s.input} placeholder="••••••••" placeholderTextColor={C.muted} value={password} onChangeText={setPass} secureTextEntry returnKeyType="done" onSubmitEditing={login} />
        </View>

        <TouchableOpacity style={[s.btn, loading && s.disabled]} onPress={login} disabled={loading}>
          {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.btnTxt}>Giriş Yap</Text>}
        </TouchableOpacity>

        <TouchableOpacity style={s.link} onPress={() => router.push('/(auth)/register')}>
          <Text style={s.linkTxt}>Hesabın yok mu? <Text style={{ color: C.blue, fontWeight: '600' }}>Kayıt ol</Text></Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg, justifyContent: 'center', paddingHorizontal: 24 },
  logo:      { alignItems: 'center', marginBottom: 48 },
  logoIco:   { fontSize: 64, marginBottom: 8 },
  logoTxt:   { fontSize: 32, fontWeight: '700', color: C.txt, letterSpacing: 1 },
  logoSub:   { fontSize: 14, color: C.txt2, marginTop: 4 },
  form:      { gap: 16 },
  field:     { gap: 6 },
  lbl:       { fontSize: 12, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  input:     { backgroundColor: C.input, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, color: C.txt, borderWidth: 1, borderColor: C.border },
  btn:       { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 8 },
  disabled:  { opacity: 0.6 },
  btnTxt:    { color: C.white, fontSize: 16, fontWeight: '700' },
  link:      { alignItems: 'center', paddingVertical: 8 },
  linkTxt:   { fontSize: 14, color: C.txt2 },
});
