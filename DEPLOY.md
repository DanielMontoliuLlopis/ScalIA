# Despliegue en servidor — Growth OS

## Regla de oro: NUNCA borrar la BD

- El volumen de Postgres es **`external: true`**. `docker compose down -v` **NO** lo borra.
- **NUNCA** correr `alembic downgrade`.
- **NUNCA** usar `DROP` en migraciones.
- Backup **antes** de cada despliegue.

---

## 1. Preparar servidor (una sola vez)

```bash
# Instalar docker + compose plugin (Ubuntu)
curl -fsSL https://get.docker.com | sh

# Crear el volumen de BD A MANO (external → no se borra nunca por accidente)
docker volume create growthos_pgdata

# Copiar entorno y rellenar
cp .env.prod.example .env.prod
nano .env.prod   # poner passwords/keys reales
```

## 2. Primer arranque

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

Orden automático: `postgres` → `migrate` (alembic upgrade head) → `backend`/`worker`/`beat`/`frontend`.

## 3. Actualizar (deploy nuevo código)

```bash
# 1. BACKUP primero (ver abajo)
./backup_db.sh

# 2. traer cambios
git pull

# 3. reconstruir y levantar (el volumen de BD se mantiene)
docker compose -f docker-compose.prod.yml up -d --build
```

`migrate` aplica solo migraciones nuevas. Los datos persisten en el volumen.

---

## Backup / Restore

### Backup

```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U postgres growthOS | gzip > backup_$(date +%F_%H%M).sql.gz
```

### Restore

```bash
gunzip -c backup_XXXX.sql.gz | \
  docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U postgres growthOS
```

---

## Comandos PELIGROSOS — no usar

```bash
docker compose down -v           # intenta borrar volúmenes (el external se salva, pero NO lo uses)
docker volume rm growthos_pgdata # BORRA LA BD. nunca.
alembic downgrade ...            # nunca
```

## Comando seguro para parar

```bash
docker compose -f docker-compose.prod.yml down   # sin -v → datos intactos
```
