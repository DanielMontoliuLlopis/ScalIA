import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../lib/api";
import { usePlansStore } from "../store/plansStore";
import { useTasksStore } from "../store/tasksStore";
import { useWebSocket } from "../hooks/useWebSocket";
import { ApprovalCard } from "../components/approval/ApprovalCard";
import type { Plan } from "../store/plansStore";

export function PlanWorkspace() {
  const { planId } = useParams<{ planId: string }>();
  const { plans, upsertPlan } = usePlansStore();
  const { fetchTasks } = useTasksStore();
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useWebSocket();

  useEffect(() => {
    if (!planId) return;
    (async () => {
      try {
        const plan = await api.get<Plan>(`/plans/${planId}`);
        upsertPlan(plan);
        await fetchTasks(planId);
      } catch {
        setNotFound(true);
      } finally {
        setLoading(false);
      }
    })();
  }, [planId]);

  const plan = plans.find((p) => p.id === planId);

  return (
    <div className="flex-1 overflow-y-auto bg-transparent">
      <div className="max-w-2xl mx-auto px-6 py-8">
        <Link to="/campaigns" className="text-xs text-gray-500 hover:text-gray-800">
          ← Mis campañas
        </Link>
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-6 h-6 border-2 border-brand-400 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : notFound || !plan ? (
          <div className="text-center py-20 text-gray-400">
            <p className="text-lg font-medium text-gray-700">Campaña no encontrada</p>
            <Link to="/campaigns/new" className="text-sm text-brand-600 underline mt-2 inline-block">
              Crear una nueva
            </Link>
          </div>
        ) : (
          <div className="mt-3">
            <ApprovalCard plan={plan} />
          </div>
        )}
      </div>
    </div>
  );
}
