import { create } from "zustand";
import { api } from "../lib/api";
import { useClientStore } from "./clientStore";

export type BusinessType = "saas" | "ecommerce" | "services" | "app" | "local";
export type PlanTier = "trial" | "starter" | "growth" | "agency";
export type TeamRole = "owner" | "admin" | "member" | "viewer";

interface User {
  id: string;
  email: string;
  full_name: string | null;
  phone: string | null;
  business_type: BusinessType | null;
  plan: PlanTier;
  role: TeamRole;
  is_founder: boolean;
  is_superadmin: boolean;
  active_campaigns_limit: number;
  subscription_status: string | null;
  subscription_current_period_end: string | null;
  stripe_customer_id?: string | null;
  created_at: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
  phone?: string;
  business_type?: BusinessType;
  ref_code?: string;
}

export interface FeaturesInfo {
  plan: string;
  research_only: boolean;
  features: string[];
  limits: Record<string, number>;
  scans_remaining: number;
  scans_per_month: number;
  scans_reset_at: string | null;
  is_founder: boolean;
  is_superadmin: boolean;
}

interface AuthState {
  user: User | null;
  token: string | null;
  features: FeaturesInfo | null;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  fetchFeatures: () => Promise<void>;
  hasFeature: (f: string) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: localStorage.getItem("token"),
  features: null,

  login: async (email, password) => {
    const { access_token } = await api.post<{ access_token: string }>("/auth/login", {
      email,
      password,
    });
    localStorage.setItem("token", access_token);
    set({ token: access_token });
    const user = await api.get<User>("/auth/me");
    set({ user });
    await get().fetchFeatures();
    await useClientStore.getState().fetchClientAccounts();
  },

  register: async (payload) => {
    const { access_token } = await api.post<{ access_token: string }>("/auth/register", payload);
    localStorage.setItem("token", access_token);
    set({ token: access_token });
    const user = await api.get<User>("/auth/me");
    set({ user });
    await get().fetchFeatures();
    await useClientStore.getState().fetchClientAccounts();
  },

  logout: () => {
    localStorage.removeItem("token");
    useClientStore.getState().reset();
    set({ user: null, token: null, features: null });
  },

  fetchMe: async () => {
    try {
      const user = await api.get<User>("/auth/me");
      set({ user });
      await get().fetchFeatures();
      await useClientStore.getState().fetchClientAccounts();
    } catch {
      localStorage.removeItem("token");
      set({ user: null, token: null, features: null });
    }
  },

  fetchFeatures: async () => {
    try {
      const features = await api.get<FeaturesInfo>("/auth/me/features");
      set({ features });
    } catch {
      set({ features: null });
    }
  },

  hasFeature: (f: string) => {
    const features = get().features;
    return features ? features.features.includes(f) : true; // optimista hasta cargar
  },
}));
