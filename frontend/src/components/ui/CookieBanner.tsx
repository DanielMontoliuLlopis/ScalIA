import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CONSENT_KEY, CONSENT_VERSION } from "../../legal/legalData";

/**
 * Banner de cookies. La plataforma solo usa cookies/almacenamiento TÉCNICOS
 * (exentos de consentimiento, art. 22.2 LSSI-CE), por lo que el aviso es
 * informativo: el usuario confirma haberlo leído. Si en el futuro se añaden
 * cookies analíticas o de marketing en la app, este componente debe ampliarse
 * con opciones de aceptar/rechazar por categoría ANTES de cargarlas.
 */
export function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(CONSENT_KEY);
      if (stored !== CONSENT_VERSION) setVisible(true);
    } catch {
      setVisible(true);
    }
  }, []);

  const accept = () => {
    try {
      localStorage.setItem(CONSENT_KEY, CONSENT_VERSION);
    } catch {
      /* almacenamiento no disponible */
    }
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-label="Aviso de cookies"
      className="fixed bottom-4 inset-x-4 md:left-auto md:right-6 md:max-w-md z-[1000]"
    >
      <div className="bg-white border border-gray-200 rounded-2xl shadow-2xl p-5">
        <p className="text-sm text-gray-700 leading-relaxed">
          Usamos únicamente <strong>cookies técnicas necesarias</strong> para mantener tu
          sesión y el funcionamiento de la plataforma. No usamos cookies de publicidad ni de
          seguimiento. Consulta nuestra{" "}
          <Link to="/legal/cookies" className="text-brand-600 hover:underline">
            Política de Cookies
          </Link>
          .
        </p>
        <div className="mt-4 flex items-center justify-end gap-3">
          <Link
            to="/legal/cookies"
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            Más información
          </Link>
          <button
            onClick={accept}
            className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
          >
            Entendido
          </button>
        </div>
      </div>
    </div>
  );
}
