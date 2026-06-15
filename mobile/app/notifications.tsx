import {
  View, Text, StyleSheet, ActivityIndicator, TouchableOpacity,
  ScrollView, RefreshControl,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C } from '../constants/Colors';
import { misc } from '../services/api';

const URGENCY_COLOR: Record<string, string> = {
  urgent: '#ef4444',
  soon:   '#f59e0b',
  normal: C.border,
};

const CAT_ICO: Record<string, string> = {
  kart:      '💳',
  duzenli:   '🔄',
  butce:     '🎯',
  vergi:     '📊',
  tedarikci: '🏭',
  bakim:     '🔧',
  sigorta:   '🛡️',
  cek:       '📋',
  kredi:     '🏦',
  alacak:    '💰',
};

export default function NotificationsScreen() {
  const router = useRouter();
  const [notifs,  setNotifs]  = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [ref,     setRef]     = useState(false);
  const [filter,  setFilter]  = useState('');

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const d = await misc.notifications() as any;
      // API returns { ok, items, count }
      const list = Array.isArray(d) ? d : (d.items ?? d.notifications ?? []);
      setNotifs(list);
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const urgent = notifs.filter(n => n.urgency === 'urgent');
  const shown  = filter ? notifs.filter(n => n.category === filter) : notifs;
  const cats   = [...new Set(notifs.map((n: any) => n.category).filter(Boolean))];

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.backBtn}>
          <Text style={s.back}>←</Text>
        </TouchableOpacity>
        <Text style={s.title}>Bildirimler</Text>
        {notifs.length > 0 && (
          <View style={s.badge}>
            <Text style={s.badgeTxt}>{notifs.length}</Text>
          </View>
        )}
      </View>

      {/* Urgent banner */}
      {urgent.length > 0 && !loading && (
        <View style={s.urgentBanner}>
          <Text style={s.urgentBannerTxt}>🚨 {urgent.length} acil bildirim var</Text>
        </View>
      )}

      {/* Category filter pills */}
      {cats.length > 1 && !loading && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false}
          contentContainerStyle={s.pills}>
          <TouchableOpacity
            style={[s.pill, !filter && s.pillActive]}
            onPress={() => setFilter('')}>
            <Text style={[s.pillTxt, !filter && s.pillTxtActive]}>Tümü</Text>
          </TouchableOpacity>
          {cats.map(cat => (
            <TouchableOpacity key={cat}
              style={[s.pill, filter === cat && s.pillActive]}
              onPress={() => setFilter(filter === cat ? '' : cat)}>
              <Text style={[s.pillTxt, filter === cat && s.pillTxtActive]}>
                {CAT_ICO[cat] ?? '📌'} {cat}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} size="large" /></View>
        : <ScrollView
            showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}
            contentContainerStyle={{ padding: 16, paddingBottom: 48 }}>

            {shown.length === 0
              ? (
                <View style={s.empty}>
                  <Text style={s.emptyIco}>🔔</Text>
                  <Text style={s.emptyTitle}>Bildirim yok</Text>
                  <Text style={s.emptyTxt}>Şu an için herhangi bir uyarı veya hatırlatma bulunmuyor.</Text>
                </View>
              )
              : shown.map((n: any, i: number) => (
                <View key={i} style={[s.card, { borderLeftColor: URGENCY_COLOR[n.urgency] ?? C.border }]}>
                  <View style={s.cardLeft}>
                    <Text style={s.ico}>{n.icon ?? CAT_ICO[n.category] ?? '📌'}</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <View style={s.cardTop}>
                      <Text style={s.cardTitle} numberOfLines={1}>{n.title}</Text>
                      {n.urgency === 'urgent' && (
                        <View style={s.urgentPill}>
                          <Text style={s.urgentPillTxt}>ACİL</Text>
                        </View>
                      )}
                      {n.urgency === 'soon' && (
                        <View style={[s.urgentPill, { backgroundColor: 'rgba(245,158,11,.15)' }]}>
                          <Text style={[s.urgentPillTxt, { color: '#f59e0b' }]}>YAKINDA</Text>
                        </View>
                      )}
                    </View>
                    <Text style={s.body}>{n.body}</Text>
                    {n.days !== undefined && (
                      <Text style={[s.days, { color: URGENCY_COLOR[n.urgency] ?? C.muted }]}>
                        {n.days <= 0
                          ? `${Math.abs(n.days)} gün geçti`
                          : n.days === 0 ? 'Bugün'
                          : `${n.days} gün kaldı`}
                      </Text>
                    )}
                  </View>
                </View>
              ))
            }
          </ScrollView>
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:           { flex: 1, backgroundColor: C.bg },
  center:       { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:       { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 10, gap: 10 },
  backBtn:      { padding: 4 },
  back:         { fontSize: 24, color: C.txt },
  title:        { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  badge:        { backgroundColor: C.red, borderRadius: 12, paddingHorizontal: 8, paddingVertical: 2 },
  badgeTxt:     { color: '#fff', fontSize: 12, fontWeight: '800' },
  urgentBanner: { backgroundColor: 'rgba(239,68,68,.12)', borderRadius: 10, marginHorizontal: 16, marginBottom: 10, padding: 10 },
  urgentBannerTxt: { color: C.red, fontWeight: '700', fontSize: 13 },
  pills:        { paddingHorizontal: 16, gap: 8, paddingBottom: 10, flexDirection: 'row' },
  pill:         { backgroundColor: C.card, borderRadius: 20, paddingHorizontal: 14, paddingVertical: 6, borderWidth: 1, borderColor: C.border },
  pillActive:   { backgroundColor: C.blue, borderColor: C.blue },
  pillTxt:      { fontSize: 12, fontWeight: '600', color: C.txt2 },
  pillTxtActive:{ color: '#fff' },
  card:         { flexDirection: 'row', backgroundColor: C.card, borderRadius: 14, padding: 14, marginBottom: 10, borderWidth: 1, borderColor: C.border, borderLeftWidth: 3, gap: 12 },
  cardLeft:     { paddingTop: 2 },
  ico:          { fontSize: 22 },
  cardTop:      { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 },
  cardTitle:    { fontSize: 14, fontWeight: '700', color: C.txt, flex: 1 },
  body:         { fontSize: 13, color: C.txt2, lineHeight: 19 },
  days:         { fontSize: 12, fontWeight: '600', marginTop: 5 },
  urgentPill:   { backgroundColor: 'rgba(239,68,68,.15)', borderRadius: 8, paddingHorizontal: 7, paddingVertical: 2 },
  urgentPillTxt:{ color: C.red, fontSize: 10, fontWeight: '800', letterSpacing: 0.5 },
  empty:        { alignItems: 'center', paddingVertical: 60 },
  emptyIco:     { fontSize: 56, marginBottom: 16 },
  emptyTitle:   { fontSize: 18, fontWeight: '800', color: C.txt, marginBottom: 8 },
  emptyTxt:     { fontSize: 14, color: C.txt2, textAlign: 'center', paddingHorizontal: 32, lineHeight: 21 },
});
