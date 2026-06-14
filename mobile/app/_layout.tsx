import React, { useEffect, Component } from 'react';
import { Stack, useRouter, useSegments, useRootNavigationState } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View, Text, ScrollView, ActivityIndicator } from 'react-native';
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
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="cards"          options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="add-card"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="accounts"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="add-account"    options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="investments"    options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="recurring"      options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="suppliers"      options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="assets"         options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="telegram"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="settings"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="edit-tx"        options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="transfer"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="todos"          options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="pay-card"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="add-goal"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="set-budget"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="invoices"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="rates"          options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="card-report"    options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="notifications"  options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="profiles"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="insights"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="templates"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="projects"      options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="categories"    options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="tags"          options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="scheduled"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="income-sources" options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="changelog"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="help"          options={{ animation: 'slide_from_right' }} />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return (
    <ErrorBoundary>
      <RootLayoutNav />
    </ErrorBoundary>
  );
}
