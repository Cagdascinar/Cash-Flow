import { View, Text, ScrollView, StyleSheet, ActivityIndicator, RefreshControl, TouchableOpacity } from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money, fmtDate } from '../../constants/Colors';
import { summary as summaryApi, transactions, misc } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';
import { BalanceCard } from '../../components/BalanceCard';
import { WelcomeHero } from '../../components/WelcomeHero';
import { TransactionItem, type Tx } from '../../components/TransactionItem';

type Period = 'ay' | 'yil' | 'tum';
const PERIOD_MAP: Record<Period, string> = { ay: 'month', yil: 'year', tum: 'all' };

export default function Dashboard() {
  const { user, activeProfile } = useAuthStore();
  const router = useRouter();
  const [sum,        setSum]      = useState<any>(null);
  const [recent,     setRecent]   = useState<Tx[]>([]);
  const [today,      setToday]    = useState<any>(null);
  const [reminders,  setReminders]= useState<any[]>([]);
  const [quote,      setQuote]    = useState<string | undefined>(undefined);
  const [period,     setPeriod]   = useState<Period>('ay');
  const [loading,    setLoad]     = useState(true);
  const [refreshing, setRef]      = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoad(true);
    try {
      const now = new Date();
      const [s, tx, tod, rem, mot] = await Promise.all([
        summaryApi.get(PERIOD_MAP[period], now.getFullYear(), period === 'ay' ? now.getMonth() + 1 : undefined),
        transactions.list({ per_page: '10' }),
        misc.today().catch(() => null),
        misc.reminders().catch(() => []),
        misc.motivation().catch(() => null),
      ]);
      setSum(s);
      setRecent(Array.isArray(tx) ? (tx as Tx[]).slice(0, 8) : []);
      setToday(tod);
      setReminders(Array.isArray(rem) ? rem.slice(0, 5) : []);
      setQuote(mot?.quote ?? mot?.message ?? undefined);
    } catch (e) {
      console.warn('dashboard load error', e);
    } finally { setLoad(false); setRef(false); }
  }, [period, activeProfile?.id]);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <SafeAreaView style={s.container}>
      <View style={s.center}><ActivityIndicator size="large" color={C.blue} /></View>
    </SafeAreaView>
  );

  const gelir = sum?.gelir ?? 0;
  const gider = sum?.gider ?? 0;
  const net   = sum?.net   ?? 0;

  const todayGelir: any[] = today?.gelir ?? [];
  const todayGider: any[] = today?.gider ?? [];

  // Top 4 harcama kategorisi
  const giderCats: Record<string, number> = sum?.gider_cats ?? {};
  const topCats = Object.entries(giderCats)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4);

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={C.blue} />}
      >
        <WelcomeHero
          username={user?.username ?? ''}
          profileName={activeProfile?.name}
          profileType={activeProfile?.type}
          avatar={activeProfile?.avatar}
          isPremium={user?.is_premium}
          quote={quote}
          onAvatarPress={() => router.push('/profiles' as any)}
        />

        <BalanceCard
          gelir={gelir} gider={gider} net={net}
          kullanilabilir={sum?.kullanilabilir_nakit ?? net}
          kartBorcu={sum?.kart_borcu ?? 0}
          period={period}
          onPeriod={setPeriod}
        />

        {/* Kısa linkler */}
        <View style={[s.section, { flexDirection: 'row', gap: 8, marginTop: 16 }]}>
          <TouchableOpacity style={s.quickBtn} onPress={() => router.push('/(tabs)/budget' as any)}>
            <Text style={s.quickIco}>🎯</Text><Text style={s.quickTxt}>Bütçe</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.quickBtn} onPress={() => router.push('/investments' as any)}>
            <Text style={s.quickIco}>📈</Text><Text style={s.quickTxt}>Yatırım</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.quickBtn} onPress={() => router.push('/rates' as any)}>
            <Text style={s.quickIco}>💱</Text><Text style={s.quickTxt}>Kurlar</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.quickBtn} onPress={() => router.push('/transfer' as any)}>
            <Text style={s.quickIco}>🔄</Text><Text style={s.quickTxt}>Transfer</Text>
          </TouchableOpacity>
        </View>

        {/* Hatırlatıcılar */}
        {reminders.length > 0 && (
          <View style={s.section}>
            <Text style={s.sTitle}>🔔 Hatırlatıcılar</Text>
            <View style={s.remList}>
              {reminders.map((r: any, i: number) => (
                <View key={i} style={[s.remItem, i < reminders.length - 1 && s.remBorder]}>
                  <Text style={s.remIco}>{r.type === 'card' ? '💳' : r.type === 'recurring' ? '🔄' : '📌'}</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={s.remName}>{r.name ?? r.description}</Text>
                    {r.due_date && <Text style={s.remDate}>{fmtDate(r.due_date)}</Text>}
                  </View>
                  {r.amount && <Text style={[s.remAmt, { color: '#f87171' }]}>{money(r.amount)}</Text>}
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Bugünün işlemleri */}
        {(todayGelir.length > 0 || todayGider.length > 0) && (
          <View style={s.section}>
            <Text style={s.sTitle}>📅 Bugün</Text>
            <View style={s.list}>
              {[...todayGelir, ...todayGider].map((tx: any, i: number) => (
                <View key={tx.id}>
                  <TransactionItem item={tx} onPress={(t) => router.push({ pathname: '/edit-tx' as any, params: { id: t.id, type: t.type, amount: String(t.amount), category: t.category, description: t.description ?? '', date: t.date, project_id: t.project_id ? String(t.project_id) : '' } })} />
                  {i < todayGelir.length + todayGider.length - 1 && <View style={s.sep} />}
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Kategori dağılımı */}
        {topCats.length > 0 && (
          <View style={s.section}>
            <Text style={s.sTitle}>📊 En Yüksek Giderler</Text>
            <View style={s.catCard}>
              {topCats.map(([cat, amt], i) => {
                const pct = gider > 0 ? (amt / gider) * 100 : 0;
                const barColor = pct > 40 ? '#f87171' : pct > 20 ? '#fbbf24' : '#60a5fa';
                return (
                  <View key={cat}>
                    <View style={s.catRow}>
                      <Text style={s.catName} numberOfLines={1}>{cat}</Text>
                      <Text style={[s.catAmt, { color: '#f87171' }]}>{money(amt)}</Text>
                      <Text style={s.catPct}>%{Math.round(pct)}</Text>
                    </View>
                    <View style={s.barTrack}>
                      <View style={[s.barFill, { width: `${pct}%` as any, backgroundColor: barColor }]} />
                    </View>
                    {i < topCats.length - 1 && <View style={{ height: 12 }} />}
                  </View>
                );
              })}
            </View>
          </View>
        )}

        {/* Son işlemler */}
        <View style={s.section}>
          <View style={s.sRow}>
            <Text style={s.sTitle}>Son İşlemler</Text>
            <TouchableOpacity onPress={() => router.push('/(tabs)/ledger' as any)}>
              <Text style={s.seeAll}>Tümünü Gör →</Text>
            </TouchableOpacity>
          </View>
          {recent.length === 0
            ? <View style={s.empty}><Text style={s.emptyIco}>📭</Text><Text style={s.emptyTxt}>Henüz işlem yok</Text></View>
            : <View style={s.list}>
                {recent.map((tx, i) => (
                  <View key={tx.id}>
                    <TransactionItem item={tx} onPress={(t) => router.push({ pathname: '/edit-tx' as any, params: { id: t.id, type: t.type, amount: String(t.amount), category: t.category, description: t.description ?? '', date: t.date, project_id: t.project_id ? String(t.project_id) : '' } })} />
                    {i < recent.length - 1 && <View style={s.sep} />}
                  </View>
                ))}
              </View>
          }
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: C.bg },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center' },
  section:     { marginTop: 20, paddingHorizontal: 16 },
  sRow:        { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  sTitle:      { fontSize: 12, fontWeight: '700', color: C.txt2, textTransform: 'uppercase', letterSpacing: 0.8 },
  seeAll:      { fontSize: 12, fontWeight: '600', color: C.blue },
  remList:     { backgroundColor: C.card, borderRadius: 14, borderWidth: 1, borderColor: C.border, overflow: 'hidden' },
  remItem:     { flexDirection: 'row', alignItems: 'center', padding: 12, gap: 10 },
  remBorder:   { borderBottomWidth: 1, borderBottomColor: C.border },
  remIco:      { fontSize: 18 },
  remName:     { fontSize: 14, fontWeight: '600', color: C.txt },
  remDate:     { fontSize: 12, color: C.txt2, marginTop: 2 },
  remAmt:      { fontSize: 14, fontWeight: '700' },
  list:        { backgroundColor: C.card, borderRadius: 16, borderWidth: 1, borderColor: C.border, overflow: 'hidden' },
  sep:         { height: 1, backgroundColor: C.border, marginHorizontal: 14 },
  empty:       { alignItems: 'center', paddingVertical: 32, backgroundColor: C.card, borderRadius: 16, borderWidth: 1, borderColor: C.border },
  emptyIco:    { fontSize: 40, marginBottom: 8 },
  emptyTxt:    { fontSize: 14, color: C.txt2 },
  quickBtn:    { flex: 1, backgroundColor: C.card, borderRadius: 12, borderWidth: 1, borderColor: C.border, alignItems: 'center', paddingVertical: 10, gap: 4 },
  quickIco:    { fontSize: 20 },
  quickTxt:    { fontSize: 10, fontWeight: '600', color: C.txt2 },
  catCard:     { backgroundColor: C.card, borderRadius: 16, borderWidth: 1, borderColor: C.border, padding: 14 },
  catRow:      { flexDirection: 'row', alignItems: 'center', gap: 8 },
  catName:     { flex: 1, fontSize: 13, fontWeight: '600', color: C.txt },
  catAmt:      { fontSize: 13, fontWeight: '700' },
  catPct:      { fontSize: 11, color: C.txt2, minWidth: 30, textAlign: 'right' },
  barTrack:    { height: 4, backgroundColor: C.input, borderRadius: 2, marginTop: 5, overflow: 'hidden' },
  barFill:     { height: '100%', borderRadius: 2 },
});
