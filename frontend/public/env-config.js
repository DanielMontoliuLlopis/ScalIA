// Default para desarrollo local. En producción el contenedor lo SOBREESCRIBE
// al arrancar (docker-entrypoint.sh) con los valores de las env vars.
// Vacío = usa import.meta.env (dev) o el mismo origen como fallback.
window.__APP_CONFIG__ = {
  API_URL: "",
  WS_URL: "",
};
