import { create } from "zustand";
import { persist } from "zustand/middleware";
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

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: "",
      user: null,
      loading: false,
      error: null,

      login: async (payload: LoginPayload) => {
        set({ loading: true, error: null });
        try {
          const loginResponse = await authService.login(payload);
          const token = loginResponse.access_token;
          set({ token, user: null });
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
        set({ token: "", user: null, error: null });
      },

      loadSession: async () => {
        const token = get().token;
        if (!token) return;
        set({ loading: true, error: null });
        try {
          const profile = await authService.me(token);
          set({ user: profile });
        } catch {
          set({ token: "", user: null });
        } finally {
          set({ loading: false });
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ token: state.token }),
    }
  )
);
