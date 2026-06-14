import {
  View, Text, ScrollView, StyleSheet, ActivityIndicator,
  RefreshControl, TouchableOpacity,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { C, money, fmtDate } from '../constants/Colors';
import { transactions as txApi } from '../services/api';

export default function TagsScreen() {
  const router = useRouter();
  const [allTx,     setAllTx]    = useState<any[]>([]);
  const [loading,   setLoading]  = useState(true);
  const [ref,       setRef]      = useState(false);
  const [activeTag, setActiveTag] = useState<string | null>(null);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoading(true);
    try {
      const data = await txApi.list({ per_page: '500' });
      setAllTx(Array.isArray(data) ? data : (data as any)?.data ?? []);
    } catch {}
    finally { setLoading(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const tagMap: Record<string, number> = {};
  allTx.forEach(tx => {
    const tags = (tx.tags ?? '').split(',').map((t: string) => t.trim()).filter(Boolean);
    tags.forEach((t: string) => { tagMap[t] = (tagMap[t] || 0) + 1; });
  });
  const tags = Object.entries(tagMap).sort((a, b) => b[1] - a[1]);

  const filtered = activeTag
    ? allTx.filter(tx => {
        const tags = (tx.tags ?? '').split(',').map((t: string) => t.trim());
        return tags.includes(activeTag);
      })
    : [];

  return (
    <SafeAreaView style={s.bg} edges={['top']}>
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()}><Text style={s.back}>←</Text></TouchableOpacity>
        <Text style={s.title}>Etiketler</Text>
        {activeTag && (
          <TouchableOpacity onPress={() => setActiveTag(null)}>
            <Text style={{ color: C.blue, fontSize: 14, fontWeight: '600' }}>Temizle</Text>
          </TouchableOpacity>
        )}
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator color={C.blue} /></View>
        : <ScrollView showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={ref} onRefresh={() => load(true)} tintColor={C.blue} />}>

            {tags.length === 0 ? (
              <View style={s.empty}>
                <Text style={s.emptyIco}>🏷️</Text>
                <Text style={s.emptyTxt}>Henüz etiket yok</Text>
                <Text style={s.emptySub}>İşlem eklerken etiket kullanabilirsiniz</Text>
              </View>
            ) : (
              <>
                <Text style={s.sect}>Tüm Etiketler</Text>
                <View style={s.cloud}>
                  {tags.map(([tag, count]) => (
                    <TouchableOpacity key={tag}
                      style={[s.tagChip, activeTag === tag && s.tagChipActive]}
                      onPress={() => setActiveTag(activeTag === tag ? null : tag)}>
                      <Text style={[s.tagTxt, activeTag === tag && s.tagTxtActive]}>
                        🏷️ {tag}
                      </Text>
                      <View style={[s.tagBadge, activeTag === tag && s.tagBadgeActive]}>
                        <Text style={[s.tagBadgeTxt, activeTag === tag && { color: C.white }]}>{count}</Text>
                      </View>
                    </TouchableOpacity>
                  ))}
                </View>

                {activeTag && (
                  <>
                    <Text style={s.sect}>"{activeTag}" İşlemleri ({filtered.length})</Text>
                    {filtered.map(tx => (
                      <View key={tx.id} style={s.txRow}>
                        <View style={{ flex: 1 }}>
                          <Text style={s.txDesc} numberOfLines={1}>{tx.description || tx.category}</Text>
                          <Text style={s.txDate}>{fmtDate(tx.date)} · {tx.category}</Text>
                        </View>
                        <Text style={[s.txAmt, { color: tx.type === 'gelir' ? C.green : C.red }]}>
                          {tx.type === 'gelir' ? '+' : '-'}{money(tx.amount)}
                        </Text>
                      </View>
                    ))}
                  </>
                )}
              </>
            )}

            <View style={{ height: 40 }} />
          </ScrollView>
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  bg:           { flex: 1, backgroundColor: C.bg },
  center:       { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:       { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, gap: 12 },
  back:         { fontSize: 24, color: C.txt },
  title:        { fontSize: 20, fontWeight: '800', color: C.txt, flex: 1 },
  sect:         { fontSize: 11, fontWeight: '700', color: C.muted, textTransform: 'uppercase', letterSpacing: 1.1, paddingHorizontal: 16, marginTop: 20, marginBottom: 10 },
  cloud:        { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 16, gap: 8 },
  tagChip:      { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 12, paddingVertical: 8, backgroundColor: C.card, borderRadius: 20, borderWidth: 1, borderColor: C.border },
  tagChipActive:{ backgroundColor: C.blue, borderColor: C.blue },
  tagTxt:       { fontSize: 13, color: C.txt2 },
  tagTxtActive: { color: C.white, fontWeight: '600' },
  tagBadge:     { backgroundColor: C.input, borderRadius: 10, paddingHorizontal: 6, paddingVertical: 1 },
  tagBadgeActive:{ backgroundColor: 'rgba(255,255,255,0.25)' },
  tagBadgeTxt:  { fontSize: 11, fontWeight: '700', color: C.txt2 },
  txRow:        { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 6, backgroundColor: C.card, borderRadius: 12, padding: 12, borderWidth: 1, borderColor: C.border, gap: 10 },
  txDesc:       { fontSize: 14, fontWeight: '600', color: C.txt },
  txDate:       { fontSize: 12, color: C.txt2, marginTop: 2 },
  txAmt:        { fontSize: 14, fontWeight: '800' },
  empty:        { alignItems: 'center', paddingVertical: 60 },
  emptyIco:     { fontSize: 52, marginBottom: 12 },
  emptyTxt:     { fontSize: 16, color: C.txt, fontWeight: '700', marginBottom: 4 },
  emptySub:     { fontSize: 13, color: C.txt2, textAlign: 'center', paddingHorizontal: 40 },
});
