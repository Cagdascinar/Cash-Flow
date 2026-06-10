import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { C } from '../constants/Colors';
import { BASE_URL } from '../services/api';

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
  avatar?: string;
  isPremium?: boolean;
  quote?: string;
  onAvatarPress?: () => void;
}

export function WelcomeHero({ username, profileName, profileType, avatar, isPremium, quote, onAvatarPress }: Props) {
  const initial   = (username?.[0] ?? '?').toUpperCase();
  const color     = avatarColor(username ?? '');
  const greet     = greeting();
  const day       = todayStr();
  const avatarUri = avatar
    ? (avatar.startsWith('http') ? avatar : `${BASE_URL}${avatar}`)
    : null;

  return (
    <View style={s.container}>
      <View style={s.header}>
        {/* Sol üst köşe — büyük kare avatar */}
        <TouchableOpacity onPress={onAvatarPress} activeOpacity={0.8} style={s.avatarTouch}>
          <View style={[s.avatar, { backgroundColor: color }]}>
            {avatarUri
              ? <Image source={{ uri: avatarUri }} style={s.avatarImg} />
              : <Text style={s.initial}>{initial}</Text>
            }
          </View>
          {isPremium && (
            <View style={s.crown}><Text style={{ fontSize: 10 }}>✨</Text></View>
          )}
          <View style={s.onlineDot} />
        </TouchableOpacity>

        {/* Selamlama + profil chip */}
        <View style={s.textWrap}>
          <Text style={s.greet}>{greet}</Text>
          <Text style={s.name} numberOfLines={1}>{username} 👋</Text>
          <Text style={s.date}>{day}</Text>
          {profileName && (
            <TouchableOpacity onPress={onAvatarPress} activeOpacity={0.7}
              style={[s.chip, profileType === 'sirket' && s.chipBiz]}>
              <Text style={[s.chipTxt, profileType === 'sirket' && s.chipTxtBiz]}>
                {profileType === 'sirket' ? '🏢' : '👤'} {profileName}
              </Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {quote && (
        <View style={s.quoteBox}>
          <Text style={s.quoteText}>"{quote}"</Text>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container:   { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 8 },
  header:      { flexDirection: 'row', alignItems: 'flex-start', gap: 14 },
  avatarTouch: { position: 'relative' },
  avatar:      {
    width: 90, height: 90, borderRadius: 22,
    alignItems: 'center', justifyContent: 'center',
    shadowColor: '#000', shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35, shadowRadius: 12, elevation: 8,
  },
  avatarImg:   { width: 90, height: 90, borderRadius: 22 },
  initial:     { fontSize: 38, fontWeight: '900', color: '#fff' },
  crown:       {
    position: 'absolute', top: -5, right: -5,
    backgroundColor: '#1a1d23', borderRadius: 11,
    width: 22, height: 22, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: C.border,
  },
  onlineDot:   {
    position: 'absolute', bottom: 4, right: 4,
    width: 14, height: 14, borderRadius: 7,
    backgroundColor: '#0ecb81', borderWidth: 2.5, borderColor: C.bg,
  },
  textWrap:    { flex: 1, paddingTop: 4 },
  greet:       { fontSize: 13, color: C.txt2, fontWeight: '500' },
  name:        { fontSize: 22, fontWeight: '800', color: C.txt, letterSpacing: -0.5, marginTop: 2 },
  date:        { fontSize: 12, color: C.muted, marginTop: 4, fontWeight: '500' },
  chip:        {
    marginTop: 8, alignSelf: 'flex-start',
    backgroundColor: C.card, borderRadius: 20,
    paddingHorizontal: 10, paddingVertical: 5,
    borderWidth: 1, borderColor: C.border,
  },
  chipBiz:     { backgroundColor: 'rgba(0,122,255,0.12)', borderColor: 'rgba(0,122,255,0.3)' },
  chipTxt:     { fontSize: 12, fontWeight: '600', color: C.txt2 },
  chipTxtBiz:  { color: C.blue },
  quoteBox:    { marginTop: 12, paddingTop: 10, borderTopWidth: 1, borderTopColor: C.border },
  quoteText:   { fontSize: 12, color: C.txt2, fontStyle: 'italic', lineHeight: 18 },
});
