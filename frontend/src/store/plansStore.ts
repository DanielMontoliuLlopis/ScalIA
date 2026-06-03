import { create } from "zustand";
import { api } from "../lib/api";

export interface PlanStep {
  order: number;
  agent: string;
  action: string;
  description: string;
}

export interface CreativeAsset {
  url?: string | null;
  thumbnail_url?: string | null;
  media_type?: string | null;
  post_id?: string | null;
  width?: number | null;
  height?: number | null;
}

export interface AngleTested {
  angle: string;
  hook?: string;
  image_url?: string | null;
  budget_share?: number | null;
  ctr?: number | null;
  cpl?: number | null;
  roas?: number | null;
  status?: string;
}

export interface Plan {
  id: string;
  user_id: string;
  title: string;
  description: string;
  steps: PlanStep[];
  status: "pending_approval" | "approved" | "rejected" | "executing" | "awaiting_creative_choice" | "pending_copy_approval" | "awaiting_funnel_choice" | "pending_ads_approval" | "research_view" | "done";
  feedback: string | null;
  funnel_type: string | null;
  sale_type: string | null;
  redirect_url: string | null;
  creative_type: string | null;
  creative_a: CreativeAsset | null;
  creative_b: CreativeAsset | null;
  ab_testing: boolean;
  ab_mode: string;
  num_angles: number | null;
  angles_tested: AngleTested[] | null;
  research_export: boolean;
  export_url: string | null;
  precio_base: number | null;
  tipo_oferta: string | null;
  urgencia: string | null;
  garantia: string | null;
  transformacion: string | null;
  created_at: string;
  updated_at: string;
}

interface PlansState {
  plans: Plan[];
  fetchPlans: () => Promise<void>;
  approvePlan: (id: string) => Promise<void>;
  rejectPlan: (id: string, feedback: string) => Promise<void>;
  upsertPlan: (plan: Plan) => void;
}

export const usePlansStore = create<PlansState>((set, get) => ({
  plans: [],

  fetchPlans: async () => {
    const plans = await api.get<Plan[]>("/plans");
    set({ plans });
  },

  approvePlan: async (id) => {
    const updated = await api.post<Plan>(`/plans/${id}/approve`);
    set({ plans: get().plans.map((p) => (p.id === id ? updated : p)) });
  },

  rejectPlan: async (id, feedback) => {
    const updated = await api.post<Plan>(`/plans/${id}/reject`, { feedback });
    set({ plans: get().plans.map((p) => (p.id === id ? updated : p)) });
  },

  upsertPlan: (plan) => {
    const existing = get().plans.find((p) => p.id === plan.id);
    if (existing) {
      set({ plans: get().plans.map((p) => (p.id === plan.id ? plan : p)) });
    } else {
      set({ plans: [plan, ...get().plans] });
    }
  },
}));
