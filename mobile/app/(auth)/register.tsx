import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  KeyboardAvoidingView, Platform, ActivityIndicator, Alert, ScrollView,
} from 'react-native';
import { useState } from 'react';
import { useRouter } from 'expo-router';
import { Colors } from '../../constants/Colors';
import { auth } from '../../services/api';

export default function RegisterScreen() {
  const [username, setUsername] = useState('');
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [loading,  setLoading]  = useState(false);
  const router = useRouter();

  async function handleRegister() {
    if (!username.trim() || !email.trim() || !password.trim()) {
      Alert.alert('Hata', 'Tüm alanlar gerekli'); return;
    }
    setLoading(true);
    try {
      await auth.register(username.trim(), email.trim(), password);
      Alert.alert('Kayıt Başarılı', 'E-posta adresinize doğrulama bağlantısı gönderildi.', [
        { text: 'Giriş Yap', onPress: () => router.replace('/(auth)/login') },
      ]);
    } catch (e: any) {
      Alert.alert('Hata', e.message ?? 'Bir hata oluştu');
    } finally { setLoading(false); }
  }

  return (
    <KeyboardAvoidingView style={s.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={s.scroll} showsVerticalScrollIndicator={false}>
        <TouchableOpacity onPress={() => router.back()} style={s.back}>
          <Text style={s.backIcon}>←</Text>
        </TouchableOpacity>

        <Text style={s.title}>Hesap Oluştur</Text>
        <Text style={s.sub}>30 gün ücretsiz premium</Text>

        <View style={s.form}>
          {[
            { label: 'Kullanıcı adı', value: username, set: setUsername, placeholder: 'kullanici_adi', cap: 'none' as const },
            { label: 'E-posta',       value: email,    set: setEmail,    placeholder: 'ornek@email.com', cap: 'none' as const, kb: 'email-address' as const },
            { label: 'Şifre',         value: password, set: setPassword, placeholder: 'En az 8 karakter', secure: true },
          ].map(({ label, value, set, placeholder, cap, kb, secure }) => (
            <View key={label} style={s.field}>
              <Text style={s.label}>{label}</Text>
              <TextInput
                style={s.input}
                placeholder={placeholder}
                placeholderTextColor={Colors.textMuted}
                value={value}
                onChangeText={set}
                autoCapitalize={cap ?? 'none'}
                keyboardType={kb}
                secureTextEntry={secure}
              />
            </View>
          ))}

          <TouchableOpacity
            style={[s.btn, loading && s.disabled]}
            onPress={handleRegister}
            disabled={loading}
          >
            {loading
              ? <ActivityIndicator color={Colors.white} />
              : <Text style={s.btnText}>Kayıt Ol</Text>
            }
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.bg },
  scroll:    { paddingHorizontal: 24, paddingTop: 64, paddingBottom: 40 },
  back:      { marginBottom: 24 },
  backIcon:  { fontSize: 24, color: Colors.textPrimary },
  title:     { fontSize: 28, fontWeight: '700', color: Colors.textPrimary },
  sub:       { fontSize: 14, color: Colors.green, marginTop: 4, fontWeight: '600', marginBottom: 32 },
  form:      { gap: 16 },
  field:     { gap: 6 },
  label:     { fontSize: 13, fontWeight: '600', color: Colors.textSecondary, textTransform: 'uppercase', letterSpacing: 0.8 },
  input:     { backgroundColor: Colors.bgInput, borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14, fontSize: 16, color: Colors.textPrimary, borderWidth: 1, borderColor: Colors.border },
  btn:       { backgroundColor: Colors.blue, borderRadius: 14, paddingVertical: 16, alignItems: 'center', marginTop: 8 },
  disabled:  { opacity: 0.6 },
  btnText:   { color: Colors.white, fontSize: 16, fontWeight: '700' },
});
