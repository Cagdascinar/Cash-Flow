import { Modal, Pressable, Animated, Dimensions, StyleSheet } from 'react-native';
import { useEffect, useRef, useState } from 'react';
import { useUIStore } from '../stores/uiStore';
import { MoreMenuContent } from './MoreMenuContent';
import { C } from '../constants/Colors';

const SCREEN_W = Dimensions.get('window').width;
const DRAWER_W = Math.min(SCREEN_W * 0.82, 340);

export function MoreDrawer() {
  const moreMenuOpen  = useUIStore(s => s.moreMenuOpen);
  const closeMoreMenu = useUIStore(s => s.closeMoreMenu);
  const [mounted, setMounted] = useState(false);
  const translateX = useRef(new Animated.Value(-DRAWER_W)).current;
  const backdrop    = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (moreMenuOpen) {
      setMounted(true);
      Animated.parallel([
        Animated.timing(translateX, { toValue: 0, duration: 260, useNativeDriver: true }),
        Animated.timing(backdrop,   { toValue: 1, duration: 260, useNativeDriver: true }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(translateX, { toValue: -DRAWER_W, duration: 220, useNativeDriver: true }),
        Animated.timing(backdrop,   { toValue: 0, duration: 220, useNativeDriver: true }),
      ]).start(() => setMounted(false));
    }
  }, [moreMenuOpen]);

  if (!mounted) return null;

  return (
    <Modal visible transparent animationType="none" statusBarTranslucent onRequestClose={closeMoreMenu}>
      <Animated.View style={[StyleSheet.absoluteFill, { backgroundColor: '#000', opacity: backdrop }]}>
        <Pressable style={StyleSheet.absoluteFill} onPress={closeMoreMenu} />
      </Animated.View>
      <Animated.View style={[s.panel, { width: DRAWER_W, transform: [{ translateX }] }]}>
        <MoreMenuContent onNavigate={closeMoreMenu} />
      </Animated.View>
    </Modal>
  );
}

const s = StyleSheet.create({
  panel: {
    position: 'absolute', top: 0, left: 0, bottom: 0,
    backgroundColor: C.bg,
    shadowColor: '#000', shadowOffset: { width: 2, height: 0 }, shadowOpacity: 0.35, shadowRadius: 12,
    elevation: 16,
  },
});
