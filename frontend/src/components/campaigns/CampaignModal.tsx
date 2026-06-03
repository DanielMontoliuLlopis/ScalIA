import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { TabCampaign } from "./TabCampaign";
import { TabSequences } from "./TabSequences";
import { TabLeads } from "./TabLeads";
import { TabAngles } from "./TabAngles";
import type { Campaign, MetaStatus } from "./types";

export type { Campaign } from "./types";

interface Props {
  campaign: Campaign;
  onClose: () => void;
}

function statusLabel(s: string) {
  const map: Record<string, string> = {
    executing: "En ejecución",
    pending_ads_approval: "Pendiente de ads",
    pending_copy_approval: "Pendiente de copies",
    done: "Completada",
  };
  return map[s] ?? s;
}

function statusColor(s: string) {
  if (s === "done") return "bg-green-100 text-green-700";
  if (s === "executing") return "bg-blue-100 text-blue-700";
  return "bg-yellow-100 text-yellow-700";
}

type Tab = "campaign" | "sequences" | "leads" | "angles";

export function CampaignModal({ campaign: initialCampaign, onClose }: Props) {
  const [tab, setTab] = useState<Tab>("campaign");
  const [campaign, setCampaign] = useState<Campaign>(initialCampaign);
  const [metaStatus, setMetaStatus] = useState<MetaStatus | null>(null);

  useEffect(() => {
    api
      .get<MetaStatus>(`/campaigns/${campaign.plan_id}/meta-status`)
      .then(setMetaStatus)
      .catch(() => setMetaStatus({ has_meta_campaign: false, meta_status: null, is_locked: false, error: null }));
  }, [campaign.plan_id]);

  const tabs: Array<{ id: Tab; label: string; emoji: string }> = [
    { id: "campaign", label: "Campaña", emoji: "📣" },
    { id: "sequences", label: "Secuencias", emoji: "✉️" },
    { id: "leads", label: `Leads (${campaign.total_leads})`, emoji: "🎯" },
    ...(campaign.ab_mode === "multi_angle"
      ? [{ id: "angles" as Tab, label: "Ángulos", emoji: "🎭" }]
      : []),
  ];

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="bg-white/90 backdrop-blur-2xl rounded-2xl shadow-glass-lg w-full max-w-7xl flex flex-col"
        style={{ aspectRatio: "16 / 9", maxHeight: "92vh" }}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-gray-100">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor(campaign.status)}`}>
                {statusLabel(campaign.status)}
              </span>
              {metaStatus?.has_meta_campaign && metaStatus.meta_status && (
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    metaStatus.is_locked
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-600"
                  }`}
                >
                  Meta: {metaStatus.meta_status}
                </span>
              )}
              <span className="text-xs text-gray-400">
                {new Date(campaign.created_at).toLocaleDateString("es-ES", {
                  day: "2-digit",
                  month: "long",
                  year: "numeric",
                })}
              </span>
            </div>
            <h2 className="font-bold text-gray-900 text-base truncate">{campaign.title}</h2>
          </div>
          <button
            onClick={onClose}
            className="ml-3 shrink-0 w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-100 px-5">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-3 py-3 text-sm font-medium border-b-2 transition-colors -mb-px ${
                tab === t.id
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              <span>{t.emoji}</span>
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {tab === "campaign" && (
            <TabCampaign campaign={campaign} metaStatus={metaStatus} onUpdated={setCampaign} />
          )}
          {tab === "sequences" && <TabSequences campaign={campaign} />}
          {tab === "leads" && <TabLeads planId={campaign.plan_id} />}
          {tab === "angles" && <TabAngles planId={campaign.plan_id} />}
        </div>
      </div>
    </div>
  );
}
