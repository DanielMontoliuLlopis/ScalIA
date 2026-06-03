import { create } from "zustand";
import { api } from "../lib/api";

export interface AgentTask {
  id: string;
  plan_id: string;
  agent_name: string;
  tool_name: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | null;
  status: "pending" | "running" | "completed" | "failed";
  created_at: string;
  updated_at: string;
}

interface TasksState {
  tasksByPlan: Record<string, AgentTask[]>;
  fetchTasks: (planId: string) => Promise<void>;
  upsertTask: (task: AgentTask) => void;
}

export const useTasksStore = create<TasksState>((set, get) => ({
  tasksByPlan: {},

  fetchTasks: async (planId) => {
    const tasks = await api.get<AgentTask[]>(`/plans/${planId}/tasks`);
    set({ tasksByPlan: { ...get().tasksByPlan, [planId]: tasks } });
  },

  upsertTask: (task) => {
    const planId = task.plan_id;
    const existing = get().tasksByPlan[planId] ?? [];
    const idx = existing.findIndex((t) => t.id === task.id);
    const updated = idx >= 0
      ? existing.map((t) => (t.id === task.id ? task : t))
      : [...existing, task];
    set({ tasksByPlan: { ...get().tasksByPlan, [planId]: updated } });
  },
}));
