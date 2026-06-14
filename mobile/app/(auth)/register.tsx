import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, ActivityIndicator, Alert, ScrollView } from 'react-native';
import { useState } from 'react';
import { useRouter } from 'expo-router';
import { C } from '../../constants/Colors';
import { auth } from '../../services/api';

export default function RegisterScreen() {
  const [username, setUser] = useState('');
  const [email,    setEmail] = useState('');
  const [password, setPass] = useState('');
  const [loading,  setLoad] = useState(false);
  const router = useRouter();

  async function register() {
    if (!username.trim() || !email.trim() || !password.trim()) { Alert.alert('Hata', 'Tüm alanlar gerekli'); return; }
    setLoad(true);
    try {
      await auth.register(username.trim(), email.trim(), password);
      Alert.alert('Kayıt Başarılı', 'E-posta adresinize doğrulama bağlantısı gönderildi.', [
        { text: 'Giriş Yap', onPress: () => router.replace('/(auth)/login') },
      ]);
    } catch (e: any) {
      Alert.alert('Hata', e.message ?? 'Bir hata oluştu');
    } finally { setLoad(false); }
  }

  return (
    <KeyboardAvoidingView style={s.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>
        <TouchableOpacity onPress={() => router.back()} style={s.back}><Text style={s.backIco}>←</Text></TouchableOpacity>
        <Text style={s.title}>Hesap Oluştur</Text>
        <Text style={s.sub}>30 gün ücretsiz premium</Text>

        <View style={s.form}>
          {[
            { lbl: 'Kullanıcı Adı', val: username, set: setUser, ph: 'kullanici_adi' },
            { lbl: 'E-posta',       val: email,    set: setEmail, ph: 'ornek@email.com', kb: 'email-address' as const },
            { lbl: 'Şifre',         val: password, set: setPass,  ph: 'En az 8 karakter', sec: true },
          ].map(({ lbl, val, set, ph, kb, sec }) => (
            <View key={lbl} style={s.field}>
              <Text style={s.lbl}>{lbl}</Text>
              <TextInput style={s.input} placeholder={ph} placeholderTextColor={C.muted} value={val} onChangeText={set} autoCapitalize="none" keyboardType={kb} secureTextEntry={sec} />
            </View>
          ))}
          <TouchableOpacity style={[s.btn, loading && s.disabled]} onPress={register} disabled={loading}>
            {loading ? <ActivityIndicator color={C.white} /> : <Text style={s.btnTxt}>Kayıt Ol</Text>}
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  scroll:    { paddingHorizontal: 24, paddingTop: 64, paddingBottom: 40 },
  back:      { marginBottom: 24 },
  backIco:   { fontSize: 24, color: C.txt },
  title:     { fontSize: 28, fontWeight: '700', color: C.txt },
  sub:       { fontSize: 14, color: C.green, marginTop: 4, fontWeight: '600', marginBottom: 32 },
  form:      { gap: 16 },
  field:     { gap: 6 },
  lbl:       { fontSize: 12, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  input:     { backgroundColor: C.input, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, color: C.txt, borderWidth: 1, borderColor: C.border },
  btn:       { backgroundColor: C.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 8 },
  disabled:  { opacity: 0.6 },
  btnTxt:    { color: C.white, fontSize: 16, fontWeight: '700' },
});
