import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { C } from '../constants/Colors';

const AVATAR_COLORS = [
  '#007aff', '#0ecb81', '#f0b90b', '#f6465d', '#9b59b6', '#1abc9c',
];

function greeting() {
  const h = new Date().getHours();
  if (h < 6)  return 'İyi geceler';
  if (h < 12) return 'Günaydın';
  if (h < 18) return 'İyi günler';
  return 'İyi akşamlar';
}

function todayStr() {
  return new Date().toLocaleDateString('tr-TR', {
    weekday: 'long', day: 'numeric', month: 'long',
  });
}

function avatarColor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + hash * 31;
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

interface Props {
  username: string;
  profileName?: string;
  profileType?: string;
  isPremium?: boolean;
  quote?: string;
  onAvatarPress?: () => void;
}

export function WelcomeHero({ username, profileName, profileType, isPremium, quote, onAvatarPress }: Props) {
  const initial = (username?.[0] ?? '?').toUpperCase();
  const color   = avatarColor(username ?? '');
  const greet   = greeting();
  const day     = todayStr();

  return (
    <View style={s.container}>
      <View style={s.header}>
        {/* Sol üst köşe — profil avatarı */}
        <TouchableOpacity onPress={onAvatarPress} activeOpacity={0.8} style={s.avatarTouch}>
          <View style={[s.avatar, { backgroundColor: color }]}>
            <Text style={s.initial}>{initial}</Text>
          </View>
          {isPremium && (
            <View style={s.crown}>
              <Text style={{ fontSize: 9 }}>✨</Text>
            </View>
          )}
          <View style={s.onlineDot} />
        </TouchableOpacity>

        {/* Selamlama metni */}
        <View style={s.textWrap}>
          <Text style={s.greet}>{greet}</Text>
          <Text style={s.name} numberOfLines={1}>{username} 👋</Text>
        </View>

        {/* Profil chip — sağ üst */}
        {profileName && (
          <TouchableOpacity onPress={onAvatarPress} activeOpacity={0.7}
            style={[s.chip, profileType === 'sirket' && s.chipBiz]}>
            <Text style={[s.chipTxt, profileType === 'sirket' && s.chipTxtBiz]}>
              {profileType === 'sirket' ? '🏢' : '👤'} {profileName}
            </Text>
          </TouchableOpacity>
        )}
      </View>

      <Text style={s.date}>{day}</Text>

      {quote && (
        <View style={s.quoteBox}>
          <Text style={s.quoteText}>"{quote}"</Text>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container:   { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 4 },
  header:      { flexDirection: 'row', alignItems: 'center', gap: 12 },
  avatarTouch: { position: 'relative' },
  avatar:      {
    width: 54, height: 54, borderRadius: 27,
    alignItems: 'center', justifyContent: 'center',
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3, shadowRadius: 8, elevation: 6,
  },
  initial:     { fontSize: 22, fontWeight: '900', color: '#fff' },
  crown:       {
    position: 'absolute', top: -3, right: -3,
    backgroundColor: '#1a1d23', borderRadius: 9,
    width: 18, height: 18, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: C.border,
  },
  onlineDot:   {
    position: 'absolute', bottom: 2, right: 2,
    width: 13, height: 13, borderRadius: 7,
    backgroundColor: '#0ecb81', borderWidth: 2, borderColor: C.bg,
  },
  textWrap:    { flex: 1 },
  greet:       { fontSize: 13, color: C.txt2, fontWeight: '500' },
  name:        { fontSize: 21, fontWeight: '800', color: C.txt, letterSpacing: -0.4, marginTop: 1 },
  chip:        {
    backgroundColor: C.card, borderRadius: 20,
    paddingHorizontal: 10, paddingVertical: 6,
    borderWidth: 1, borderColor: C.border, maxWidth: 130,
  },
  chipBiz:     { backgroundColor: 'rgba(0,122,255,0.12)', borderColor: 'rgba(0,122,255,0.3)' },
  chipTxt:     { fontSize: 12, fontWeight: '600', color: C.txt2 },
  chipTxtBiz:  { color: C.blue },
  date:        { fontSize: 12, color: C.muted, marginTop: 8, fontWeight: '500' },
  quoteBox:    { marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: C.border },
  quoteText:   { fontSize: 12, color: C.txt2, fontStyle: 'italic', lineHeight: 18 },
});
