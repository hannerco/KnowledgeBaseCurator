import { create } from "zustand";
import { authService } from "../services/auth.service";
import type {
  LoginPayload,
  RegisterPayload,
  UserProfile,
} from "../types/auth.types";

interface AuthState {
  token: string;
  user: UserProfile | null;
  loading: boolean;
  error: string | null;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<string>;
  logout: () => void;
  loadSession: () => Promise<void>;
}

const AUTH_TOKEN_KEY = "authToken";

export const useAuthStore = create<AuthState>((set) => ({
  token: "",
  user: null,
  loading: false,
  error: null,

  login: async (payload: LoginPayload) => {
    set({ loading: true, error: null });
    try {
      const loginResponse = await authService.login(payload);
      const token = loginResponse.access_token;
      set({ token });
      if (typeof window !== "undefined") {
        localStorage.setItem(AUTH_TOKEN_KEY, token);
      }
      const profile = await authService.me(token);
      set({ user: profile });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Error en el login";
      set({ error: message });
      throw new Error(message);
    } finally {
      set({ loading: false });
    }
  },

  register: async (payload: RegisterPayload) => {
    set({ loading: true, error: null });
    try {
      const response = await authService.register(payload);
      return response.message;
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Error en el registro";
      set({ error: message });
      throw new Error(message);
    } finally {
      set({ loading: false });
    }
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(AUTH_TOKEN_KEY);
    }
    set({ token: "", user: null, error: null });
  },

  loadSession: async () => {
    if (typeof window === "undefined") return;
    const token = localStorage.getItem(AUTH_TOKEN_KEY);
    if (!token) return;
    set({ loading: true, error: null });
    try {
      const profile = await authService.me(token);
      set({ token, user: profile });
    } catch {
      set({ token: "", user: null });
      localStorage.removeItem(AUTH_TOKEN_KEY);
    } finally {
      set({ loading: false });
    }
  },
}));
