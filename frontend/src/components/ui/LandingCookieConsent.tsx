import { useEffect, useState } from "react";

const LANDING_CONSENT_KEY = "landing_cookie_consent";

/**
 * Banner de consentimiento para landings publicadas que cargan el píxel de Meta
 * (cookie de marketing). A diferencia del banner de la app, aquí SÍ hay que
 * recabar consentimiento previo (art. 22.2 LSSI-CE): el píxel solo se carga si
 * el visitante acepta. La decisión se guarda en el navegador del visitante.
 */
export function LandingCookieConsent({
  pixelId,
  onAccept,
}: {
  pixelId: string;
  onAccept: () => void;
}) {
  const [decision, setDecision] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let stored: string | null = null;
    try {
      stored = localStorage.getItem(LANDING_CONSENT_KEY);
    } catch {
      /* almacenamiento no disponible */
    }
    setDecision(stored);
    if (stored === "accepted") onAccept();
    setReady(true);
    // pixelId en deps por si cambia entre landings
  }, [pixelId]);

  const accept = () => {
    try {
      localStorage.setItem(LANDING_CONSENT_KEY, "accepted");
    } catch {
      /* noop */
    }
    setDecision("accepted");
    onAccept();
  };

  const reject = () => {
    try {
      localStorage.setItem(LANDING_CONSENT_KEY, "rejected");
    } catch {
      /* noop */
    }
    setDecision("rejected");
  };

  if (!ready || decision) return null;

  return (
    <div
      role="dialog"
      aria-label="Consentimiento de cookies"
      className="fixed bottom-0 inset-x-0 z-[1000] p-4"
    >
      <div className="max-w-3xl mx-auto bg-white border border-gray-200 rounded-2xl shadow-2xl p-5 md:flex md:items-center md:gap-6">
        <p className="text-sm text-gray-700 leading-relaxed flex-1">
          Esta página usa cookies de medición publicitaria (píxel de Meta) para entender el
          rendimiento de la campaña. Puedes aceptarlas o rechazarlas. Si las rechazas, la
          página sigue funcionando con normalidad.
        </p>
        <div className="flex items-center justify-end gap-3 mt-4 md:mt-0 flex-shrink-0">
          <button
            onClick={reject}
            className="text-sm font-medium px-5 py-2 rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Rechazar
          </button>
          <button
            onClick={accept}
            className="text-sm font-medium px-5 py-2 rounded-lg bg-gray-900 text-white hover:bg-gray-800 transition-colors"
          >
            Aceptar
          </button>
        </div>
      </div>
    </div>
  );
}
