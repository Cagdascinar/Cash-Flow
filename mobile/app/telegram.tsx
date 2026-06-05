import { View, Text, StyleSheet, TouchableOpacity, Alert, ActivityIndicator, TextInput } from 'react-native';
import { useState, useEffect } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { misc } from '../services/api';

export default function TelegramScreen() {
  const router = useRouter();
  const [status,  setStatus]  = useState<any>(null);
  const [code,    setCode]    = useState('');
  const [loading, setLoading] = useState(true);
  const [genning, setGenning] = useState(false);

  useEffect(() => {
    misc.telegramStatus().then(d => setStatus(d)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function generateCode() {
    setGenning(true);
    try {
      const d = await misc.telegramLinkCode() as any;
      setCode(d.code ?? '');
    } catch (e: any) { Alert.alert('Hata', e.message); }
    finally { setGenning(false); }
  }

  async function unlink() {
    Alert.alert('Bot Bağlantısını Kes', 'Telegram bağlantısını kesmek istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Bağlantıyı Kes', style: 'destructive', onPress: async () => {
        try {
          await misc.telegramUnlink();
          setStatus({ linked: false });
          setCode('');
        } catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Telegram Botu</Text>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <View style={s.content}>
            <View style={s.botCard}>
              <Text style={s.botIco}>🤖</Text>
              <Text style={s.botName}>@KirpiNakitBot</Text>
              <Text style={s.botDesc}>Telegram üzerinden hızlıca işlem girin.{'\n'}"50 tl market" yazmanız yeterli!</Text>
            </View>

            {status?.linked
              ? <>
                  <View style={s.linkedCard}>
                    <Text style={s.linkedIco}>✅</Text>
                    <Text style={s.linkedTxt}>Bağlı: @{status.telegram_username ?? 'kullanıcı'}</Text>
                  </View>
                  <TouchableOpacity style={s.unlinkBtn} onPress={unlink}>
                    <Text style={s.unlinkTxt}>🔗 Bağlantıyı Kes</Text>
                  </TouchableOpacity>
                </>
              : <>
                  <Text style={s.step}>Nasıl bağlanılır:</Text>
                  <View style={s.steps}>
                    {['1. Aşağıdan kod alın', '2. Telegram\'da @KirpiNakitBot\'u bulun', '3. /start komutunu gönderin', '4. Kodu bot\'a gönderin'].map((t, i) => (
                      <Text key={i} style={s.stepTxt}>{t}</Text>
                    ))}
                  </View>

                  {code
                    ? <View style={s.codeCard}>
                        <Text style={s.codeLbl}>Bağlantı Kodu</Text>
                        <Text style={s.code}>{code}</Text>
                        <Text style={s.codeExp}>Bu kodu Telegram botuna gönderin</Text>
                      </View>
                    : <TouchableOpacity style={[s.genBtn, genning && { opacity: 0.6 }]} onPress={generateCode} disabled={genning}>
                        {genning ? <ActivityIndicator color={C.white} /> : <Text style={s.genTxt}>🔑 Kod Al</Text>}
                      </TouchableOpacity>
                  }
                </>
            }
          </View>
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:         { flex: 1, backgroundColor: C.bg },
  center:     { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:     { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:       { fontSize: 24, color: C.txt },
  title:      { fontSize: 20, fontWeight: '800', color: C.txt },
  content:    { padding: 16 },
  botCard:    { backgroundColor: C.card, borderRadius: 16, padding: 20, borderWidth: 1, borderColor: C.border, alignItems: 'center', marginBottom: 20 },
  botIco:     { fontSize: 48, marginBottom: 8 },
  botName:    { fontSize: 18, fontWeight: '700', color: C.blue, marginBottom: 8 },
  botDesc:    { fontSize: 14, color: C.txt2, textAlign: 'center', lineHeight: 22 },
  linkedCard: { backgroundColor: 'rgba(14,203,129,.1)', borderRadius: 12, padding: 16, borderWidth: 1, borderColor: 'rgba(14,203,129,.3)', flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 12 },
  linkedIco:  { fontSize: 20 },
  linkedTxt:  { fontSize: 15, fontWeight: '600', color: C.green },
  unlinkBtn:  { backgroundColor: C.input, borderRadius: 12, padding: 14, alignItems: 'center', borderWidth: 1, borderColor: C.border },
  unlinkTxt:  { fontSize: 15, fontWeight: '600', color: C.txt2 },
  step:       { fontSize: 12, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 },
  steps:      { backgroundColor: C.card, borderRadius: 12, padding: 14, borderWidth: 1, borderColor: C.border, gap: 8, marginBottom: 20 },
  stepTxt:    { fontSize: 14, color: C.txt, lineHeight: 22 },
  codeCard:   { backgroundColor: C.hero, borderRadius: 16, padding: 20, alignItems: 'center', borderWidth: 1, borderColor: 'rgba(99,160,255,.2)' },
  codeLbl:    { fontSize: 12, color: 'rgba(255,255,255,.45)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 },
  code:       { fontSize: 32, fontWeight: '900', color: C.white, letterSpacing: 4 },
  codeExp:    { fontSize: 13, color: 'rgba(255,255,255,.45)', marginTop: 8 },
  genBtn:     { backgroundColor: C.blue, borderRadius: 14, padding: 16, alignItems: 'center' },
  genTxt:     { fontSize: 16, fontWeight: '700', color: C.white },
});
