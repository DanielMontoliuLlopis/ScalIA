import { useEffect, useState } from "react";
import { api } from "../../lib/api";

interface AngleMetric {
  angle: string;
  hook: string | null;
  image_url: string | null;
  status: string;
  budget_share: number | null;
  impressions: number;
  clicks: number;
  leads: number;
  spend: number;
  ctr: number | null;
  cpl: number | null;
  roas: number | null;
}

interface Recommendation {
  id: string;
  type: string;
  reasoning: string;
  status: string;
}

const ANGLE_LABELS: Record<string, string> = {
  dolor: "Dolor",
  aspiracion: "Aspiración",
  miedo_urgencia: "Miedo / Urgencia",
  social_proof: "Prueba social",
  curiosidad: "Curiosidad",
  credibilidad: "Credibilidad",
};

const STATUS_STYLES: Record<string, string> = {
  winner: "bg-green-100 text-green-700",
  loser: "bg-red-100 text-red-700",
  inconclusive: "bg-yellow-100 text-yellow-700",
  insufficient_data: "bg-gray-100 text-gray-500",
  active: "bg-blue-100 text-blue-700",
  paused: "bg-gray-100 text-gray-500",
};

const STATUS_LABELS: Record<string, string> = {
  winner: "Ganador",
  loser: "Perdedor",
  inconclusive: "No concluyente",
  insufficient_data: "Sin señal suficiente",
  active: "Activo",
  paused: "Pausado",
};

interface Props {
  planId: string;
}

export function TabAngles({ planId }: Props) {
  const [angles, setAngles] = useState<AngleMetric[]>([]);
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [a, r] = await Promise.all([
          api.get<AngleMetric[]>(`/analytics/campaign/${planId}/angles`),
          api.get<Recommendation[]>(`/recommendations/campaigns/${planId}`).catch(() => []),
        ]);
        setAngles(a);
        setRecs(r.filter((x) => x.type === "angle_redistribute" || x.type === "angle_inconclusive"));
      } finally {
        setLoading(false);
      }
    })();
  }, [planId]);

  if (loading) return <p className="text-sm text-gray-500">Cargando ángulos…</p>;
  if (angles.length === 0)
    return <p className="text-sm text-gray-500">Esta campaña no usa Multi-Angle Testing.</p>;

  return (
    <div className="space-y-4">
      {recs.map((rec) => (
        <div key={rec.id} className="rounded-xl border border-brand-200 bg-brand-50 p-3">
          <p className="text-xs font-semibold text-brand-700 uppercase tracking-wide mb-1">
            Recomendación del OptimizationAgent
          </p>
          <p className="text-sm text-gray-700">{rec.reasoning}</p>
        </div>
      ))}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-gray-500 border-b border-gray-200">
              <th className="py-2 pr-3">Ángulo</th>
              <th className="py-2 px-2">Estado</th>
              <th className="py-2 px-2 text-right">Impr.</th>
              <th className="py-2 px-2 text-right">CTR</th>
              <th className="py-2 px-2 text-right">Leads</th>
              <th className="py-2 px-2 text-right">CPL</th>
              <th className="py-2 px-2 text-right">Gasto</th>
            </tr>
          </thead>
          <tbody>
            {angles.map((a) => (
              <tr key={a.angle} className="border-b border-gray-100">
                <td className="py-2 pr-3">
                  <div className="flex items-center gap-2">
                    {a.image_url && (
                      <img src={a.image_url} alt={a.angle} className="w-9 h-9 rounded object-cover" />
                    )}
                    <div className="min-w-0">
                      <p className="font-medium text-gray-900">{ANGLE_LABELS[a.angle] || a.angle}</p>
                      {a.hook && <p className="text-xs text-gray-500 truncate max-w-[200px]">{a.hook}</p>}
                    </div>
                  </div>
                </td>
                <td className="py-2 px-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[a.status] || "bg-gray-100 text-gray-500"}`}>
                    {STATUS_LABELS[a.status] || a.status}
                  </span>
                </td>
                <td className="py-2 px-2 text-right tabular-nums">{a.impressions.toLocaleString()}</td>
                <td className="py-2 px-2 text-right tabular-nums">{a.ctr != null ? `${a.ctr.toFixed(2)}%` : "—"}</td>
                <td className="py-2 px-2 text-right tabular-nums">{a.leads}</td>
                <td className="py-2 px-2 text-right tabular-nums">{a.cpl != null ? `€${a.cpl.toFixed(2)}` : "—"}</td>
                <td className="py-2 px-2 text-right tabular-nums">€{a.spend.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
