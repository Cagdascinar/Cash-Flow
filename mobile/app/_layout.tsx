import { useEffect } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuthStore } from '../stores/authStore';

export default function RootLayout() {
  const { user, isLoading, hydrate } = useAuthStore();
  const router  = useRouter();
  const segments = useSegments();

  useEffect(() => { hydrate(); }, []);

  useEffect(() => {
    if (isLoading) return;
    const inAuth = segments[0] === '(auth)';
    if (!user && !inAuth)  router.replace('/(auth)/login');
    if (user  &&  inAuth)  router.replace('/(tabs)');
  }, [user, isLoading, segments]);

  return (
    <>
      <StatusBar style="light" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(auth)"  />
        <Stack.Screen name="(tabs)"  />
        <Stack.Screen name="cards"    options={{ presentation: 'card' }} />
        <Stack.Screen name="accounts" options={{ presentation: 'card' }} />
      </Stack>
    </>
  );
}
