# Despliegue en Coolify — Growth OS

Deploy como **Docker Compose**. Coolify gestiona HTTPS, proxy y deploys.
No necesitas nginx-proxy ni Cloudflare.

## Reparto

- **Postgres** → recurso de BD SEPARADO en Coolify (no en el compose). No se borra en redeploys.
- **Redis** → dentro del `docker-compose.prod.yml` (uno solo, compartido por backend/worker/beat).
- **App** (backend, worker, beat, frontend) → el compose.

---

## 1. Crear Postgres (recurso de Coolify, aparte)

1. Coolify → proyecto → **+ New** → **Database** → **PostgreSQL 16**.
2. Volumen persistente automático (sobrevive a redeploys).
3. Activar **Backups** (Scheduled Backups → diario).
4. Copiar la **Connection String interna**.
   > Cambia el prefijo `postgres://` por `postgresql+asyncpg://` para `DATABASE_URL`.

## 2. Desplegar la app (Docker Compose)

1. **+ New** → **Resource** → desde tu repo Git.
2. Build pack: **Docker Compose**.
3. Compose file: `docker-compose.prod.yml`.
4. Coolify detecta los servicios. Asignar **dominios**:
   - `backend` (puerto 8000) → `api.scalia.hacelerix.com`
   - `frontend` (puerto 80) → `scalia.hacelerix.com`
   - `worker`, `beat`, `redis`, `migrate` → sin dominio.

## 3. Variables de entorno (en la UI de Coolify, NO en el repo)

```
DATABASE_URL=postgresql+asyncpg://user:pass@<host-pg-interno>:5432/db
OPENAI_API_KEY=...
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
BRAVE_API_KEY=...
META_APP_ID=...
META_APP_SECRET=...
ALLOWED_ORIGINS=https://scalia.hacelerix.com
VITE_API_URL=https://api.scalia.hacelerix.com
VITE_WS_URL=wss://api.scalia.hacelerix.com
```

> `REDIS_URL` no hace falta: el compose ya apunta a `redis://redis:6379` (servicio interno).

## 4. Migraciones

El servicio `migrate` del compose corre `alembic upgrade head` y termina.
`backend` y `worker` esperan a que termine (`service_completed_successfully`).
Solo aplica migraciones nuevas. NUNCA downgrade.

---

## Redeploy (código nuevo)

`git push` → Coolify rebuild + redeploy.
`migrate` aplica migraciones nuevas. La BD persiste (recurso aparte). Redis persiste (volumen `redis_data`).

## NO HACER

- NO meter Postgres en el compose.
- NO `alembic downgrade`.
- NO borrar el recurso de BD en Coolify (eso sí borra el volumen).
- Verifica que los **Backups** de la BD están activos antes de producción.
