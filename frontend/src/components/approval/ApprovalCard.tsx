import { useState, useEffect } from "react";
import type { Plan } from "../../store/plansStore";
import { usePlansStore } from "../../store/plansStore";
import { useTasksStore } from "../../store/tasksStore";
import { AgentActivityFeed } from "../dashboard/AgentActivityFeed";
import { CopyApprovalPanel } from "./CopyApprovalPanel";
import { AdsApprovalPanel } from "./AdsApprovalPanel";
import { FunnelTypeSelector } from "../dashboard/FunnelTypeSelector";
import { CreativeChoiceSelector } from "../dashboard/CreativeChoiceSelector";
import { ResearchModeScreen } from "../../pages/ResearchModeScreen";
import { api } from "../../lib/api";

const STATUS_STYLES: Record<string, string> = {
  pending_approval: "border-yellow-400 bg-yellow-50",
  approved: "border-green-400 bg-green-50",
  rejected: "border-red-400 bg-red-50",
  executing: "border-blue-400 bg-blue-50",
  awaiting_creative_choice: "border-brand-500 bg-brand-50",
  pending_copy_approval: "border-brand-400 bg-brand-50",
  awaiting_funnel_choice: "border-brand-500 bg-brand-50",
  pending_ads_approval: "border-violet-400 bg-violet-50",
  research_view: "border-amber-400 bg-amber-50",
  done: "border-gray-300 bg-gray-50",
};

const STATUS_BADGE: Record<string, string> = {
  pending_approval: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  executing: "bg-blue-100 text-blue-800",
  awaiting_creative_choice: "bg-brand-100 text-brand-800",
  pending_copy_approval: "bg-brand-100 text-brand-800",
  awaiting_funnel_choice: "bg-brand-100 text-brand-800",
  pending_ads_approval: "bg-violet-100 text-violet-800",
  research_view: "bg-amber-100 text-amber-800",
  done: "bg-gray-100 text-gray-600",
};

const STATUS_LABEL: Record<string, string> = {
  pending_approval: "Pendiente de aprobación",
  approved: "Aprobado",
  rejected: "Rechazado",
  executing: "Ejecutando",
  awaiting_creative_choice: "Elige creativo",
  pending_copy_approval: "Selecciona copies",
  awaiting_funnel_choice: "Elige tu funnel",
  pending_ads_approval: "Revisa la campaña",
  research_view: "Research disponible",
  done: "Completado",
};

interface Props {
  plan: Plan;
}

export function ApprovalCard({ plan }: Props) {
  const { approvePlan, rejectPlan } = usePlansStore();
  const [showReject, setShowReject] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);

  const handleApprove = async () => {
    setLoading(true);
    try {
      await approvePlan(plan.id);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!feedback.trim()) return;
    setLoading(true);
    try {
      await rejectPlan(plan.id, feedback);
      setShowReject(false);
    } finally {
      setLoading(false);
    }
  };

  const showFeed = ["approved", "executing", "awaiting_creative_choice", "pending_copy_approval", "awaiting_funnel_choice", "pending_ads_approval", "done"].includes(plan.status);
  const isRunning = plan.status === "approved" || plan.status === "executing" || plan.status === "pending_ads_approval" || plan.status === "awaiting_funnel_choice" || plan.status === "awaiting_creative_choice";
  const isPendingCopy = plan.status === "pending_copy_approval";
  const isPendingAds = plan.status === "pending_ads_approval";
  const isAwaitingFunnel = plan.status === "awaiting_funnel_choice";
  const isAwaitingCreative = plan.status === "awaiting_creative_choice";

  const { tasksByPlan, fetchTasks } = useTasksStore();
  const tasks = tasksByPlan[plan.id] ?? [];
  const copyTask = tasks.find((t) => t.agent_name === "CopyAgent" && t.status === "completed");
  const adsTask = tasks.find((t) => t.agent_name === "AdsAgent" && t.status === "completed");
  const nextStep = (plan.steps ?? []).findIndex((s: { agent: string }) => s.agent === "LandingAgent");
  // Tras AdsAgent ya no hay más steps — el plan termina
  const nextStepAfterAds = (plan.steps ?? []).length;
  const { upsertPlan } = usePlansStore();

  // Fallback: si el plan ya está en pending_ads_approval pero el task aún no está en store
  useEffect(() => {
    if (isPendingAds && !adsTask) {
      fetchTasks(plan.id);
    }
  }, [plan.id, isPendingAds, tasks.length]);

  // Polling del plan mientras está en ejecución (fallback si falla el WS)
  useEffect(() => {
    if (!isRunning) return;
    const interval = setInterval(async () => {
      try {
        const updated = await api.get<Plan>(`/plans/${plan.id}`);
        upsertPlan(updated);
      } catch {}
    }, 3000);
    return () => clearInterval(interval);
  }, [plan.id, isRunning]);

  return (
    <div className={`rounded-xl border-2 p-4 my-2 ${STATUS_STYLES[plan.status]}`}>
      <div className="flex items-start justify-between mb-2">
        <h3 className="font-semibold text-gray-900 text-sm">{plan.title}</h3>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_BADGE[plan.status]}`}>
          {STATUS_LABEL[plan.status]}
        </span>
      </div>

      <p className="text-gray-600 text-xs mb-3">{plan.description}</p>

      <ol className="space-y-1.5 mb-3">
        {plan.steps.map((step) => (
          <li key={step.order} className="flex gap-2 text-xs">
            <span className="flex-shrink-0 w-5 h-5 rounded-full bg-white border border-gray-300 flex items-center justify-center font-mono font-bold text-gray-500">
              {step.order}
            </span>
            <div>
              <span className="font-medium text-gray-700">{step.agent}</span>
              <span className="text-gray-400 mx-1">›</span>
              <span className="text-gray-600">{step.description}</span>
            </div>
          </li>
        ))}
      </ol>

      {plan.status === "pending_approval" && (
        <>
          {!showReject ? (
            <div className="flex gap-2">
              <button
                onClick={handleApprove}
                disabled={loading}
                className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium py-1.5 rounded-lg transition-colors"
              >
                Aprobar
              </button>
              <button
                onClick={() => setShowReject(true)}
                disabled={loading}
                className="flex-1 bg-red-100 hover:bg-red-200 disabled:opacity-50 text-red-700 text-sm font-medium py-1.5 rounded-lg transition-colors"
              >
                Rechazar
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="¿Qué debería cambiar?"
                rows={2}
                className="w-full text-xs border border-gray-300 rounded-lg p-2 resize-none focus:outline-none focus:ring-2 focus:ring-red-300"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleReject}
                  disabled={loading || !feedback.trim()}
                  className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium py-1.5 rounded-lg transition-colors"
                >
                  Confirmar rechazo
                </button>
                <button
                  onClick={() => setShowReject(false)}
                  disabled={loading}
                  className="px-3 text-gray-500 hover:text-gray-700 text-sm"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {plan.status === "rejected" && plan.feedback && (
        <p className="text-xs text-red-600 mt-1">Feedback: {plan.feedback}</p>
      )}

      {showFeed && (
        <AgentActivityFeed
          planId={plan.id}
          planSteps={plan.steps}
          planStatus={plan.status}
        />
      )}

      {isPendingCopy && copyTask && (
        <CopyApprovalPanel
          plan={plan}
          copyTask={copyTask}
          nextStep={nextStep >= 0 ? nextStep : (plan.steps ?? []).findIndex((s: { agent: string }) => s.agent === "AdsAgent")}
        />
      )}

      {isPendingAds && adsTask && (
        <AdsApprovalPanel
          plan={plan}
          adsTask={adsTask}
          nextStep={nextStepAfterAds >= 0 ? nextStepAfterAds : (plan.steps ?? []).length}
        />
      )}

      {isAwaitingCreative && <CreativeChoiceSelector plan={plan} />}

      {isAwaitingFunnel && <FunnelTypeSelector plan={plan} />}

      {plan.status === "research_view" && <ResearchModeScreen plan={plan} />}
    </div>
  );
}
