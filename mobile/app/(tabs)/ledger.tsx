import {
  View, Text, FlatList, StyleSheet, TextInput,
  TouchableOpacity, ActivityIndicator, RefreshControl, Alert,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../../constants/Colors';
import { transactions } from '../../services/api';
import { TransactionItem } from '../../components/TransactionItem';

type Filter = 'hepsi' | 'gelir' | 'gider';
const FILTERS: { key: Filter; label: string }[] = [
  { key: 'hepsi', label: 'Hepsi' },
  { key: 'gelir', label: 'Gelir' },
  { key: 'gider', label: 'Gider' },
];

export default function LedgerScreen() {
  const [all,        setAll]        = useState<any[]>([]);
  const [filtered,   setFiltered]   = useState<any[]>([]);
  const [search,     setSearch]     = useState('');
  const [filter,     setFilter]     = useState<Filter>('hepsi');
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (pull = false) => {
    if (pull) setRefreshing(true); else setLoading(true);
    try {
      const data = await transactions.list();
      setAll(Array.isArray(data) ? data : []);
    } catch {}
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    let list = all;
    if (filter !== 'hepsi') list = list.filter(t => t.type === filter);
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(t =>
        t.description?.toLowerCase().includes(q) ||
        t.category?.toLowerCase().includes(q)
      );
    }
    setFiltered(list);
  }, [all, filter, search]);

  async function onDelete(id: number) {
    Alert.alert('İşlemi Sil', 'Bu işlemi silmek istediğinize emin misiniz?', [
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
      {/* Başlık */}
      <View style={s.header}>
        <Text style={s.title}>İşlemler</Text>
        <Text style={s.count}>{filtered.length} kayıt</Text>
      </View>

      {/* Arama */}
      <View style={s.searchRow}>
        <View style={s.searchBox}>
          <Text style={s.searchIco}>🔍</Text>
          <TextInput
            style={s.searchInput}
            placeholder="Ara..."
            placeholderTextColor={Colors.textMuted}
            value={search}
            onChangeText={setSearch}
          />
          {search.length > 0 && (
            <TouchableOpacity onPress={() => setSearch('')}>
              <Text style={s.clearBtn}>✕</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Filtre */}
      <View style={s.filterRow}>
        {FILTERS.map(f => (
          <TouchableOpacity
            key={f.key}
            style={[s.filterBtn, filter === f.key && s.filterActive]}
            onPress={() => setFilter(f.key)}
          >
            <Text style={[s.filterTxt, filter === f.key && s.filterTxtActive]}>{f.label}</Text>
          </TouchableOpacity>
        ))}
        {filter !== 'hepsi' && (
          <View style={s.totalBadge}>
            <Text style={s.totalTxt}>
              {filter === 'gelir'
                ? `+₺${totalGelir.toLocaleString('tr-TR')}`
                : `-₺${totalGider.toLocaleString('tr-TR')}`
              }
            </Text>
          </View>
        )}
      </View>

      {loading
        ? <View style={s.center}><ActivityIndicator size="large" color={Colors.blue} /></View>
        : <FlatList
            data={filtered}
            keyExtractor={item => String(item.id)}
            renderItem={({ item }) => <TransactionItem item={item} onDelete={onDelete} />}
            ItemSeparatorComponent={() => <View style={s.sep} />}
            contentContainerStyle={{ paddingBottom: 24 }}
            showsVerticalScrollIndicator={false}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={Colors.blue} />}
            ListEmptyComponent={
              <View style={s.empty}>
                <Text style={s.emptyIco}>{search ? '🔎' : '📭'}</Text>
                <Text style={s.emptyTxt}>{search ? 'Sonuç bulunamadı' : 'Henüz işlem yok'}</Text>
              </View>
            }
          />
      }
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container:      { flex: 1, backgroundColor: Colors.bg },
  center:         { flex: 1, alignItems: 'center', justifyContent: 'center' },
  header:         { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 16, paddingTop: 8, paddingBottom: 4 },
  title:          { fontSize: 24, fontWeight: '800', color: Colors.textPrimary },
  count:          { fontSize: 13, color: Colors.textSecondary },
  searchRow:      { paddingHorizontal: 16, paddingVertical: 8 },
  searchBox:      { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.bgInput, borderRadius: 12, paddingHorizontal: 12, borderWidth: 1, borderColor: Colors.border, gap: 8 },
  searchIco:      { fontSize: 16 },
  searchInput:    { flex: 1, paddingVertical: 12, fontSize: 15, color: Colors.textPrimary },
  clearBtn:       { fontSize: 14, color: Colors.textMuted, padding: 4 },
  filterRow:      { flexDirection: 'row', paddingHorizontal: 16, gap: 8, marginBottom: 8, alignItems: 'center' },
  filterBtn:      { paddingHorizontal: 16, paddingVertical: 7, borderRadius: 20, backgroundColor: Colors.bgInput, borderWidth: 1, borderColor: Colors.border },
  filterActive:   { backgroundColor: Colors.blue, borderColor: Colors.blue },
  filterTxt:      { fontSize: 13, fontWeight: '600', color: Colors.textSecondary },
  filterTxtActive:{ color: Colors.white },
  totalBadge:     { marginLeft: 'auto' as any, backgroundColor: Colors.bgCard, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 4, borderWidth: 1, borderColor: Colors.border },
  totalTxt:       { fontSize: 13, fontWeight: '700', color: Colors.textPrimary },
  sep:            { height: 1, backgroundColor: Colors.border, marginHorizontal: 14 },
  empty:          { alignItems: 'center', paddingVertical: 48 },
  emptyIco:       { fontSize: 40, marginBottom: 8 },
  emptyTxt:       { fontSize: 14, color: Colors.textSecondary },
});
