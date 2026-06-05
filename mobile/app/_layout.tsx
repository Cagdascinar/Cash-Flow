import { useEffect } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from '../stores/authStore';

export default function RootLayout() {
  const { user, isLoading, hydrate } = useAuthStore();
  const router   = useRouter();
  const segments = useSegments();

  useEffect(() => { hydrate(); }, []);

  useEffect(() => {
    if (isLoading) return;
    const inAuth = segments[0] === '(auth)';
    if (!user && !inAuth) router.replace('/(auth)/login');
    if ( user &&  inAuth) router.replace('/(tabs)');
  }, [user, isLoading, segments]);

  return (
    <>
      <StatusBar style="light" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="cards"        options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="add-card"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="accounts"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="add-account"  options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="investments"  options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="recurring"    options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="suppliers"    options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="assets"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="telegram"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="settings"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="edit-tx"      options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="transfer"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="todos"        options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="pay-card"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="add-goal"     options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="set-budget"   options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="invoices"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="rates"          options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="card-report"    options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="notifications"  options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="profiles"       options={{ animation: 'slide_from_right' }} />
        <Stack.Screen name="insights"       options={{ animation: 'slide_from_right' }} />
      </Stack>
    </>
  );
}
