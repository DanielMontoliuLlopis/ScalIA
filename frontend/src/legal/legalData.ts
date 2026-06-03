// Datos del titular y constantes legales.

export const LEGAL = {
  // Identidad del responsable (art. 10 LSSI + art. 13 RGPD)
  companyName: "Hacelerix",
  legalName: "HACELERIX SOLUTIONS, S.L.",
  cif: "B-23839772",
  address: "Calle Carlos Cervera, 14 Bajo – 46006 – Valencia (Valencia), España",
  contactEmail: "info@hacelerix.com",
  privacyEmail: "info@hacelerix.com",
  domain: "hacelerix.com",

  // Autoridad de control y fechas
  authority: "Agencia Española de Protección de Datos (AEPD) — www.aepd.es",
  lastUpdated: "3 de junio de 2026",
} as const;

export type CookieCategory = "necessary" | "analytics" | "marketing";

export interface CookieDef {
  name: string;
  provider: string;
  purpose: string;
  duration: string;
  category: CookieCategory;
}

// Inventario real de tecnologías de almacenamiento de la plataforma.
// La sesión se guarda en localStorage (JWT) → técnica/necesaria, exenta de consentimiento.
export const COOKIES: CookieDef[] = [
  {
    name: "token",
    provider: LEGAL.companyName,
    purpose:
      "Token de sesión (JWT) en almacenamiento local del navegador. Mantiene la sesión iniciada del usuario. Imprescindible para usar la plataforma.",
    duration: "Hasta cierre de sesión",
    category: "necessary",
  },
  {
    name: "active_client_id",
    provider: LEGAL.companyName,
    purpose:
      "Almacenamiento local que recuerda el cliente/workspace activo en cuentas de agencia.",
    duration: "Hasta cierre de sesión",
    category: "necessary",
  },
  {
    name: "cookie_consent",
    provider: LEGAL.companyName,
    purpose:
      "Almacenamiento local que guarda tu decisión sobre el aviso de cookies para no volver a mostrarlo.",
    duration: "12 meses",
    category: "necessary",
  },
  {
    name: "ref_code",
    provider: LEGAL.companyName,
    purpose:
      "Almacenamiento local temporal que conserva el código de referido (closer) hasta el registro.",
    duration: "Hasta el registro",
    category: "necessary",
  },
];

export const CONSENT_KEY = "cookie_consent";
export const CONSENT_VERSION = "1";
