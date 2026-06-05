import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface Profile {
  id: number; name: string; type: string; avatar?: string;
}
export interface User {
  id: number; username: string; email: string;
  is_premium: boolean; active_profile_id: number;
  profiles: Profile[];
}

interface AuthState {
  user:          User | null;
  activeProfile: Profile | null;
  isLoading:     boolean;
  setUser:           (u: User | null)  => void;
  setActiveProfile:  (p: Profile)      => void;
  logout:            ()                => void;
  hydrate:           ()                => Promise<void>;
  refreshUser:       ()                => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null, activeProfile: null, isLoading: true,

  setUser: (user) => {
    const ap = user?.profiles?.find((p) => p.id === user.active_profile_id)
            ?? user?.profiles?.[0] ?? null;
    set({ user, activeProfile: ap });
    if (user) AsyncStorage.setItem('cached_user', JSON.stringify(user));
    else      AsyncStorage.removeItem('cached_user');
  },

  setActiveProfile: (p) => set({ activeProfile: p }),

  logout: () => {
    AsyncStorage.multiRemove(['cached_user', 'mobile_auth_token']);
    set({ user: null, activeProfile: null });
  },

  hydrate: async () => {
    try {
      const [cached, token] = await Promise.all([
        AsyncStorage.getItem('cached_user'),
        AsyncStorage.getItem('mobile_auth_token'),
      ]);
      if (cached && token) {
        const u = JSON.parse(cached) as User;
        const ap = u.profiles?.find((p) => p.id === u.active_profile_id) ?? u.profiles?.[0] ?? null;
        set({ user: u, activeProfile: ap });
      }
    } finally {
      set({ isLoading: false });
    }
  },

  refreshUser: async () => {
    try {
      const { auth } = await import('../services/api');
      const u = await auth.me();
      const ap = u?.profiles?.find((p: Profile) => p.id === u.active_profile_id) ?? u?.profiles?.[0] ?? null;
      if (u) {
        AsyncStorage.setItem('cached_user', JSON.stringify(u));
        set({ user: u, activeProfile: ap });
      }
    } catch {}
  },
}));
