import Swipeable from 'react-native-gesture-handler/Swipeable';
import { View, Text, TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';
import { ReactNode, useRef } from 'react';

export interface SwipeAction {
  label: string;
  icon: string;
  color: string;
  onPress: () => void;
}

const BTN_W = 76;

// Aynı anda tek satır açık kalsın: açılan satır, daha önce açık olanı kapatır.
const openRowRef: { current: Swipeable | null } = { current: null };

export function SwipeableRow({ children, actions, style }: {
  children: ReactNode;
  actions: SwipeAction[];
  style?: ViewStyle;
}) {
  const ref = useRef<Swipeable>(null);

  function handleWillOpen() {
    if (openRowRef.current && openRowRef.current !== ref.current) {
      openRowRef.current.close();
    }
    openRowRef.current = ref.current;
  }

  function handleClose() {
    if (openRowRef.current === ref.current) openRowRef.current = null;
  }

  function RightActions() {
    return (
      <View style={{ flexDirection: 'row', width: actions.length * BTN_W }}>
        {actions.map((a, i) => (
          <TouchableOpacity
            key={i}
            style={[sr.btn, { backgroundColor: a.color }]}
            onPress={() => { ref.current?.close(); a.onPress(); }}
            activeOpacity={0.8}
          >
            <Text style={sr.icon}>{a.icon}</Text>
            <Text style={sr.label}>{a.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    );
  }

  return (
    <Swipeable
      ref={ref}
      renderRightActions={() => <RightActions />}
      overshootRight={false}
      friction={2}
      rightThreshold={40}
      containerStyle={style}
      onSwipeableWillOpen={handleWillOpen}
      onSwipeableClose={handleClose}
    >
      {children}
    </Swipeable>
  );
}

const sr = StyleSheet.create({
  btn:   { width: BTN_W, alignItems: 'center', justifyContent: 'center', gap: 5 },
  icon:  { fontSize: 20 },
  label: { fontSize: 11, fontWeight: '700', color: '#fff' },
});
