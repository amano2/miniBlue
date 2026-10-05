import { create } from 'zustand';
import { User, UserRole, AuthTokens } from '../types';

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (tokens: AuthTokens, user: User) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
}

const STORAGE_KEY_AUTH = 'miniblue_auth';

// Load stored session if available
const getInitialState = (): { user: User | null; tokens: AuthTokens | null } => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_AUTH);
    if (raw) {
      return JSON.parse(raw);
    }
  } catch (e) {
    console.error('Failed to load auth from storage', e);
  }
  return { user: null, tokens: null };
};

const initial = getInitialState();

export const useAuthStore = create<AuthState>((set) => ({
  user: initial.user,
  tokens: initial.tokens,
  isAuthenticated: Boolean(initial.tokens?.access_token),
  isLoading: false,
  login: (tokens, user) => {
    try {
      localStorage.setItem(STORAGE_KEY_AUTH, JSON.stringify({ tokens, user }));
    } catch (e) {
      console.error(e);
    }
    set({ tokens, user, isAuthenticated: true, isLoading: false });
  },
  logout: () => {
    try {
      localStorage.removeItem(STORAGE_KEY_AUTH);
    } catch (e) {
      console.error(e);
    }
    set({ tokens: null, user: null, isAuthenticated: false, isLoading: false });
  },
  updateUser: (updated) => {
    set((state) => {
      if (!state.user) return state;
      const newUser = { ...state.user, ...updated };
      if (state.tokens) {
        localStorage.setItem(STORAGE_KEY_AUTH, JSON.stringify({ tokens: state.tokens, user: newUser }));
      }
      return { user: newUser };
    });
  },
}));

interface UIState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  activeSessionId: string;
  setActiveSessionId: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarCollapsed: false,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  activeSessionId: 'default-session',
  setActiveSessionId: (id) => set({ activeSessionId: id }),
}));
