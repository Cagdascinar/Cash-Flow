import { useRef, useState } from 'react';
import {
  StyleSheet, View, ActivityIndicator, Platform,
  TouchableOpacity, Text, BackHandler, Alert,
} from 'react-native';
import { WebView } from 'react-native-webview';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { useFocusEffect } from 'expo-router';
import { useCallback } from 'react';

const APP_URL = 'https://web-production-ba700.up.railway.app';

export default function KirpiApp() {
  const webRef  = useRef<WebView>(null);
  const [canGoBack, setCanGoBack] = useState(false);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(false);

  // Android geri tuşu — WebView'de geri git
  useFocusEffect(
    useCallback(() => {
      if (Platform.OS !== 'android') return;
      const sub = BackHandler.addEventListener('hardwareBackPress', () => {
        if (canGoBack) { webRef.current?.goBack(); return true; }
        return false;
      });
      return () => sub.remove();
    }, [canGoBack])
  );

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <StatusBar style="light" />

      {/* Hata ekranı */}
      {error && (
        <View style={s.errorBox}>
          <Text style={s.errorIco}>📡</Text>
          <Text style={s.errorTitle}>Bağlantı Kurulamadı</Text>
          <Text style={s.errorSub}>İnternet bağlantınızı kontrol edin</Text>
          <TouchableOpacity style={s.retryBtn} onPress={() => { setError(false); webRef.current?.reload(); }}>
            <Text style={s.retryTxt}>Tekrar Dene</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Loading göstergesi */}
      {loading && !error && (
        <View style={s.loadBox}>
          <Text style={s.logo}>🦔</Text>
          <Text style={s.logoTxt}>Kirpi</Text>
          <ActivityIndicator color="#0ecb81" style={{ marginTop: 24 }} />
        </View>
      )}

      {/* Ana WebView */}
      <WebView
        ref={webRef}
        source={{ uri: APP_URL }}
        style={[s.webview, (loading || error) && s.hidden]}
        onLoadStart={() => setLoading(true)}
        onLoadEnd={()  => setLoading(false)}
        onError={()    => { setLoading(false); setError(true); }}
        onHttpError={(e) => { if (e.nativeEvent.statusCode >= 500) setError(true); }}
        onNavigationStateChange={(state) => setCanGoBack(state.canGoBack)}
        // Performans
        javaScriptEnabled
        domStorageEnabled
        cacheEnabled
        startInLoadingState={false}
        // Mobil için kullanıcı ajanı — responsive tetikler
        userAgent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 KirpiApp/1.0"
        // Medya & izinler
        mediaPlaybackRequiresUserAction={false}
        allowsInlineMediaPlayback
        // iOS ayarları
        allowsBackForwardNavigationGestures
        // Güvenlik
        originWhitelist={['https://web-production-ba700.up.railway.app', 'https://*']}
        // Yeni sekmeleri engelle — uygulama içinde aç
        onShouldStartLoadWithRequest={(req) => {
          if (req.url.startsWith(APP_URL)) return true;
          if (req.url.startsWith('mailto:') || req.url.startsWith('tel:')) return false;
          return true;
        }}
      />
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0b0e11' },
  webview:   { flex: 1, backgroundColor: '#0b0e11' },
  hidden:    { opacity: 0, height: 0 },
  loadBox: {
    ...StyleSheet.absoluteFill,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0b0e11',
    zIndex: 10,
  },
  logo:    { fontSize: 64 },
  logoTxt: { fontSize: 28, fontWeight: '800', color: '#eaecef', marginTop: 12, letterSpacing: -0.5 },
  errorBox: {
    ...StyleSheet.absoluteFill,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#0b0e11',
    padding: 32,
    zIndex: 10,
  },
  errorIco:   { fontSize: 56, marginBottom: 16 },
  errorTitle: { fontSize: 20, fontWeight: '700', color: '#eaecef', marginBottom: 8 },
  errorSub:   { fontSize: 14, color: '#848e9c', textAlign: 'center', marginBottom: 32 },
  retryBtn:   { backgroundColor: '#007aff', borderRadius: 14, paddingHorizontal: 32, paddingVertical: 14 },
  retryTxt:   { fontSize: 16, fontWeight: '700', color: '#fff' },
});
