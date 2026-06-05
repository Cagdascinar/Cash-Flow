import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity, ScrollView, RefreshControl } from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money } from '../constants/Colors';
import { misc } from '../services/api';

export default function NotificationsScreen() {
  const router = useRouter();
  const [notifs,  setNotifs]  = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const d = await misc.notifications() as any;
      setNotifs(Array.isArray(d) ? d : (d.notifications ?? []));
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const TYPE_ICO: Record<string, string> = {
    card_payment: '💳', recurring: '🔄', budget_limit: '⚠️',
    goal: '🎯', reminder: '🔔', info: 'ℹ️',
  };

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Bildirimler</Text>
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>
            {notifs.length === 0
              ? <View style={s.empty}><Text style={s.emptyIco}>🔔</Text><Text style={s.emptyTxt}>Bildirim yok</Text></View>
              : notifs.map((n: any, i: number) => (
                  <View key={i} style={[s.card, n.urgent && { borderColor: C.red }]}>
                    <Text style={s.ico}>{TYPE_ICO[n.type] ?? '📌'}</Text>
                    <View style={{ flex: 1 }}>
                      <Text style={s.title2}>{n.title ?? n.message}</Text>
                      {n.body && <Text style={s.body}>{n.body}</Text>}
                      {n.amount && <Text style={[s.amount, { color: n.type === 'budget_limit' ? C.red : C.txt }]}>{money(n.amount)}</Text>}
                    </View>
                    {n.urgent && <View style={s.urgentDot} />}
                  </View>
                ))
            }
            <View style={{ height: 40 }} />
          </ScrollView>
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:        { flex: 1, backgroundColor: C.bg },
  center:    { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:    { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 8, gap: 12 },
  back:      { fontSize: 24, color: C.txt },
  title:     { fontSize: 20, fontWeight: '800', color: C.txt },
  card:      { flexDirection: 'row', alignItems: 'flex-start', marginHorizontal: 16, marginTop: 10, backgroundColor: C.card, borderRadius: 14, padding: 14, borderWidth: 1, borderColor: C.border, gap: 12 },
  ico:       { fontSize: 22 },
  title2:    { fontSize: 14, fontWeight: '700', color: C.txt },
  body:      { fontSize: 13, color: C.txt2, marginTop: 3, lineHeight: 20 },
  amount:    { fontSize: 14, fontWeight: '700', marginTop: 4 },
  urgentDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: C.red, marginTop: 4 },
  empty:     { alignItems: 'center', paddingVertical: 48 },
  emptyIco:  { fontSize: 48, marginBottom: 12 },
  emptyTxt:  { fontSize: 15, color: C.txt2 },
});
