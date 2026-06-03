import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { Plan } from "../store/plansStore";

interface ResearchAngle {
  angle: string;
  hook: string | null;
  copy: string | null;
  image_url: string | null;
  headline: string | null;
}

interface AngleHistory {
  angle: string;
  total: number;
  win_rate: number;
}

interface ResearchData {
  plan_id: string;
  business_type: string | null;
  icp: Record<string, unknown> | null;
  pain_points: unknown[];
  angles: ResearchAngle[];
  audience_language: string[];
  angle_history: AngleHistory[];
  scans_remaining: number | null;
}

const ANGLE_LABELS: Record<string, string> = {
  dolor: "Dolor",
  aspiracion: "Aspiración",
  miedo_urgencia: "Miedo / Urgencia",
  social_proof: "Prueba social",
  curiosidad: "Curiosidad",
  credibilidad: "Credibilidad",
};

interface Props {
  plan: Plan;
}

export function ResearchModeScreen({ plan }: Props) {
  const [data, setData] = useState<ResearchData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeAngle, setActiveAngle] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get<ResearchData>(`/plans/${plan.id}/research`);
        setData(res);
        if (res.angles.length > 0) setActiveAngle(res.angles[0].angle);
      } finally {
        setLoading(false);
      }
    })();
  }, [plan.id]);

  // PDF = la vista "tal cual" en una ventana nueva (flujo normal → pagina
  // correctamente todos los ángulos, sin el recorte a 1 página de @media print).
  const handleExport = () => {
    const node = document.getElementById("research-print-area");
    if (!node) return;
    const w = window.open("", "_blank", "width=900,height=1200");
    if (!w) return;

    // Reutilizamos los estilos ya cargados (Tailwind, fuentes) en la ventana nueva.
    const headStyles = Array.from(
      document.querySelectorAll('link[rel="stylesheet"], style')
    )
      .map((el) =>
        el.tagName === "LINK"
          ? `<link rel="stylesheet" href="${(el as HTMLLinkElement).href}">`
          : el.outerHTML
      )
      .join("\n");

    w.document.write(`<!doctype html><html lang="es"><head><meta charset="utf-8" />
      <title>Research</title>
      ${headStyles}
      <style>
        html, body { background: #1c1207 !important; margin: 0; padding: 0; }
        body { padding: 1.2cm; }
        .no-print, .screen-only { display: none !important; }
        .print-only { display: block !important; }
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        article { break-inside: avoid; }
        @page { margin: 0; }
      </style>
    </head><body>${node.outerHTML}</body></html>`);
    w.document.close();
    w.focus();

    let fired = false;
    const fire = () => {
      if (fired) return;
      fired = true;
      w.print();
      w.close();
    };
    // Espera a que carguen las imágenes de los ángulos antes de imprimir.
    const imgs = Array.from(w.document.images);
    const pending = imgs.filter((img) => !img.complete);
    if (pending.length === 0) {
      setTimeout(fire, 300);
      return;
    }
    let left = pending.length;
    const done = () => {
      if (--left <= 0) fire();
    };
    pending.forEach((img) => {
      img.addEventListener("load", done);
      img.addEventListener("error", done);
    });
    setTimeout(fire, 3000); // fallback por si alguna imagen no resuelve
  };

  const copyAngle = (a: ResearchAngle) => {
    const text = `${a.hook || ""}\n\n${a.copy || ""}`.trim();
    navigator.clipboard.writeText(text);
    setCopied(a.angle);
    setTimeout(() => setCopied(null), 1500);
  };

  if (loading) {
    return (
      <div className="mt-4 flex items-center gap-3 text-amber-200/60 text-sm">
        <span className="w-4 h-4 border-2 border-amber-400/40 border-t-amber-300 rounded-full animate-spin" />
        Cargando research…
      </div>
    );
  }
  if (!data) {
    return <div className="mt-4 text-amber-200/60 text-sm">No hay research disponible.</div>;
  }

  const active = data.angles.find((a) => a.angle === activeAngle);

  return (
    <div id="research-print-area" className="mt-4 text-amber-50">
      {/* Hero */}
      <header className="pb-6 border-b border-amber-900/30">
        <p className="text-[11px] font-semibold uppercase tracking-[0.32em] text-amber-500/80">Research Mode</p>
        <h2
          className="mt-3 text-3xl leading-tight text-amber-50"
          style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
        >
          El research y los 6 ángulos,<br />listos para usar
        </h2>
        <p className="mt-3 text-sm text-amber-200/50 max-w-lg">
          ICP, pain points reales y 6 ángulos con copy e imagen. Explóralos y expórtalos cuando quieras.
        </p>
      </header>

      {/* ICP + pain points + histórico */}
      <section className="grid sm:grid-cols-2 gap-x-8 gap-y-7 py-7 border-b border-amber-900/30">
        {data.icp && (
          <div>
            <h3 className="text-amber-500/70 text-[11px] font-semibold uppercase tracking-[0.2em] mb-3">
              Perfil de cliente ideal
            </h3>
            <div className="space-y-2">
              {Object.entries(data.icp).map(([k, v]) => (
                <p key={k} className="text-[13px] leading-relaxed text-amber-100/80">
                  <span className="text-amber-300/90 font-medium">{k}: </span>
                  {String(v)}
                </p>
              ))}
            </div>
          </div>
        )}

        {data.pain_points.length > 0 && (
          <div>
            <h3 className="text-amber-500/70 text-[11px] font-semibold uppercase tracking-[0.2em] mb-3">
              Pain points
            </h3>
            <ul className="space-y-2">
              {data.pain_points.slice(0, 6).map((p, i) => (
                <li key={i} className="flex gap-2 text-[13px] leading-relaxed text-amber-100/80">
                  <span className="text-amber-500/60 mt-0.5">—</span>
                  <span>{typeof p === "string" ? p : (p as { phrase?: string }).phrase || JSON.stringify(p)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.angle_history.length > 0 && (
          <div className="sm:col-span-2">
            <h3 className="text-amber-500/70 text-[11px] font-semibold uppercase tracking-[0.2em] mb-3">
              Histórico de ángulos {data.business_type ? `· ${data.business_type}` : ""}
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {data.angle_history.map((h) => (
                <div
                  key={h.angle}
                  className="flex items-center justify-between rounded-lg border border-amber-900/30 bg-amber-950/20 px-3 py-2"
                >
                  <span className="text-[12px] text-amber-100/70">{ANGLE_LABELS[h.angle] || h.angle}</span>
                  <span className="text-[13px] font-semibold text-amber-300">{h.win_rate}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Ángulos */}
      <section className="py-7">
        <h3 className="text-amber-500/70 text-[11px] font-semibold uppercase tracking-[0.2em] mb-4">
          Los 6 ángulos
        </h3>
        {/* Pantalla: selector interactivo (1 ángulo a la vez) */}
        <div className="screen-only">
          <div className="flex flex-wrap gap-2">
            {data.angles.map((a) => (
              <button
                key={a.angle}
                onClick={() => setActiveAngle(a.angle)}
                className={`text-[13px] px-4 py-2 rounded-full border transition-colors ${
                  activeAngle === a.angle
                    ? "bg-amber-400 text-amber-950 border-amber-400 font-semibold"
                    : "border-amber-800/50 text-amber-100/70 hover:border-amber-500/70 hover:text-amber-100"
                }`}
              >
                {ANGLE_LABELS[a.angle] || a.angle}
              </button>
            ))}
          </div>

          {active && (
            <article className="mt-5 rounded-2xl border border-amber-900/40 bg-gradient-to-b from-amber-950/30 to-transparent p-6">
              <div className="flex flex-col sm:flex-row gap-6">
                {active.image_url && (
                  <img
                    src={active.image_url}
                    alt={active.angle}
                    className="w-full sm:w-40 h-40 rounded-xl object-cover flex-shrink-0 border border-amber-900/40"
                  />
                )}
                <div className="flex-1 min-w-0">
                  {active.hook && (
                    <p
                      className="text-xl leading-snug text-amber-50"
                      style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                    >
                      {active.hook}
                    </p>
                  )}
                  {active.copy && (
                    <p className="mt-3 text-[14px] leading-relaxed text-amber-100/70 whitespace-pre-line">
                      {active.copy}
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => copyAngle(active)}
                className="no-print mt-5 text-[12px] font-medium px-4 py-2 rounded-lg border border-amber-700/50 text-amber-200 hover:bg-amber-400 hover:text-amber-950 hover:border-amber-400 transition-colors"
              >
                {copied === active.angle ? "✓ Copiado" : "Copiar ángulo"}
              </button>
            </article>
          )}
        </div>

        {/* PDF: los 6 ángulos completos, uno tras otro */}
        <div className="print-only space-y-4">
          {data.angles.map((a) => (
            <article
              key={a.angle}
              className="rounded-2xl border border-amber-900/40 bg-gradient-to-b from-amber-950/30 to-transparent p-6"
              style={{ breakInside: "avoid" }}
            >
              <p className="text-amber-500/70 text-[11px] font-semibold uppercase tracking-[0.2em] mb-3">
                {ANGLE_LABELS[a.angle] || a.angle}
              </p>
              <div className="flex gap-6">
                {a.image_url && (
                  <img
                    src={a.image_url}
                    alt={a.angle}
                    className="w-40 h-40 rounded-xl object-cover flex-shrink-0 border border-amber-900/40"
                  />
                )}
                <div className="flex-1 min-w-0">
                  {a.hook && (
                    <p
                      className="text-xl leading-snug text-amber-50"
                      style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}
                    >
                      {a.hook}
                    </p>
                  )}
                  {a.copy && (
                    <p className="mt-3 text-[14px] leading-relaxed text-amber-100/70 whitespace-pre-line">
                      {a.copy}
                    </p>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* Acciones */}
      <footer className="no-print flex flex-wrap items-center justify-between gap-4 pt-6 border-t border-amber-900/30">
        <button
          onClick={handleExport}
          className="text-[12px] font-semibold px-5 py-2 rounded-lg bg-amber-400 text-amber-950 hover:bg-amber-300 transition-colors"
        >
          Exportar PDF
        </button>
        {data.scans_remaining != null && (
          <p className="text-[12px] text-amber-200/50">
            Escaneos restantes este ciclo:{" "}
            <span className="text-amber-300 font-semibold">{data.scans_remaining}</span>
          </p>
        )}
      </footer>
    </div>
  );
}
