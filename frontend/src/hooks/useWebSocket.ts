import { useEffect, useRef } from "react";
import { useAuthStore } from "../store/authStore";
import { usePlansStore } from "../store/plansStore";
import { useTasksStore } from "../store/tasksStore";
import { api } from "../lib/api";
import type { Plan } from "../store/plansStore";
import type { AgentTask } from "../store/tasksStore";

const WS_URL = import.meta.env.VITE_WS_URL || `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;

type WsEvent =
  | { type: "new_plan"; plan_id: string }
  | { type: "plan_approved"; plan_id: string }
  | { type: "plan_executing"; plan_id: string }
  | { type: "plan_completed"; plan_id: string }
  | { type: "plan_pending_copy_approval"; plan_id: string; next_step: number }
  | { type: "plan_awaiting_creative_choice"; plan_id: string; next_step: number }
  | { type: "plan_creative_chosen"; plan_id: string; creative_type: string }
  | { type: "plan_awaiting_funnel_choice"; plan_id: string; next_step: number }
  | { type: "plan_funnel_chosen"; plan_id: string; funnel_type: string }
  | { type: "plan_pending_ads_approval"; plan_id: string; next_step: number }
  | { type: "plan_research_view"; plan_id: string }
  | { type: "task_update"; task_id: string; status: AgentTask["status"]; output?: Record<string, unknown>; agent?: string };

export function useWebSocket() {
  const { user } = useAuthStore();
  const { fetchPlans, upsertPlan } = usePlansStore();
  const { upsertTask, fetchTasks } = useTasksStore();
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!user) return;

    const ws = new WebSocket(`${WS_URL}/ws/${user.id}`);
    wsRef.current = ws;

    ws.onmessage = async (event: MessageEvent) => {
      const data = JSON.parse(event.data as string) as WsEvent;

      if (data.type === "new_plan" && data.plan_id) {
        try {
          const plan = await api.get<Plan>(`/plans/${data.plan_id}`);
          upsertPlan(plan);
        } catch {
          await fetchPlans();
        }
      }

      if (
        (data.type === "plan_approved" ||
          data.type === "plan_executing" ||
          data.type === "plan_completed" ||
          data.type === "plan_pending_copy_approval" ||
          data.type === "plan_awaiting_creative_choice" ||
          data.type === "plan_creative_chosen" ||
          data.type === "plan_awaiting_funnel_choice" ||
          data.type === "plan_funnel_chosen" ||
          data.type === "plan_pending_ads_approval" ||
          data.type === "plan_research_view") &&
        data.plan_id
      ) {
        try {
          const plan = await api.get<Plan>(`/plans/${data.plan_id}`);
          upsertPlan(plan);
          if (
            data.type === "plan_executing" ||
            data.type === "plan_completed" ||
            data.type === "plan_pending_ads_approval"
          ) {
            await fetchTasks(data.plan_id);
          }
        } catch {
          await fetchPlans();
        }
      }

      if (data.type === "task_update" && data.task_id) {
        // Fetch the full task list to get the plan_id and all fields
        // We optimistically update with the info we have from the WS event
        // The full task will come from the next fetchTasks call
        const allTasks = useTasksStore.getState().tasksByPlan;
        for (const tasks of Object.values(allTasks)) {
          const existing = tasks.find((t) => t.id === data.task_id);
          if (existing) {
            upsertTask({
              ...existing,
              status: data.status,
              ...(data.output ? { output: data.output } : {}),
            });
            break;
          }
        }
        // If not found locally, refresh all task lists for executing plans
        if (!Object.values(allTasks).flat().find((t) => t.id === data.task_id)) {
          const plans = usePlansStore.getState().plans;
          const executingPlan = plans.find((p) => p.status === "executing");
          if (executingPlan) await fetchTasks(executingPlan.id);
        }
      }
    };

    return () => {
      ws.close();
    };
  }, [user?.id]);
}
