import { create } from 'zustand';

interface UIState {
  moreMenuOpen: boolean;
  openMoreMenu: () => void;
  closeMoreMenu: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  moreMenuOpen: false,
  openMoreMenu: () => set({ moreMenuOpen: true }),
  closeMoreMenu: () => set({ moreMenuOpen: false }),
}));
