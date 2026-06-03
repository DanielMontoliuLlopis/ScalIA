import { create } from "zustand";
import { closerApi } from "../lib/closerApi";

export interface CloserMe {
  id: string;
  full_name: string;
  email: string;
  commission_rate: number;
  referral_code: string;
  calendly_url: string | null;
  is_active: boolean;
}

interface CloserAuthState {
  closer: CloserMe | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
}

export const useCloserAuthStore = create<CloserAuthState>((set) => ({
  closer: null,
  token: localStorage.getItem("closer_token"),

  login: async (email, password) => {
    const { access_token } = await closerApi.post<{ access_token: string }>(
      "/closer-portal/login",
      { email, password }
    );
    localStorage.setItem("closer_token", access_token);
    set({ token: access_token });
    const closer = await closerApi.get<CloserMe>("/closer-portal/me");
    set({ closer });
  },

  logout: () => {
    localStorage.removeItem("closer_token");
    set({ closer: null, token: null });
  },

  fetchMe: async () => {
    try {
      const closer = await closerApi.get<CloserMe>("/closer-portal/me");
      set({ closer });
    } catch {
      localStorage.removeItem("closer_token");
      set({ closer: null, token: null });
    }
  },
}));
