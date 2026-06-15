import React, { useEffect, Component } from 'react';
import { Stack, useRouter, useSegments, useRootNavigationState } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View, Text, ScrollView, ActivityIndicator } from 'react-native';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { useAuthStore } from '../stores/authStore';

// ── Error Boundary ──────────────────────────────────────────────────────────
class ErrorBoundary extends Component<
  { children: React.ReactNode },
  { error: Error | null }
> {
  constructor(props: any) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error: Error) { return { error }; }
  render() {
    if (this.state.error) {
      return (
        <View style={{ flex: 1, backgroundColor: '#0b0e11', padding: 20, paddingTop: 60 }}>
          <Text style={{ color: '#f6465d', fontSize: 18, fontWeight: '700', marginBottom: 12 }}>
            🔴 Hata
          </Text>
          <ScrollView>
            <Text style={{ color: '#eaecef', fontSize: 13 }}>{this.state.error?.message}</Text>
            <Text style={{ color: '#848e9c', fontSize: 11, marginTop: 8 }}>{this.state.error?.stack}</Text>
          </ScrollView>
        </View>
      );
    }
    return this.props.children;
  }
}

// ── Root Layout ─────────────────────────────────────────────────────────────
function RootLayoutNav() {
  const { user, isLoading, hydrate } = useAuthStore();
  const router    = useRouter();
  const segments  = useSegments();
  const navState  = useRootNavigationState();

  useEffect(() => { hydrate(); }, []);

  useEffect(() => {
    if (isLoading) return;
    if (!navState?.key) return; // wait for navigator to be ready
    try {
      const inAuth = segments[0] === '(auth)';
      if (!user && !inAuth) router.replace('/(auth)/login');
      if ( user &&  inAuth) router.replace('/(tabs)');
    } catch (e) {
      console.error('nav error', e);
    }
  }, [user, isLoading, segments, navState?.key]);

  if (isLoading) {
    return (
      <View style={{ flex: 1, backgroundColor: '#0b0e11', alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator size="large" color="#007aff" />
      </View>
    );
  }

  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerShown: false,
          animation: 'ios',
          gestureEnabled: true,
          contentStyle: { backgroundColor: '#0b0e11' },
          animationDuration: 280,
        }}
      >
        {/* Auth/tabs: fade geçiş — push animasyonu değil */}
        <Stack.Screen name="(auth)" options={{ animation: 'fade', gestureEnabled: false }} />
        <Stack.Screen name="(tabs)" options={{ animation: 'fade', gestureEnabled: false }} />

        {/* Modal tarzı ekranlar — alttan yukarı açılır */}
        <Stack.Screen name="settings"      options={{ animation: 'slide_from_bottom' }} />
        <Stack.Screen name="profiles"      options={{ animation: 'slide_from_bottom' }} />
        <Stack.Screen name="help"          options={{ animation: 'slide_from_bottom' }} />
        <Stack.Screen name="telegram"      options={{ animation: 'slide_from_bottom' }} />
        <Stack.Screen name="notifications" options={{ animation: 'slide_from_bottom' }} />

        {/* Geri kalan tüm ekranlar screenOptions'dan 'ios' alır */}
        <Stack.Screen name="cards" />
        <Stack.Screen name="add-card" />
        <Stack.Screen name="accounts" />
        <Stack.Screen name="add-account" />
        <Stack.Screen name="investments" />
        <Stack.Screen name="recurring" />
        <Stack.Screen name="suppliers" />
        <Stack.Screen name="assets" />
        <Stack.Screen name="edit-tx" />
        <Stack.Screen name="transfer" />
        <Stack.Screen name="todos" />
        <Stack.Screen name="pay-card" />
        <Stack.Screen name="add-goal" />
        <Stack.Screen name="set-budget" />
        <Stack.Screen name="invoices" />
        <Stack.Screen name="rates" />
        <Stack.Screen name="card-report" />
        <Stack.Screen name="insights" />
        <Stack.Screen name="templates" />
        <Stack.Screen name="projects" />
        <Stack.Screen name="categories" />
        <Stack.Screen name="tags" />
        <Stack.Screen name="scheduled" />
        <Stack.Screen name="income-sources" />
        <Stack.Screen name="customers" />
        <Stack.Screen name="employees" />
        <Stack.Screen name="kdv" />
        <Stack.Screen name="ploss" />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ErrorBoundary>
        <RootLayoutNav />
      </ErrorBoundary>
    </GestureHandlerRootView>
  );
}
