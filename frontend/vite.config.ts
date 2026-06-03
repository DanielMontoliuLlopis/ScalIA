import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const apiTarget = { target: "http://backend:8000" };

// Si el navegador pide HTML (recarga de página SPA), no proxy al backend:
// devolvemos null para que Vite sirva index.html.
const htmlBypass = (req: { headers: Record<string, string | string[] | undefined> } & any) => {
  const accept = req.headers?.accept;
  const acceptStr = Array.isArray(accept) ? accept.join(",") : accept || "";
  if (req.method === "GET" && acceptStr.includes("text/html")) {
    return req.url;
  }
  return null;
};

const apiProxy = { ...apiTarget, bypass: htmlBypass };

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0",
    allowedHosts: true,
    proxy: {
      "/auth": apiProxy,
      "/chat": apiProxy,
      "/plans": apiProxy,
      "/settings": apiProxy,
      "/landings": apiProxy,
      "/campaigns": apiProxy,
      "/leads": apiProxy,
      "/meta-oauth": apiProxy,
      "/meta/connect-url": apiProxy,
      "/meta/exchange": apiProxy,
      "/meta/ad-accounts": apiProxy,
      "/meta/select-account": apiProxy,
      "/meta/pages": apiProxy,
      "/meta/select-page": apiProxy,
      "/meta/disconnect": apiProxy,
      "/ws": { target: "ws://backend:8000", ws: true },
    },
  },
});
