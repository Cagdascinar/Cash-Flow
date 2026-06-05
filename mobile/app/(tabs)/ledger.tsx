import {
  View, Text, FlatList, StyleSheet, TextInput,
  TouchableOpacity, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { C, money } from '../../constants/Colors';
import { transactions } from '../../services/api';
import { TransactionItem, type Tx } from '../../components/TransactionItem';
import { useRouter } from 'expo-router';

type Filter = 'hepsi' | 'gelir' | 'gider';

export default function LedgerScreen() {
  const router = useRouter();
  const [all,        setAll]     = useState<Tx[]>([]);
  const [filtered,   setFilt]    = useState<Tx[]>([]);
  const [search,     setSearch]  = useState('');
  const [filter,     setFilter]  = useState<Filter>('hepsi');
  const [loading,    setLoad]    = useState(true);
  const [refreshing, setRef]     = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRef(true); else setLoad(true);
    try {
      const d = await transactions.list();
      setAll(Array.isArray(d) ? d as Tx[] : []);
    } catch { }
    finally { setLoad(false); setRef(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    let list = all;
    if (filter !== 'hepsi') list = list.filter(t => t.type === filter);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(t =>
        t.category?.toLowerCase().includes(q) ||
        t.description?.toLowerCase().includes(q)
      );
    }
    setFilt(list);
  }, [all, filter, search]);

  async function del(id: number) {
    Alert.alert('Sil', 'Bu işlemi silmek istiyor musunuz?', [
      { text: 'İptal', style: 'cancel' },
      { text: 'Sil', style: 'destructive', onPress: async () => {
        try { await transactions.delete(id); setAll(p => p.filter(t => t.id !== id)); }
        catch (e: any) { Alert.alert('Hata', e.message); }
      }},
    ]);
  }

  const totalGelir = filtered.filter(t => t.type === 'gelir').reduce((s, t) => s + t.amount, 0);
  const totalGider = filtered.filter(t => t.type === 'gider').reduce((s, t) => s + t.amount, 0);

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <View style={s.header}>
        <Text style={s.title}>İşlemler</Text>
        <Text style={s.count}>{filtered.length} kayıt</Text>
      </View>

      {/* Arama */}
      <View style={s.searchWrap}>
        <View style={s.searchBox}>
          <Text>🔍</Text>
          <TextInput style={s.searchInput} placeholder="Ara…" placeholderTextColor={C.muted} value={search} onChangeText={setSearch} />
          {!!search && <TouchableOpacity onPress={() => setSearch('')}><Text style={{ color: C.muted }}>✕</Text></TouchableOpacity>}
        </View>
      </View>

      {/* Filtre + toplam */}
      <View style={s.filterRow}>
        {(['hepsi', 'gelir', 'gider'] as Filter[]).map(f => (
          <TouchableOpacity key={f} style={[s.fBtn, filter === f && s.fActive]} onPress={() => setFilter(f)}>
            <Text style={[s.fTxt, filter === f && s.fTxtActive]}>{f === 'hepsi' ? 'Hepsi' : f === 'gelir' ? 'Gelir' : 'Gider'}</Text>
          </TouchableOpacity>
        ))}
        {filter === 'gelir' && <Text style={[s.total, { color: C.green }]}>+{money(totalGelir)}</Text>}
        {filter === 'gider' && <Text style={[s.total, { color: C.red   }]}>-{money(totalGider)}</Text>}
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator size="large" color={C.blue} /></View>
        : <FlatList
            data={filtered}
            keyExtractor={i => String(i.id)}
            renderItem={({ item }) => <TransactionItem item={item} onDelete={del} onPress={(tx) => router.push({ pathname: '/edit-tx' as any, params: { id: tx.id, type: tx.type, amount: String(tx.amount), category: tx.category, description: tx.description ?? '', date: tx.date } })} />}
            ItemSeparatorComponent={() => <View style={{ height: 1, backgroundColor: C.border, marginHorizontal: 14 }} />}
            contentContainerStyle={{ paddingBottom: 24 }}
            showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={C.blue} />}
            ListEmptyComponent={
              <View style={s.empty}>
                <Text style={s.emptyIco}>{search ? '🔎' : '📭'}</Text>
                <Text style={s.emptyTxt}>{search ? 'Sonuç yok' : 'Henüz işlem yok'}</Text>
              </View>
            }
          />
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:   { flex: 1, backgroundColor: C.bg },
  center:      { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:      { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8 },
  title:       { fontSize: 24, fontWeight: '800', color: C.txt },
  count:       { fontSize: 13, color: C.txt2 },
  searchWrap:  { paddingHorizontal: 16, paddingVertical: 10 },
  searchBox:   { flexDirection: 'row', alignItems: 'center', backgroundColor: C.input, borderRadius: 12, paddingHorizontal: 12, borderWidth: 1, borderColor: C.border, gap: 8 },
  searchInput: { flex: 1, paddingVertical: 12, fontSize: 15, color: C.txt },
  filterRow:   { flexDirection: 'row', paddingHorizontal: 16, gap: 8, marginBottom: 8, alignItems: 'center' },
  fBtn:        { paddingHorizontal: 16, paddingVertical: 7, borderRadius: 20, backgroundColor: C.input, borderWidth: 1, borderColor: C.border },
  fActive:     { backgroundColor: C.blue, borderColor: C.blue },
  fTxt:        { fontSize: 13, fontWeight: '600', color: C.txt2 },
  fTxtActive:  { color: C.white },
  total:       { marginLeft: 'auto' as any, fontSize: 14, fontWeight: '800' },
  empty:       { alignItems: 'center', paddingVertical: 48 },
  emptyIco:    { fontSize: 40, marginBottom: 8 },
  emptyTxt:    { fontSize: 14, color: C.txt2 },
});
