import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface Profile {
  id: number;
  name: string;
  type: string;
  avatar?: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  is_premium: boolean;
  active_profile_id: number;
  profiles: Profile[];
}

interface AuthState {
  user: User | null;
  activeProfile: Profile | null;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  setActiveProfile: (profile: Profile) => void;
  logout: () => void;
  hydrate: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  activeProfile: null,
  isLoading: true,

  setUser: (user) => {
    const activeProfile = user?.profiles?.find(
      (p) => p.id === user.active_profile_id
    ) ?? user?.profiles?.[0] ?? null;
    set({ user, activeProfile });
    if (user) {
      AsyncStorage.setItem('cached_user', JSON.stringify(user));
    }
  },

  setActiveProfile: (profile) => set({ activeProfile: profile }),

  logout: () => {
    AsyncStorage.removeItem('cached_user');
    set({ user: null, activeProfile: null });
  },

  hydrate: async () => {
    try {
      const cached = await AsyncStorage.getItem('cached_user');
      if (cached) {
        const user = JSON.parse(cached) as User;
        const activeProfile = user.profiles?.find(
          (p) => p.id === user.active_profile_id
        ) ?? user.profiles?.[0] ?? null;
        set({ user, activeProfile });
      }
    } finally {
      set({ isLoading: false });
    }
  },
}));
