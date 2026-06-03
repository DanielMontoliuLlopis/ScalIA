import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

export function BillingSuccess() {
  const navigate = useNavigate();
  const { fetchMe } = useAuthStore();

  useEffect(() => {
    // El webhook tarda un poco. Hacemos polling de /auth/me hasta que subscription_status esté activo.
    let cancelled = false;
    let attempts = 0;
    const tick = async () => {
      if (cancelled) return;
      attempts += 1;
      await fetchMe();
      const status = useAuthStore.getState().user?.subscription_status;
      const research = useAuthStore.getState().features?.research_only;
      const dest = research ? "/research" : "/campaigns/new";
      if (status === "trialing" || status === "active") {
        navigate(dest, { replace: true });
        return;
      }
      if (attempts > 20) {
        navigate(dest, { replace: true });
        return;
      }
      setTimeout(tick, 1000);
    };
    tick();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 via-white to-violet-50 flex items-center justify-center p-4">
      <div className="bg-white/90 backdrop-blur-2xl rounded-2xl shadow-glass-lg border border-gray-200 p-10 max-w-md text-center">
        <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900">¡Trial activado!</h1>
        <p className="text-gray-600 mt-2 text-sm">
          Tu suscripción está lista. Te llevamos a tu panel…
        </p>
        <div className="mt-6 flex justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-brand-600"></div>
        </div>
      </div>
    </div>
  );
}
