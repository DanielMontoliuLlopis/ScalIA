export const OBJECTIVE_LABELS: Record<string, string> = {
  OUTCOME_LEADS: "Generación de leads",
  OUTCOME_SALES: "Ventas",
  OUTCOME_ENGAGEMENT: "Interacción",
  OUTCOME_AWARENESS: "Reconocimiento de marca",
  OUTCOME_TRAFFIC: "Tráfico",
  OUTCOME_APP_PROMOTION: "Promoción de app",
  LEAD_GENERATION: "Generación de leads",
  CONVERSIONS: "Conversiones",
};

export const OBJECTIVE_OPTIONS = [
  { value: "OUTCOME_LEADS", label: "Generación de leads" },
  { value: "OUTCOME_SALES", label: "Ventas" },
  { value: "OUTCOME_TRAFFIC", label: "Tráfico" },
  { value: "OUTCOME_ENGAGEMENT", label: "Interacción" },
  { value: "OUTCOME_AWARENESS", label: "Reconocimiento" },
];

export const OPTIMIZATION_LABELS: Record<string, string> = {
  LEAD: "Lead",
  LEAD_GENERATION: "Generación de leads",
  OFFSITE_CONVERSIONS: "Conversiones externas",
  IMPRESSIONS: "Impresiones",
  LINK_CLICKS: "Clics en enlace",
  LANDING_PAGE_VIEWS: "Vistas de landing",
  REACH: "Alcance",
};

export const OPTIMIZATION_OPTIONS = [
  { value: "LEAD_GENERATION", label: "Generación de leads" },
  { value: "OFFSITE_CONVERSIONS", label: "Conversiones externas" },
  { value: "LINK_CLICKS", label: "Clics en enlace" },
  { value: "LANDING_PAGE_VIEWS", label: "Vistas de landing" },
  { value: "IMPRESSIONS", label: "Impresiones" },
  { value: "REACH", label: "Alcance" },
];

export const BILLING_LABELS: Record<string, string> = {
  IMPRESSIONS: "CPM (por 1000 impresiones)",
  LINK_CLICKS: "CPC (por clic)",
};

export const BID_LABELS: Record<string, string> = {
  LOWEST_COST_WITHOUT_CAP: "Coste mínimo sin límite",
  LOWEST_COST_WITH_BID_CAP: "Coste mínimo con límite",
  COST_CAP: "Límite de coste objetivo",
};

export const BID_OPTIONS = [
  { value: "LOWEST_COST_WITHOUT_CAP", label: "Coste mínimo sin límite" },
  { value: "LOWEST_COST_WITH_BID_CAP", label: "Coste mínimo con límite" },
  { value: "COST_CAP", label: "Límite de coste objetivo" },
];

export const CTA_OPTIONS = [
  "SHOP_NOW", "LEARN_MORE", "SIGN_UP", "SUBSCRIBE", "DOWNLOAD",
  "BOOK_TRAVEL", "CONTACT_US", "GET_OFFER", "GET_QUOTE",
  "APPLY_NOW", "ORDER_NOW", "BUY_NOW", "WATCH_MORE",
];

export const PLATFORM_ICONS: Record<string, string> = {
  facebook: "📘",
  instagram: "📸",
  messenger: "💬",
  audience_network: "🌐",
};

export const PLATFORM_OPTIONS = [
  { value: "facebook", label: "📘 Facebook" },
  { value: "instagram", label: "📸 Instagram" },
  { value: "messenger", label: "💬 Messenger" },
  { value: "audience_network", label: "🌐 Audience Network" },
];

export const FACEBOOK_POSITIONS = [
  { value: "feed", label: "Feed" },
  { value: "story", label: "Stories" },
  { value: "reels", label: "Reels" },
  { value: "marketplace", label: "Marketplace" },
  { value: "right_hand_column", label: "Columna derecha" },
];

export const INSTAGRAM_POSITIONS = [
  { value: "stream", label: "Feed" },
  { value: "story", label: "Stories" },
  { value: "reels", label: "Reels" },
  { value: "explore", label: "Explorar" },
];

export const PLACEMENT_LABELS: Record<string, string> = {
  feed: "Feed",
  story: "Stories",
  reels: "Reels",
  stream: "Feed",
  explore: "Explorar",
  right_hand_column: "Columna derecha",
  marketplace: "Marketplace",
};

export const DEVICE_OPTIONS = [
  { value: "mobile", label: "📱 Móvil" },
  { value: "desktop", label: "🖥 Desktop" },
];

export const COUNTRY_NAMES: Record<string, string> = {
  ES: "🇪🇸 España", MX: "🇲🇽 México", AR: "🇦🇷 Argentina",
  CO: "🇨🇴 Colombia", US: "🇺🇸 EE.UU.", GB: "🇬🇧 Reino Unido",
  DE: "🇩🇪 Alemania", FR: "🇫🇷 Francia", CL: "🇨🇱 Chile", PE: "🇵🇪 Perú",
  IT: "🇮🇹 Italia", PT: "🇵🇹 Portugal", BR: "🇧🇷 Brasil",
};

export const COLOR_PALETTES = [
  { name: "Indigo", primary: "#6366f1" },
  { name: "Emerald", primary: "#10b981" },
  { name: "Violet", primary: "#8b5cf6" },
  { name: "Sky", primary: "#0ea5e9" },
  { name: "Rose", primary: "#f43f5e" },
  { name: "Amber", primary: "#f59e0b" },
  { name: "Cyan", primary: "#06b6d4" },
  { name: "Slate", primary: "#475569" },
  { name: "Orange", primary: "#f97316" },
  { name: "Teal", primary: "#14b8a6" },
];

export const SEGMENT_COLORS: Record<string, string> = {
  hot: "bg-red-100 text-red-700 border-red-200",
  warm: "bg-amber-100 text-amber-700 border-amber-200",
  cold: "bg-gray-100 text-gray-500 border-gray-200",
};

export const ACTION_COLORS: Record<string, string> = {
  red: "bg-red-50 text-red-700 border-red-200",
  amber: "bg-amber-50 text-amber-700 border-amber-200",
  gray: "bg-gray-50 text-gray-600 border-gray-200",
};

export const SPECIAL_AD_CATEGORIES: Record<string, string> = {
  NONE: "Ninguna",
  EMPLOYMENT: "Empleo",
  HOUSING: "Vivienda",
  CREDIT: "Crédito",
  ISSUES_ELECTIONS_POLITICS: "Política / elecciones",
  ONLINE_GAMBLING_AND_GAMING: "Juegos de azar",
  FINANCIAL_PRODUCTS_SERVICES: "Productos financieros",
};

export const CUSTOM_EVENT_TYPES: Record<string, string> = {
  PURCHASE: "Compra",
  LEAD: "Lead",
  ADD_TO_CART: "Añadir al carrito",
  INITIATE_CHECKOUT: "Iniciar checkout",
  ADD_PAYMENT_INFO: "Info de pago",
  COMPLETE_REGISTRATION: "Registro completado",
  CONTACT: "Contacto",
  SCHEDULE: "Programar cita",
  SEARCH: "Búsqueda",
  START_TRIAL: "Inicio de trial",
  SUBSCRIBE: "Suscripción",
  VIEW_CONTENT: "Vista de contenido",
  SUBMIT_APPLICATION: "Solicitud enviada",
  DONATE: "Donación",
};

export const DESTINATION_LABELS: Record<string, string> = {
  WEBSITE: "Sitio web",
  APP: "App",
  MESSENGER: "Messenger",
  WHATSAPP: "WhatsApp",
  INSTAGRAM_DIRECT: "Instagram Direct",
  ON_AD: "En el anuncio",
  SHOP_AUTOMATIC: "Tienda Meta",
  FACEBOOK: "Facebook",
  APP_STORE: "App Store",
  DEEPLINK: "Deeplink",
};

export const PACING_LABELS: Record<string, string> = {
  standard: "Estándar — distribución uniforme",
  no_pacing: "Acelerado — entrega lo antes posible",
};

export const GENDER_LABELS: Record<number, string> = {
  1: "👨 Hombres",
  2: "👩 Mujeres",
};

export const BUYING_TYPE_LABELS: Record<string, string> = {
  AUCTION: "Subasta",
  RESERVED: "Reservada",
};

// ─── Opciones de edición ampliadas ──────────────────────────────────────────

export const BUYING_TYPE_OPTIONS = [
  { value: "AUCTION", label: "Subasta" },
  { value: "RESERVED", label: "Reservada (Reach & Frequency)" },
];

export const CAMPAIGN_BID_OPTIONS = [
  { value: "LOWEST_COST_WITHOUT_CAP", label: "Coste mínimo sin límite" },
  { value: "LOWEST_COST_WITH_BID_CAP", label: "Coste mínimo con tope de puja" },
  { value: "COST_CAP", label: "Límite de coste objetivo" },
  { value: "LOWEST_COST_WITH_MIN_ROAS", label: "ROAS mínimo objetivo" },
];

export const BILLING_OPTIONS = [
  { value: "IMPRESSIONS", label: "CPM — por 1000 impresiones" },
  { value: "LINK_CLICKS", label: "CPC — por clic en enlace" },
  { value: "THRUPLAY", label: "ThruPlay — vídeo" },
];

export const DESTINATION_OPTIONS = [
  { value: "WEBSITE", label: "Sitio web" },
  { value: "APP", label: "App" },
  { value: "MESSENGER", label: "Messenger" },
  { value: "WHATSAPP", label: "WhatsApp" },
  { value: "INSTAGRAM_DIRECT", label: "Instagram Direct" },
  { value: "ON_AD", label: "En el anuncio (Lead Form)" },
  { value: "PHONE_CALL", label: "Llamada" },
];

export const PACING_OPTIONS = [
  { value: "standard", label: "Estándar (uniforme)" },
  { value: "no_pacing", label: "Acelerado" },
];

export const GENDER_OPTIONS = [
  { value: "1", label: "👨 Hombres" },
  { value: "2", label: "👩 Mujeres" },
];

export const SPECIAL_AD_CATEGORY_OPTIONS = [
  { value: "EMPLOYMENT", label: "Empleo" },
  { value: "HOUSING", label: "Vivienda" },
  { value: "CREDIT", label: "Crédito" },
  { value: "ISSUES_ELECTIONS_POLITICS", label: "Política / elecciones" },
  { value: "ONLINE_GAMBLING_AND_GAMING", label: "Juegos de azar" },
  { value: "FINANCIAL_PRODUCTS_SERVICES", label: "Productos financieros" },
];

export const CUSTOM_EVENT_OPTIONS = [
  { value: "LEAD", label: "Lead" },
  { value: "PURCHASE", label: "Compra" },
  { value: "ADD_TO_CART", label: "Añadir al carrito" },
  { value: "INITIATE_CHECKOUT", label: "Iniciar checkout" },
  { value: "ADD_PAYMENT_INFO", label: "Info de pago" },
  { value: "COMPLETE_REGISTRATION", label: "Registro completado" },
  { value: "CONTACT", label: "Contacto" },
  { value: "SCHEDULE", label: "Programar cita" },
  { value: "SEARCH", label: "Búsqueda" },
  { value: "START_TRIAL", label: "Inicio de trial" },
  { value: "SUBSCRIBE", label: "Suscripción" },
  { value: "VIEW_CONTENT", label: "Vista de contenido" },
  { value: "SUBMIT_APPLICATION", label: "Solicitud enviada" },
  { value: "DONATE", label: "Donación" },
];

export const ATTRIBUTION_EVENT_OPTIONS = [
  { value: "CLICK_THROUGH", label: "Por clic" },
  { value: "VIEW_THROUGH", label: "Por vista" },
  { value: "ENGAGED_VIDEO_VIEW", label: "Vídeo visto" },
];

export const ATTRIBUTION_WINDOW_OPTIONS = [1, 7, 28];

export const AUDIENCE_NETWORK_POSITIONS = [
  { value: "classic", label: "Classic" },
  { value: "rewarded_video", label: "Vídeo con recompensa" },
];

export const MESSENGER_POSITIONS = [
  { value: "messenger_home", label: "Bandeja Messenger" },
  { value: "story", label: "Stories Messenger" },
];

export const FREQUENCY_EVENT_OPTIONS = [
  { value: "IMPRESSIONS", label: "Impresiones" },
  { value: "VIDEO_VIEWS", label: "Reproducciones" },
  { value: "REACH", label: "Alcance" },
];

export const ATTRIBUTION_EVENT_LABELS: Record<string, string> = {
  CLICK_THROUGH: "Por clic",
  VIEW_THROUGH: "Por vista",
};
