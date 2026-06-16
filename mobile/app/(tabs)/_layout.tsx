import { Tabs } from 'expo-router';
import { View, Text, StyleSheet, Platform } from 'react-native';
import { C } from '../../constants/Colors';
import { useUIStore } from '../../stores/uiStore';

function Icon({ emoji, label, focused }: { emoji: string; label: string; focused: boolean }) {
  return (
    <View style={ic.wrap}>
      <Text style={[ic.emoji, focused && ic.emojiFocused]}>{emoji}</Text>
      <Text style={[ic.label, focused && ic.labelFocused]}>{label}</Text>
    </View>
  );
}
const ic = StyleSheet.create({
  wrap:         { alignItems: 'center', gap: 2 },
  emoji:        { fontSize: 22, opacity: 0.4 },
  emojiFocused: { opacity: 1 },
  label:        { fontSize: 10, color: C.muted },
  labelFocused: { color: C.blue, fontWeight: '600' },
});

export default function TabsLayout() {
  const openMoreMenu = useUIStore(s => s.openMoreMenu);

  return (
    <Tabs screenOptions={{
      headerShown: false,
      tabBarStyle: {
        backgroundColor: C.tab,
        borderTopColor: C.border,
        borderTopWidth: 1,
        height: Platform.OS === 'ios' ? 88 : 64,
        paddingBottom: Platform.OS === 'ios' ? 28 : 8,
        paddingTop: 8,
      },
      tabBarShowLabel: false,
    }}>
      <Tabs.Screen name="index"  options={{ tabBarIcon: ({ focused }) => <Icon emoji="📊" label="Özet"    focused={focused} /> }} />
      <Tabs.Screen name="ledger" options={{ tabBarIcon: ({ focused }) => <Icon emoji="📋" label="İşlemler" focused={focused} /> }} />
      <Tabs.Screen name="add"    options={{
        tabBarIcon: () => (
          <View style={{ width: 52, height: 52, borderRadius: 26, backgroundColor: C.blue, alignItems: 'center', justifyContent: 'center', shadowColor: C.blue, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.5, shadowRadius: 8, elevation: 8 }}>
            <Text style={{ fontSize: 28, color: C.white, lineHeight: 32, fontWeight: '300' }}>+</Text>
          </View>
        ),
      }} />
      <Tabs.Screen name="budget" options={{ tabBarIcon: ({ focused }) => <Icon emoji="🎯" label="Bütçe"    focused={focused} /> }} />
      <Tabs.Screen
        name="more"
        options={{ tabBarIcon: ({ focused }) => <Icon emoji="☰"  label="Daha"     focused={focused} /> }}
        listeners={{
          tabPress: (e) => {
            e.preventDefault();
            openMoreMenu();
          },
        }}
      />
    </Tabs>
  );
}
