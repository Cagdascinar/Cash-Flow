import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { C } from '../constants/Colors';

const AVATAR_COLORS = [
  ['#007aff', '#0040ff'],
  ['#0ecb81', '#05a855'],
  ['#f0b90b', '#d48700'],
  ['#f6465d', '#c02040'],
  ['#9b59b6', '#6c3483'],
  ['#1abc9c', '#0e8c72'],
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

function avatarColor(name: string): [string, string] {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + hash * 31;
  return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
}

interface Props {
  username: string;
  profileName?: string;
  isPremium?: boolean;
  quote?: string;
  onAvatarPress?: () => void;
}

export function WelcomeHero({ username, profileName, isPremium, quote, onAvatarPress }: Props) {
  const initial = (username?.[0] ?? '?').toUpperCase();
  const [c1, c2] = avatarColor(username ?? '');
  const day = todayStr();
  const greet = greeting();

  return (
    <View style={s.container}>
      {/* Arka plan dekoratif daireler */}
      <View style={[s.blob, { backgroundColor: c1, opacity: 0.08, top: -20, right: -20, width: 140, height: 140, borderRadius: 70 }]} />
      <View style={[s.blob, { backgroundColor: c2, opacity: 0.05, top: 30, right: 60, width: 80, height: 80, borderRadius: 40 }]} />

      <View style={s.row}>
        {/* Avatar */}
        <TouchableOpacity onPress={onAvatarPress} activeOpacity={0.85}>
          <View style={[s.avatarWrap, { shadowColor: c1 }]}>
            <View style={[s.avatarBg, { backgroundColor: c1 }]}>
              <Text style={s.initial}>{initial}</Text>
            </View>
            {isPremium && (
              <View style={s.proCrown}>
                <Text style={{ fontSize: 10 }}>✨</Text>
              </View>
            )}
          </View>
        </TouchableOpacity>

        {/* Metin */}
        <View style={{ flex: 1, paddingLeft: 14 }}>
          <Text style={s.greetText}>{greet},</Text>
          <Text style={s.nameText}>{username} 👋</Text>
          {profileName && (
            <View style={s.profileChip}>
              <Text style={s.profileChipTxt}>{profileName}</Text>
            </View>
          )}
        </View>
      </View>

      <Text style={s.dateText}>{day}</Text>

      {quote && (
        <View style={s.quoteBox}>
          <Text style={s.quoteText}>"{quote}"</Text>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container:     { marginHorizontal: 16, marginTop: 8, marginBottom: 4, backgroundColor: C.card, borderRadius: 20, padding: 18, borderWidth: 1, borderColor: C.border, overflow: 'hidden', position: 'relative' },
  blob:          { position: 'absolute' },
  row:           { flexDirection: 'row', alignItems: 'center' },
  avatarWrap:    { shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.4, shadowRadius: 12, elevation: 8 },
  avatarBg:      { width: 64, height: 64, borderRadius: 32, alignItems: 'center', justifyContent: 'center' },
  initial:       { fontSize: 28, fontWeight: '900', color: '#fff' },
  proCrown:      { position: 'absolute', top: -4, right: -4, backgroundColor: C.card, borderRadius: 10, width: 20, height: 20, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: C.border },
  greetText:     { fontSize: 14, color: C.txt2, fontWeight: '500' },
  nameText:      { fontSize: 24, fontWeight: '800', color: C.txt, marginTop: 2, letterSpacing: -0.5 },
  profileChip:   { marginTop: 5, alignSelf: 'flex-start', backgroundColor: C.input, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3, borderWidth: 1, borderColor: C.border },
  profileChipTxt:{ fontSize: 12, color: C.txt2, fontWeight: '600' },
  dateText:      { fontSize: 12, color: C.muted, marginTop: 12, fontWeight: '500' },
  quoteBox:      { marginTop: 10, paddingTop: 10, borderTopWidth: 1, borderTopColor: C.border },
  quoteText:     { fontSize: 13, color: C.txt2, fontStyle: 'italic', lineHeight: 18 },
});
