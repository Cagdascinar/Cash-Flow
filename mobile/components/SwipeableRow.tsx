import {
  View, Text, StyleSheet, TouchableOpacity,
  Animated, PanResponder, ViewStyle,
} from 'react-native';
import { useRef, ReactNode } from 'react';

export interface SwipeAction {
  label: string;
  icon: string;
  color: string;
  onPress: () => void;
}

const BTN_W = 72;
const OPEN_THRESHOLD = -50;

export function SwipeableRow({ children, actions, style }: {
  children: ReactNode;
  actions: SwipeAction[];
  style?: ViewStyle;
}) {
  const totalW = actions.length * BTN_W;
  const x = useRef(new Animated.Value(0)).current;
  const isOpen = useRef(false);

  function snapTo(toValue: number) {
    isOpen.current = toValue !== 0;
    Animated.spring(x, { toValue, useNativeDriver: true, overshootClamping: true }).start();
  }

  const pan = useRef(PanResponder.create({
    // Capture phase: steal clearly-horizontal gestures BEFORE children (TouchableOpacity) can claim them.
    // Higher threshold so normal taps with slight drift still reach the child.
    onMoveShouldSetPanResponderCapture: (_, g) =>
      Math.abs(g.dx) > 12 && Math.abs(g.dx) > Math.abs(g.dy) * 2,

    // Bubble phase: also claim if the child didn't take it yet (lower threshold).
    onMoveShouldSetPanResponder: (_, g) =>
      Math.abs(g.dx) > 8 && Math.abs(g.dx) > Math.abs(g.dy) * 1.5,

    onPanResponderMove: (_, g) => {
      const base = isOpen.current ? -totalW : 0;
      x.setValue(Math.min(0, Math.max(-totalW, base + g.dx)));
    },
    onPanResponderRelease: (_, g) => {
      if (isOpen.current) {
        snapTo(g.dx > 30 ? 0 : -totalW);
      } else {
        snapTo(g.dx < OPEN_THRESHOLD ? -totalW : 0);
      }
    },
    onPanResponderTerminate: () => {
      snapTo(0);
    },
  })).current;

  return (
    <View style={[sr.wrap, style]}>
      <View style={[sr.actions, { width: totalW }]}>
        {actions.map((a, i) => (
          <TouchableOpacity
            key={i}
            style={[sr.btn, { backgroundColor: a.color }]}
            onPress={() => { snapTo(0); a.onPress(); }}
            activeOpacity={0.8}
          >
            <Text style={sr.icon}>{a.icon}</Text>
            <Text style={sr.label}>{a.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <Animated.View style={{ transform: [{ translateX: x }] }} {...pan.panHandlers}>
        {children}
      </Animated.View>
    </View>
  );
}

const sr = StyleSheet.create({
  wrap:    { overflow: 'hidden' },
  actions: { position: 'absolute', right: 0, top: 0, bottom: 0, flexDirection: 'row' },
  btn:     { width: BTN_W, alignItems: 'center', justifyContent: 'center', gap: 4 },
  icon:    { fontSize: 18 },
  label:   { fontSize: 11, fontWeight: '700', color: '#fff' },
});
