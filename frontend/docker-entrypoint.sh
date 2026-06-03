#!/bin/sh
set -e

# Lo ejecuta el entrypoint de la imagen nginx (scripts en /docker-entrypoint.d/)
# ANTES de arrancar nginx. Genera env-config.js desde las env vars del contenedor,
# así VITE_API_URL/VITE_WS_URL NO dependen del build (Coolify las pasa como env normales).
CONFIG_PATH=/usr/share/nginx/html/env-config.js

cat > "$CONFIG_PATH" <<EOF
window.__APP_CONFIG__ = {
  API_URL: "${VITE_API_URL}",
  WS_URL: "${VITE_WS_URL}",
};
EOF

echo "[env-config] generado en $CONFIG_PATH:"
cat "$CONFIG_PATH"
