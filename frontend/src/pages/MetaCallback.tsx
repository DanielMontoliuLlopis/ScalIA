import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../lib/api";

export function MetaCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const code = searchParams.get("code");
    const errorParam = searchParams.get("error");

    if (errorParam) {
      setError("El usuario canceló la conexión con Meta.");
      setTimeout(() => navigate("/settings"), 3000);
      return;
    }

    if (!code) {
      setError("No se recibió código de autorización.");
      setTimeout(() => navigate("/settings"), 3000);
      return;
    }

    const state = searchParams.get("state");
    api
      .post("/meta/exchange", { code, state })
      .then(() => navigate("/settings?meta=connected"))
      .catch((err: Error) => {
        setError(err.message ?? "Error conectando con Meta");
        setTimeout(() => navigate("/settings"), 4000);
      });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white/70 backdrop-blur-xl rounded-2xl border border-white/50 shadow-glass p-8 max-w-sm w-full text-center space-y-4">
        {error ? (
          <>
            <div className="text-3xl">❌</div>
            <p className="text-sm font-medium text-red-700">{error}</p>
            <p className="text-xs text-gray-400">Redirigiendo a Settings…</p>
          </>
        ) : (
          <>
            <div className="text-3xl animate-spin inline-block">⚙️</div>
            <p className="text-sm font-medium text-gray-700">Conectando tu cuenta de Meta…</p>
          </>
        )}
      </div>
    </div>
  );
}
