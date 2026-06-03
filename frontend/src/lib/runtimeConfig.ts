// Config resuelta en runtime, no en build.
// Prioridad:
//   1. window.__APP_CONFIG__  → inyectado por /env-config.js (generado al arrancar el contenedor)
//   2. import.meta.env.VITE_* → build-time (dev local con .env)
//   3. fallback → mismo origen
declare global {
  interface Window {
    __APP_CONFIG__?: {
      API_URL?: string;
      WS_URL?: string;
    };
  }
}

function clean(v: string | undefined): string {
  if (!v) return "";
  // ignora placeholders sin sustituir (ej: "${VITE_API_URL}" o "__API_URL__")
  if (v.includes("${") || v.startsWith("__")) return "";
  return v.replace(/\/+$/, ""); // sin barra final
}

export const API_URL: string =
  clean(window.__APP_CONFIG__?.API_URL) ||
  clean(import.meta.env.VITE_API_URL) ||
  "";

export const WS_URL: string =
  clean(window.__APP_CONFIG__?.WS_URL) ||
  clean(import.meta.env.VITE_WS_URL) ||
  `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}`;
