import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import type { Campaign, Lead } from "./types";

interface EmailMsg {
  order: number;
  send_delay_hours: number;
  subject: string;
  preview_text?: string;
  body_html?: string;
  cta_text?: string;
  cta_url?: string;
  goal?: string;
}

interface WhatsAppMsg {
  order: number;
  send_delay_hours: number;
  text: string;
  goal?: string;
}

const SEQ_TYPES_EMAIL = ["Bienvenida", "Valor", "Prueba social", "Objeción", "Urgencia"];
const SEQ_TYPES_WA = ["Bienvenida", "Tip", "Prueba social", "Objeción", "Cierre"];

const COLORS_EMAIL = [
  "from-brand-500 to-violet-500",
  "from-emerald-500 to-teal-500",
  "from-amber-500 to-orange-500",
  "from-sky-500 to-blue-500",
  "from-rose-500 to-pink-500",
];

function delayLabel(hours: number) {
  if (hours === 0) return "Inmediato";
  if (hours < 24) return `+${hours}h`;
  return `+${Math.round(hours / 24)}d`;
}

function aggregateStats(
  leads: Lead[],
  channel: "email" | "whatsapp",
  order: number,
): { sent: number; scheduled: number; failed: number; skipped: number } {
  const stats = { sent: 0, scheduled: 0, failed: 0, skipped: 0 };
  for (const lead of leads) {
    const ev = lead.sequence_events.find((e) => e.channel === channel && e.order === order);
    if (!ev) continue;
    if (ev.status in stats) {
      stats[ev.status as keyof typeof stats] += 1;
    }
  }
  return stats;
}

function StepCard({
  index,
  title,
  delay,
  badge,
  preview,
  stats,
  totalLeads,
  body,
  cta,
  gradient,
}: {
  index: number;
  title: string;
  delay: number;
  badge: string;
  preview?: string;
  stats: { sent: number; scheduled: number; failed: number; skipped: number };
  totalLeads: number;
  body?: string;
  cta?: { text?: string; url?: string };
  gradient: string;
}) {
  const [expanded, setExpanded] = useState(false);
  const done = stats.sent;
  const pending = stats.scheduled;
  const pct = totalLeads > 0 ? Math.round((done / totalLeads) * 100) : 0;

  return (
    <div className="flex gap-3 relative">
      {/* Bullet */}
      <div className="flex flex-col items-center shrink-0">
        <div
          className={`w-10 h-10 rounded-full bg-gradient-to-br ${gradient} text-white text-xs font-bold flex items-center justify-center shadow-sm z-10`}
        >
          {index + 1}
        </div>
        <p className="text-[10px] text-gray-400 mt-1 font-medium">{delayLabel(delay)}</p>
      </div>

      <div className="flex-1 bg-white border border-gray-200 rounded-xl p-3 mb-3 space-y-2">
        {/* Header */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 mb-0.5">
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                {badge}
              </span>
            </div>
            <p className="text-sm font-semibold text-gray-800">{title}</p>
            {preview && <p className="text-xs text-gray-500 line-clamp-2 mt-0.5">{preview}</p>}
          </div>
          {body && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="shrink-0 text-xs text-brand-600 hover:underline font-medium"
            >
              {expanded ? "Ocultar" : "Ver contenido"}
            </button>
          )}
        </div>

        {/* Stats por lead */}
        {totalLeads > 0 && (
          <div className="space-y-1.5 pt-1 border-t border-gray-100">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">
                <span className="font-semibold text-gray-700">{done}</span> / {totalLeads} leads recibieron
              </span>
              <div className="flex items-center gap-2 text-[10px]">
                {pending > 0 && (
                  <span className="text-blue-600">⏱ {pending} programados</span>
                )}
                {stats.failed > 0 && (
                  <span className="text-red-600">✕ {stats.failed} fallos</span>
                )}
                {stats.skipped > 0 && (
                  <span className="text-gray-400">— {stats.skipped} omitidos</span>
                )}
              </div>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${gradient} transition-all`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )}

        {/* Contenido expandido */}
        {expanded && body && (
          <div className="pt-2 border-t border-gray-100 space-y-2">
            <div className="text-xs text-gray-700 bg-gray-50 rounded-lg p-3 max-h-60 overflow-y-auto whitespace-pre-wrap leading-relaxed"
              dangerouslySetInnerHTML={{ __html: body }} />
            {cta?.text && (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-gray-400">CTA:</span>
                <span className="px-2 py-0.5 bg-brand-100 text-brand-700 rounded font-medium">
                  {cta.text}
                </span>
                {cta.url && (
                  <a
                    href={cta.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-brand-600 hover:underline truncate"
                  >
                    {cta.url}
                  </a>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function TabSequences({ campaign }: { campaign: Campaign }) {
  const [channel, setChannel] = useState<"email" | "whatsapp">("email");
  const [leads, setLeads] = useState<Lead[]>([]);

  useEffect(() => {
    api.get<Lead[]>(`/campaigns/${campaign.plan_id}/leads`).then(setLeads).catch(() => {});
  }, [campaign.plan_id]);

  const emailOutput = campaign.email_output as {
    email_sequence?: { emails?: EmailMsg[]; post_conversion_goal?: string };
    whatsapp_sequence?: { messages?: WhatsAppMsg[] };
  } | null;

  const emails: EmailMsg[] = emailOutput?.email_sequence?.emails ?? [];
  const waMessages: WhatsAppMsg[] = emailOutput?.whatsapp_sequence?.messages ?? [];
  const goal = emailOutput?.email_sequence?.post_conversion_goal;

  const hasEmail = emails.length > 0;
  const hasWA = waMessages.length > 0;
  const hasAny = hasEmail || hasWA;

  // Stats globales
  const totalLeads = leads.length;
  const leadsWithPhone = leads.filter((l) => l.telefono).length;

  return (
    <div className="space-y-4">
      {/* Resumen global */}
      {hasAny && (
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-brand-50 rounded-xl p-3 text-center">
            <p className="text-lg font-bold text-brand-700">{totalLeads}</p>
            <p className="text-xs text-brand-500">Leads en secuencia</p>
          </div>
          <div className="bg-emerald-50 rounded-xl p-3 text-center">
            <p className="text-lg font-bold text-emerald-700">{leadsWithPhone}</p>
            <p className="text-xs text-emerald-500">Reciben WhatsApp</p>
          </div>
          <div className="bg-violet-50 rounded-xl p-3 text-center">
            <p className="text-lg font-bold text-violet-700">{emails.length + waMessages.length}</p>
            <p className="text-xs text-violet-500">Pasos por lead</p>
          </div>
        </div>
      )}

      {/* Canal toggle */}
      <div className="flex items-center gap-2">
        <div className="flex bg-gray-100 rounded-xl p-1 gap-1">
          <button
            onClick={() => setChannel("email")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              channel === "email" ? "bg-white shadow-sm text-brand-700" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            ✉️ Email
            {hasEmail && (
              <span className="bg-brand-100 text-brand-600 rounded-full px-1.5 py-0.5 text-[10px] font-bold">
                {emails.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setChannel("whatsapp")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              channel === "whatsapp" ? "bg-white shadow-sm text-emerald-700" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            💬 WhatsApp
            {hasWA && (
              <span className="bg-emerald-100 text-emerald-600 rounded-full px-1.5 py-0.5 text-[10px] font-bold">
                {waMessages.length}
              </span>
            )}
          </button>
        </div>
        {goal && (
          <span className="text-xs text-gray-400 bg-gray-50 border border-gray-200 rounded-full px-2.5 py-1">
            objetivo: <strong className="text-gray-600">{goal.replace(/_/g, " ")}</strong>
          </span>
        )}
      </div>

      {!hasAny && (
        <div className="text-center py-10 text-gray-400">
          <p className="text-3xl mb-2">📭</p>
          <p className="text-sm">El EmailAgent aún no ha generado las secuencias.</p>
        </div>
      )}

      {/* Email timeline */}
      {channel === "email" && hasEmail && (
        <div className="relative">
          <div className="absolute left-5 top-5 bottom-5 w-px bg-gradient-to-b from-brand-200 via-violet-200 to-rose-200" />
          <div>
            {emails.map((e, i) => {
              const stats = aggregateStats(leads, "email", e.order ?? i + 1);
              return (
                <StepCard
                  key={e.order}
                  index={i}
                  title={e.subject}
                  delay={e.send_delay_hours}
                  badge={SEQ_TYPES_EMAIL[i] ?? `Email ${i + 1}`}
                  preview={e.preview_text}
                  stats={stats}
                  totalLeads={totalLeads}
                  body={e.body_html}
                  cta={{ text: e.cta_text, url: e.cta_url }}
                  gradient={COLORS_EMAIL[i % COLORS_EMAIL.length]}
                />
              );
            })}
          </div>
        </div>
      )}

      {channel === "email" && !hasEmail && (
        <div className="text-center py-8 text-gray-400">
          <p className="text-sm">No hay secuencia de email generada.</p>
        </div>
      )}

      {/* WhatsApp timeline */}
      {channel === "whatsapp" && hasWA && (
        <div className="relative">
          <div className="absolute left-5 top-5 bottom-5 w-px bg-emerald-200" />
          <div>
            {waMessages.map((m, i) => {
              const stats = aggregateStats(leads, "whatsapp", m.order ?? i + 1);
              return (
                <StepCard
                  key={m.order}
                  index={i}
                  title={m.text.slice(0, 80) + (m.text.length > 80 ? "…" : "")}
                  delay={m.send_delay_hours}
                  badge={SEQ_TYPES_WA[i] ?? `Msg ${i + 1}`}
                  preview={m.text}
                  stats={stats}
                  totalLeads={leadsWithPhone}
                  body={m.text}
                  gradient="from-emerald-500 to-teal-500"
                />
              );
            })}
          </div>
          <p className="text-xs text-gray-400 mt-2 pl-1">
            💡 Solo se envía si el lead proporcionó teléfono. Requiere WhatsApp Business configurado en Ajustes.
          </p>
        </div>
      )}

      {channel === "whatsapp" && !hasWA && (
        <div className="text-center py-8 text-gray-400">
          <p className="text-sm">No hay secuencia de WhatsApp generada.</p>
        </div>
      )}
    </div>
  );
}
