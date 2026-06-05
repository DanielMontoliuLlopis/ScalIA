
# Growth OS — Agentic Marketing Platform

## Visión del producto

Plataforma web que actúa como un sistema de **optimización de conversión continua** para negocios digitales.
La campaña es la entrada del ciclo, no el producto. El producto es el ciclo completo:

```
Oferta → Campaña → Leads → Pipeline → Revenue
   ↑                                      |
   └──────── OptimizationAgent ←──────────┘
```

El sistema no solo genera campañas — las mide, aprende y recomienda ajustes en oferta, copy y presupuesto con aprobación del usuario.

El ciclo de trabajo que sigue cualquier media buyer experto: **analiza → lanza → optimiza**. El sistema lo estructura y acelera sin quitarle el control al usuario.

Modelo: **propone → apruebo → ejecuta**. Nunca ejecutar sin aprobación explícita del usuario.

Tipos de negocio soportados:

- `saas` — software B2B, trials, suscripciones (copies de conversión, pain points de herramienta)
- `ecommerce` — tienda online, dropshipping, productos físicos (copies de producto, urgencia, prueba social)
- `services` — consultoría, agencias, freelancers (copies de credibilidad, resultados, proceso)
- `app` — apps móviles/web de consumo (copies de descarga, onboarding, retención)
- `local` — negocio local, restaurantes, tiendas físicas (copies de proximidad, ofertas, reseñas)

---

## Autenticación y Roles de Equipo

### Tiers de suscripción

**Plataforma completa (flujo agéntico end-to-end):**

- `starter` — 1 campaña activa, $99/mes
- `growth` — 5 campañas activas, $299/mes
- `agency` — ilimitadas, $999/mes

**Research Mode (solo research + 6 ángulos, sin funnel — ver Research Export Mode):**

Suscripción mensual con un **tope de escaneos al mes**. Un escaneo = una generación de research (ICP + pain points + 6 ángulos con copy e imagen) para un negocio/audiencia. Prueba gratis sin tarjeta de un escaneo.

- `research_10` — **10 escaneos/mes por €15/mes** (€1,50/escaneo). Para empezar y probar el valor.
- `research_100` — **100 escaneos/mes por €99/mes** (€0,99/escaneo). Para uso intensivo de agencias/expertos.

Se cobra cada mes. El contador de escaneos se **reinicia al inicio de cada ciclo de facturación** y no se acumula (los no usados se pierden). Cada escaneo incluye la vista web del research + export en PDF/JSON sin coste extra. El histórico de ángulos (`angle_performance`) se acumula con cada escaneo mientras la suscripción esté activa y está incluido en ambos planes.

> El Research Mode es la puerta de entrada natural para media buyers de agencia: les das el output más valioso (research + ángulos) sin obligarles a usar el funnel, con ingreso recurrente. El de 100 escaneos/mes es el que rentabiliza el flujo de quien lanza muchas campañas.

### Qué incluye cada plan

Hay **dos líneas de producto** con planes distintos:

1. **Plataforma completa** (`starter`, `growth`, `agency`) — el flujo agéntico end-to-end: research → copy → funnel → ads → leads → optimización.
2. **Research Mode** (`research_10`, `research_100`) — solo el research y los 6 ángulos, con un tope de escaneos al mes. No crea campañas, funnels ni publica ads. Pensado para expertos que ya tienen sus propios sistemas.

#### Plataforma completa — matriz de funcionalidades

| Funcionalidad                                          |     `starter`     | `growth` | `agency` |
| ------------------------------------------------------ | :-----------------: | :--------: | :--------: |
| Campañas activas simultáneas                         |          1          |     5     |     ∞     |
| Precio                                                 | $99/mes  | $299/mes |  $999/mes  |            |
| ResearchAgent (ICP, pain points, 6 ángulos)           |         ✅         |     ✅     |     ✅     |
| CopyAgent (copy + imagen DALL-E)                       |         ✅         |     ✅     |     ✅     |
| Vista de research + export PDF/JSON                    |         ✅         |     ✅     |     ✅     |
| Funnels: instant_form + landing_direct                 |         ✅         |     ✅     |     ✅     |
| Funnels: landing_lm + landing_lm_direct (lead magnet)  |         ✅         |     ✅     |     ✅     |
| LandingAgent + plantillas por business_type            |         ✅         |     ✅     |     ✅     |
| LeadMagnetAgent (PDF con IA)                           |         ✅         |     ✅     |     ✅     |
| EmailAgent — secuencia de 5 emails                    |         ✅         |     ✅     |     ✅     |
| EmailAgent — secuencia WhatsApp                       |         —         |     ✅     |     ✅     |
| CRMAgent (scoring + segmentación)                     |         ✅         |     ✅     |     ✅     |
| MetaPolicyAgent (validación + humanización)          |         ✅         |     ✅     |     ✅     |
| Publicar en Meta (AdsAgent → Graph API)               |         ✅         |     ✅     |     ✅     |
| Testeo A/B clásico                                    |         ✅         |     ✅     |     ✅     |
| **Multi-Angle Testing** (N ángulos en paralelo) |         ✅         |     ✅     |     ✅     |
| OptimizationAgent (recomendaciones cada 24h)           |         ✅         |     ✅     |     ✅     |
| Pipeline de métricas (CPL real, ROAS, show-up, close) |         ✅         |     ✅     |     ✅     |
| Histórico de ángulos (`angle_performance`)         |         ✅         |     ✅     |     ✅     |
| Equipo: invitar usuarios + roles                       |         —         |     —     |     ✅     |
| Multi-cliente + agregación de histórico por agencia  |         —         |     —     |     ✅     |
| Programa Fundadores (precio bloqueado)                 |         ✅         |     ✅     |     ✅     |
| Escaneos extra Research Mode                           |         10         |     30     |    100    |

Resumen del posicionamiento de cada plan:

- **`starter`** — 1 negocio que quiere lanzar de verdad: publica en Meta, lead magnets, secuencia de email, CRM y métricas de pipeline. Testeo A/B clásico.
- **`growth`** — el plan donde vive la diferenciación: **Multi-Angle Testing + OptimizationAgent + histórico de ángulos + WhatsApp**. Para quien optimiza en serio sobre 5 campañas.
- **`agency`** — todo lo anterior, ilimitado, **+ equipo, multi-cliente, agregación de histórico por agencia y Offer Testing**. Para el experto/agencia con varios clientes.

#### Research Mode — planes por escaneos

Estos planes **no crean campañas ni publican ads**. Solo research + ángulos. Suscripción mensual con tope de escaneos; 1 escaneo = 1 generación de research.

| Funcionalidad                                    |          `research_10`          |         `research_100`         |
| ------------------------------------------------ | :-------------------------------: | :-------------------------------: |
| Escaneos al mes                                  |                10                |                100                |
| Precio                                           |             €15/mes             |             €99/mes             |
| Precio por escaneo                               |              €1,50              |              €0,99              |
| Renovación                                      | mensual (se reinicia, no acumula) | mensual (se reinicia, no acumula) |
| ResearchAgent (ICP, pain points, 6 ángulos)     |                ✅                |                ✅                |
| CopyAgent (copy + imagen por ángulo)            |                ✅                |                ✅                |
| Vista de ángulos en la web (ResearchModeScreen) |                ✅                |                ✅                |
| Export PDF / JSON (incluido en cada escaneo)     |                ✅                |                ✅                |
| Histórico de ángulos (`angle_performance`)   |                ✅                |                ✅                |
| Crear campañas / funnels / publicar ads         |                —                |                —                |

> E research sera una pestaña exclusiva a la que tendran acceso todos los usuarios, el resto de pestañas estaran ocultas para los usuarios unicos dell research

### Gating de funcionalidades (implementación)

El control de acceso por plan se centraliza, no se dispersa por los routers:

```python
# app/services/permissions.py — gating central por plan (no existe carpeta app/billing/)
PLAN_FEATURES = {
    "starter":    {"max_campaigns": 1, "publish": True,  "email": True,  "whatsapp": False,
                   "multi_angle": True, "optimization": True, "angle_history": True,
                   "team": False, "scans_per_month": 10},
    "growth":     {"max_campaigns": 5, "publish": True,  "email": True,  "whatsapp": True,
                   "multi_angle": True,  "optimization": True,  "angle_history": True,
                  "team": False, "scans_per_month": 30},
    "agency":     {"max_campaigns": None, "publish": True, "email": True, "whatsapp": True,
                   "multi_angle": True,  "optimization": True,  "angle_history": True,
                   "team": True, "scans_per_month": 100},
    # Research Mode — suscripción mensual con tope de escaneos. 1 escaneo = 1 generación de research.
    "research_10":  {"research_only": True, "scans_per_month": 10,  "price_eur_month": 15, "angle_history": True},
    "research_100": {"research_only": True, "scans_per_month": 100, "price_eur_month": 99, "angle_history": True},
}
```

- El saldo `scans_remaining` se **reinicia al tope del plan en cada ciclo de facturación** (no acumula). Sin saldo → 402 con upsell a `research_100` o esperar al reinicio.
- Export PDF/JSON incluido en el escaneo (no descuenta extra ni cobra aparte).
- Dependencia FastAPI `require_feature("multi_angle")` que devuelve 402/403 si el plan no lo incluye.
- El frontend lee `GET /me/features` y oculta/bloquea con upsell las funciones no disponibles (no las esconde sin más — muestra "Disponible en Growth" para empujar el upgrade).
- El `OrchestratorAgent` respeta el gating: si el plan no tiene `multi_angle`, el `FunnelTypeSelector` no ofrece ese modo.

### Programa Fundadores

Los usuarios con `is_founder=true` obtienen precio bloqueado de por vida al tier que contraten. Se asigna manualmente en el panel de admin.

### Roles de equipo dentro de una cuenta

Una suscripción (account) puede tener múltiples usuarios con roles:

- `owner` — control total, facturación, settings
- `admin` — crear campañas, editar leads, ver métricas
- `member` — crear campañas propias, no editar ajenas
- `viewer` — solo lectura de campañas y leads

El `owner` puede invitar otros usuarios via email. Los usuarios invitados se crean con `parent_account_id` apuntando al owner.

**Campos en User:**

```
role                 string (owner | admin | member | viewer)
parent_account_id    UUID | null   # si es sub-usuario, apunta al dueño
is_founder           bool          # precio bloqueado de por vida
is_superadmin        bool          # acceso al panel /admin (global, no por account)
```

### Superadmin de plataforma

Usuarios con `is_superadmin=true` pueden acceder a `/admin` — panel de gestión global de closers, clientes y comisiones.

---

## Requisito previo — Configuración de empresa

**El usuario debe configurar su empresa antes de crear la primera campaña.**

El `OrchestratorAgent` verifica al inicio de cada conversación que `user_settings` tiene los campos mínimos cubiertos. Si faltan, redirige al usuario a Settings antes de continuar.

Campos mínimos obligatorios:

```
company_name         → nombre del negocio (usado en copies, landings, emails)
business_description → descripción corta de qué hace el negocio (1-2 frases)
business_type        → saas | ecommerce | services | app | local
color_palette        → paleta elegida (determina plantilla visual de landing)
logo_url             → opcional pero recomendado (aparece en landing y emails)
```

Campos recomendados (sin ellos algunas features quedan desactivadas):

```
meta_ad_account_id   → sin esto AdsAgent no puede publicar en Meta
resend_api_key       → sin esto EmailAgent no puede enviar emails
resend_from_email    → sin esto EmailAgent no puede enviar emails
```

El frontend muestra un banner de "configuración incompleta" en el chat si faltan campos obligatorios, con enlace directo a Settings.

---

## Offer Engine — Capa de oferta estructurada

Antes de que `ResearchAgent` actúe, el `OrchestratorAgent` captura la oferta estructurada del negocio. Esto alimenta al `CopyAgent` con la fórmula de valor percibido:

> **valor percibido = (transformación × confianza) / (tiempo + esfuerzo)**

Campos que el Orchestrator extrae (o pregunta si faltan):

```
precio_base          → ej: 997
tipo_oferta          → evergreen | lanzamiento | descuento_limitado | prueba_gratuita
urgencia             → sin_urgencia | fecha_limite | plazas_limitadas | bonus_temporal
garantia             → sin_garantia | satisfaccion | resultados | devolucion_X_dias
transformacion       → string específico (ej: "bajar 10kg en 12 semanas")
```

Estos campos se guardan en el plan y se propagan a todos los agentes. Permiten testear **ofertas distintas** (no solo copies) en campañas A/B paralelas.

---

## Sistema de Closers y Comisiones

**Closers** son comerciales (sales team) que cierran suscripciones para la plataforma. No son clientes.

### Modelo de negocio

1. Un **closer** obtiene un código referral único: `/?ref=CODE`
2. El usuario que se registra con ese código → `User.closer_id = closer_id`
3. Cuando el usuario **paga** (Stripe webhook `invoice.paid`) → se crea automáticamente una `Commission`
4. El closer ve sus comisiones en `/closer-portal` y puede descargar comprobantes

### Comisiones automáticas

Las comisiones se generan **automáticamente** desde el webhook de Stripe (`invoice.paid`), nunca se calculan a mano.

```python
COMMISSION_FIRST_QUOTA = "first_quota"    # 1er pago: 100% de la comisión (ej: €29.70 de €99)
COMMISSION_RECURRING = "recurring"         # pagos 2+: % configurado (default 6%, ej: €5.94 de €99)
```

Cada comisión tiene estado:

- `pending` → generada pero no liquidada
- `paid` → liquidada al closer

### Tabla: `closers`

```
id UUID
full_name         string(200)
email             string(255) unique
phone             string(50) | null
commission_rate   Decimal(5,4)   # default 0.06 = 6% (recurrente)
referral_code     string(40) unique, indexed
is_active         bool           # si false, no puede usar el código
hashed_password   string(255) | null  # para login en closer-portal
created_at, updated_at
```

### Tabla: `commissions`

```
id UUID
closer_id FK → closers.id
user_id FK → users.id
stripe_invoice_id string(100) unique, indexed  # idempotencia
type              string (first_quota | recurring)
base_amount       Decimal(10,2)  # monto del invoice (ej: €99)
commission_amount Decimal(10,2)  # monto comisión (ej: €29.70 o €5.94)
currency          string(10)     # default "eur"
period_start      datetime | null  # período de la suscripción
status            string (pending | paid)
paid_at           datetime | null
created_at, updated_at
```

### Portal del Closer

**Ruta:** `/closer-portal`

- Login con email + password (distinto de usuarios)
- Dashboard mensual:
  - Clientes atribuidos (total, activos)
  - Comisiones por mes: first_quota vs. recurrentes, pending vs. paid
  - Total earned, total pending
- No hay integración con Stripe directo — solo lectura de comisiones ya generadas

**Endpoints:**

```
POST /closer-portal/login          → CloserLoginRequest (email, password)
GET  /closer-portal/me             → CloserMe (info actual)
GET  /closer-portal/dashboard      → CloserDashboard (comisiones por mes)
```

---

## Panel de Administración

**Ruta:** `/admin` (solo superadmins)

Página con 4 tabs:

### Tab 1: Overview

KPIs principales:

- Total usuarios
- Suscripciones activas
- MRR aproximado (suma presupuestos de usuarios activos)
- Closers activos / totales
- Comisiones pendientes
- Comisiones pagadas

### Tab 2: Clientes

Tabla searchable de usuarios:

- Email, nombre, plan, subscription status, es founder
- Closer asignado (name + email)
- MRR individual (según plan y founder status)
- Fecha creación
- Acciones: asignar closer, cambiar plan, activar/pausar

### Tab 3: Closers

Tabla de closers:

- Nombre, email, teléfono
- Commission rate (%)
- Referral code (copiable)
- Clientes atribuidos (count)
- Comisiones pending + paid (resumen)
- Acciones: editar commission_rate, desactivar, resetear password

Botón: "Crear nuevo closer"

- Formulario: full_name, email, phone, initial_commission_rate
- Backend genera referral_code único
- Se envía email de bienvenida con instrucciones (pendiente: email template)

### Tab 4: Comisiones

Tabla de todas las comisiones:

- Closer (name), cliente (email), invoice_id, tipo (first_quota / recurring)
- Base amount, comisión, moneda
- Período
- Status (pending / paid)
- Fecha pago
- Acciones: marcar como paid, revertir a pending

Botón: "Liquidar seleccionadas" — marcar múltiples como paid + generar PDF de comprobante

**Endpoints:**

```
GET  /admin/overview                           → AdminOverview
GET  /admin/clients                             → list[AdminClientRow]
GET  /admin/closers                             → list[CloserRow]
GET  /admin/commissions                         → list[CommissionRow]
POST /admin/closers                             → CloserCreate → CloserCreated
PATCH /admin/closers/:id                        → CloserUpdate
POST /admin/closers/:id/reset-password          → ResetPasswordResponse
POST /admin/clients/:id/assign-closer           → AssignCloserRequest
POST /admin/commissions/:id/mark-paid           → CommissionRow
POST /admin/commissions/liquidate               → LiquidateRequest → LiquidateResponse
```

---

## Narrative Thread — Hilo narrativo único

**Concepto central de conversión.** El mayor asesino de campañas no es el copy malo — es el *message mismatch*: el anuncio promete X, la landing dice Y, los emails hablan de Z. El usuario se desorienta y rebota aunque cada pieza sea buena por separado.

El `narrative_thread` es un objeto que se construye después de que `CopyAgent` genera el hook principal, y se propaga a todos los agentes posteriores (`LandingAgent`, `EmailAgent`). Garantiza que todas las piezas hablen el mismo idioma.

```python
narrative_thread = {
    "hook":          "Baja 10kg en 12 semanas sin pasar hambre",  # del CopyAgent (copies[0].hook)
    "transformacion": "bajar 10kg en 12 semanas",                  # del Offer Engine
    "mecanismo":     "sin dieta, solo ajustando horarios",         # inferido del negocio
    "garantia":      "devolucion_30_dias",                         # del Offer Engine
    "urgencia":      "plazas_limitadas",                           # del Offer Engine
    "precio":        997                                            # del Offer Engine
}
```

> En modo Multi-Angle Testing, cada ángulo testeado mantiene su propio `hook` pero **comparte el resto del narrative_thread** (transformación, mecanismo, garantía, urgencia, precio). El message match se valida por ángulo: la landing y los emails se construyen sobre el hook del ángulo ganador una vez consolidado.

### Reglas de propagación

| Agente                  | Cómo usa el narrative_thread                                                                              |
| ----------------------- | ---------------------------------------------------------------------------------------------------------- |
| `CopyAgent`           | Genera el `hook` principal — fuente de verdad del hilo                                                  |
| `LandingAgent (lm)`   | Headline usa el hook; subheadline explica el mecanismo                                                     |
| `LandingAgent (sale)` | H1 = hook exacto; precio + garantía en posición prominente; urgencia en CTA                              |
| `EmailAgent`          | Email #1 referencia el hook del anuncio; emails 2-5 avanzan hacia la landing de venta sin salirse del hilo |

### LandingAgent (sale) — regla crítica

La landing de venta se construye **desde el hook del anuncio hacia abajo**, no desde el contexto genérico del plan. El usuario que llega ya escuchó la promesa — la landing debe continuarla, no reiniciarla.

Prompt obligatorio para `landing_subtype == "sale"`:

```
El usuario llegó porque el anuncio prometía: "{hook}"
Ha sido nutrido por emails que desarrollaban: "{mecanismo}"
Esta landing CIERRA la venta. Debe:
- Retomar el hook exacto como H1 (no parafrasear)
- Justificar el precio {precio} con la transformación {transformacion}
- Mostrar la garantía {garantia} como red de seguridad
- Generar urgencia real con {urgencia}
```

### Validación de message match (determinista, sin LLM)

Se ejecuta como paso de validación antes de mostrar la aprobación al usuario:

```python
def check_message_match(plan, landing_lm, landing_sale, emails) -> list[str]:
    warnings = []
    hook_words = set(plan.narrative_thread["hook"].lower().split())
  
    if not any(w in landing_lm.headline.lower() for w in hook_words):
        warnings.append("Landing de captura no refleja el hook del anuncio")
  
    if landing_sale and not any(w in landing_sale.headline.lower() for w in hook_words):
        warnings.append("Landing de venta no refleja el hook del anuncio")
  
    if plan.urgencia != "sin_urgencia" and landing_sale:
        if not mentions_urgency(landing_sale.content):
            warnings.append("La oferta tiene urgencia pero la landing de venta no la menciona")
  
    return warnings
```

Los `warnings` aparecen en el panel de aprobación. El usuario los ve antes de aprobar y puede pedir regeneración.

---

## Flujo de campaña completo

> **Entrada: Wizard visual, NO chat.** La creación de campañas ya **no usa chat**. El usuario rellena un **wizard por pasos** (`NewCampaign.tsx`, ruta `/campaigns/new`): negocio (de Settings) → oferta (precio, transformación, garantía) → audiencia + presupuesto + país → acción post-conversión. Al enviar, `POST /plans/wizard` construye un briefing estructurado y se lo pasa al `OrchestratorAgent` con `allow_clarification=False` (una sola llamada LLM para inferir `post_conversion_goal`, `tipo_oferta`, `urgencia`, título y steps). El plan se crea en `pending_approval` y el usuario lo gestiona en `PlanWorkspace` (`/plan/:id`, renderiza `ApprovalCard`). El backend del chat (`chat.py`, modelos `chat_*`) sigue existiendo pero ya no se usa desde el frontend.

```
Wizard de creación (NewCampaign → POST /plans/wizard)
  → recoge: negocio, oferta, audiencia, presupuesto, acción post-conversión
  → OrchestratorAgent (allow_clarification=False) infiere campaign_type/post_conversion_goal/oferta y crea el plan

ResearchAgent         → pain points reales (Brave Search API), ICP analysis, 6 ángulos de copy
    ↓
CopyAgent             → copies de texto + imagen (DALL-E 3) con variantes A/B
                        (en modo multi_angle: 1 copy por ángulo testeado, saldra una lista con los copies y se seleccionara con un checkbox los angulos que incluira la campaña)
    ↓
OrchestratorAgent     → pregunta al usuario: ¿qué tipo de funnel quieres?
                        [1] Formulario instantáneo Meta (Lead Ad)
                        [2] Landing directa (venta directa → pricing/pago)
                        [3] Landing lead magnet → email nurturing → URL externa de venta
                            (sub-opción: ¿cerrar por llamada o por pago directo?)
                        [4] Landing lead magnet + landing de venta propia
                            (LM captura → emails nutren → landing de venta generada)
                            (sub-opción: ¿cerrar por llamada o por pago directo?)
                      → pregunta también: ¿modo de testeo?
                        [A/B clásico]   2 variantes de copy en 1 ad set
                        [Multi-Angle]   N ángulos en paralelo (1 ad set por ángulo)
    ↓ (según funnel_type)

── instant_form ──────────────────────────────────────────────────────────────
AdsAgent              → genera JSON Lead Ad Meta con formulario nativo
                        campos: nombre, email, empresa, teléfono (configurables)
                        sin landing, sin LandingAgent
──────────────────────────────────────────────────────────────────────────────

── landing_direct ────────────────────────────────────────────────────────────
LandingAgent          → genera 1 landing (variantes A/B) de venta directa
                        sin form — CTA → redirect_url (pricing o pago)
AdsAgent              → 1 campaign → 1 ad set → 2 ads (A/B)
                        (o N ad sets si ab_mode = multi_angle)
──────────────────────────────────────────────────────────────────────────────

── landing_lm ────────────────────────────────────────────────────────────────
LandingAgent          → 1 landing de captura (variantes A/B)
                        form: nombre, email, empresa, teléfono
                        entrega recurso (PDF, guía, etc.) tras submit
LeadMagnetAgent       → genera PDF del lead magnet con IA (estructura + contenido)
                        entrega como adjunto URL en email #1
EmailAgent            → secuencia nurturing 5 emails + página de gracias
                        email #1: entrega lead magnet inmediatamente
                        emails 2-5: nutren hacia URL externa de venta
                        (sale_type=call → Calendly URL | sale_type=payment → URL pago)
CRMAgent              → scoring y segmentación de leads capturados
AdsAgent              → 1 campaign → 1 ad set → 2 ads apuntando a landing LM A/B
                        (o N ad sets si ab_mode = multi_angle)
                        (NO hay segunda landing de venta — la venta es URL externa)
──────────────────────────────────────────────────────────────────────────────

── landing_lm_direct ────────────────────────────────────────────────────────
LandingAgent (lm)     → landing de captura (variantes A/B)
                        form: nombre, email, empresa, teléfono
                        entrega recurso (PDF, guía, etc.) tras submit
LandingAgent (sale)   → landing de venta (variantes A/B)
                        sin form — CTA → llamada (Calendly) o pago directo
                        los emails de la secuencia apuntan a esta landing
LeadMagnetAgent       → genera PDF del lead magnet con IA
EmailAgent            → secuencia nurturing 5 emails + página de gracias
                        email #1: entrega lead magnet inmediatamente
                        emails 2-5: nutren hacia landing de venta generada
CRMAgent              → scoring y segmentación de leads capturados
AdsAgent              → 1 campaign → 1 ad set → 2 ads apuntando a landing LM A/B
                        (o N ad sets si ab_mode = multi_angle)
──────────────────────────────────────────────────────────────────────────────

Aprobación usuario    → revisa JSON completo en forma de formulario, puede editar todos los campos
    ↓
Publicación           → AdsAgent POST a Meta Graph API
    ↓
Métricas              → Worker de snapshots (cada 1h) guarda Meta Insights en
                        `metric_snapshots`. El Dashboard lee de BD, NO pega a Meta.
                        (NO existe AnalyticsAgent — ver "Sistema de Métricas y Analytics")
    ↓
Alertas               → reglas deterministas sobre snapshots (CPL spike, ROAS<1,
                        gasto sin leads, CTR drop) → `metric_alerts`
    ↓
Optimización          → OptimizationAgent (cada 24h) recomienda redistribuir
                        presupuesto a nivel de ángulo y creative
```

---

## Multi-Angle Testing (MAT) — Testeo de ángulos en paralelo

**Concepto de optimización de mensaje.** El testeo A/B clásico (2 variantes de copy en un mismo ad set) es conservador: solo te dice cuál de dos copies funciona mejor, pero ambos pueden partir del mismo ángulo equivocado. Un media buyer experto no busca "el mejor de dos copies" — busca **qué ángulo de mensaje resuena con la audiencia**.

El `ResearchAgent` ya genera **6 ángulos de copy** (dolor, aspiración, miedo_urgencia, social_proof, curiosidad, credibilidad). En modo Multi-Angle se lanzan varios (o los 6) en paralelo con presupuesto mínimo equitativo, se mide el rendimiento real **por ángulo**, y el `OptimizationAgent` redistribuye el presupuesto hacia los ganadores — no solo 1 o 2.

Es el ciclo **analiza → lanza → optimiza** aplicado a nivel de mensaje, no de creative.

### Estructura de campaña

| Modo (`ab_mode`) | Estructura Meta                                               |
| ------------------ | ------------------------------------------------------------- |
| `ab_classic`     | 1 campaign → 1 ad set → 2 ads (variantes A/B de un ángulo) |
| `multi_angle`    | 1 campaign → N ad sets (1 por ángulo) → 1-2 ads cada uno   |

En `multi_angle`, cada ad set representa **un ángulo distinto** del ResearchAgent. Meta distribuye la entrega entre ad sets y el sistema mide CTR, CPL y ROAS por ángulo.

El `CopyAgent` genera, para cada ángulo seleccionado, **un copy + una imagen DALL-E propia** (no solo variantes A/B de texto de uno solo). Cada ángulo necesita su creative visual coherente con su mensaje: el ángulo de "dolor" pide una imagen distinta a la de "aspiración" o "social_proof". El prompt de imagen se construye desde el `hook` del ángulo + el `business_type`, de modo que texto e imagen empujen el mismo ángulo. Así el test no mezcla señal de copy y señal de imagen — cada ad set es un paquete coherente.

El usuario elige cuántos ángulos testear (recomendado: 3-6) en el `FunnelTypeSelector` o en un selector dedicado tras la elección de funnel. Más ángulos = más señal, pero requiere mayor presupuesto total para que cada ad set salga del aprendizaje de Meta.

### Fases de redistribución de presupuesto

```
Fase 1 — Exploración (días 1-14)
  Todos los ángulos activos con presupuesto mínimo equitativo.
  Se deja que Meta optimice la entrega dentro de cada ad set.
  No se toca nada hasta acumular señal estadística mínima.

Fase 2 — Consolidación (día ~15)
  OptimizationAgent identifica los 2-3 ángulos ganadores (por CTR/CPL/ROAS).
  Propone: redistribuir presupuesto hacia ganadores + pausar perdedores.
  El usuario aprueba o rechaza (modelo propone → apruebo → ejecuta).

Fase 3 — Escalado (día 15+)
  Solo quedan los ángulos rentables, con el presupuesto concentrado.
  El narrative_thread se fija sobre el hook del ángulo ganador.
  LandingAgent y EmailAgent se alinean a ese hook si aún no estaban generados.
```

### Umbrales de señal mínima y significancia

Antes de declarar ganador/perdedor, cada ad set (ángulo) debe superar un mínimo de señal para evitar decisiones sobre ruido:

```python
MIN_IMPRESSIONS_PER_ANGLE = 3000   # impresiones mínimas antes de evaluar
MIN_SPEND_PER_ANGLE       = 30     # € mínimo gastado antes de evaluar
```

Si un ángulo no alcanza el mínimo, el OptimizationAgent lo marca como `insufficient_data` y no lo pausa ni escala todavía.

**Significancia, no solo umbrales.** Superar el mínimo de impresiones no basta: dos ángulos pueden estar tan cerca que la diferencia sea ruido. Antes de declarar un ganador, el OptimizationAgent comprueba que la diferencia entre el ángulo líder y el resto sea estadísticamente concluyente. MVP: test de proporciones simple (z-test de dos colas) sobre la tasa de conversión (CTR o CR), con `p < 0.05` como corte.

```python
def is_significant(angle_a, angle_b, alpha=0.05) -> bool:
    # z-test de dos proporciones (conversions / impressions)
    # devuelve True solo si la diferencia es concluyente al nivel alpha
    ...

# Estados posibles de un ángulo según señal:
#   insufficient_data → no alcanza MIN_IMPRESSIONS / MIN_SPEND
#   inconclusive      → alcanza el mínimo pero la diferencia no es significativa
#   winner / loser    → diferencia significativa, decisión recomendable
```

Cuando dos ángulos están cerca pero aún no son distinguibles, la recomendación es **"diferencia aún no concluyente — seguir testeando"**, no un ganador prematuro. Esto evita el error clásico de matar un ángulo por azar, justo lo que un buen media buyer detecta a ojo. No hace falta un test bayesiano completo en el MVP, pero sí marcar explícitamente el estado `inconclusive`.

### Angle × Offer matrix

El Multi-Angle Testing se cruza con el **Offer Engine** (Capa 5 — Offer Testing). A veces el problema no es el ángulo sino la oferta. Cuando ambos modos están activos:

```
matriz = ángulos (N) × ofertas (M)
```

El OptimizationAgent puede recomendar consolidar por la combinación ganadora `(ángulo, oferta)`, no solo por una de las dos dimensiones. Para evitar explosión combinatoria, se recomienda limitar a 3 ángulos × 2 ofertas como máximo en una sola campaña de test.

### Campos en Plan (extensión MAT)

```
ab_mode              string (ab_classic | multi_angle)  # default ab_classic
angles_tested        JSONB []  # ángulos en test, ej:
                               # [{"angle": "dolor", "ad_set_id": "...", "hook": "...",
                               #   "image_url": "https://...",   # imagen DALL-E propia del ángulo
                               #   "budget_share": 0.166, "ctr": null, "cpl": null,
                               #   "roas": null, "status": "active"}]
                               # status: active | winner | loser | paused
                               #         | insufficient_data | inconclusive
num_angles           int       # cuántos ángulos se testean (2-6)
```

### Histórico de ángulos — `angle_performance` (activo a largo plazo)

El valor compuesto de la plataforma no está en una campaña suelta, sino en lo que **aprende campaña tras campaña**. `angles_tested` vive dentro de cada `Plan`, pero los resultados se agregan a una tabla persistente que mejora con el uso.

Esto convierte la plataforma en algo defendible: un wrapper de GPT puede generar ángulos, pero no tiene tu data acumulada de qué ángulo gana para qué tipo de negocio. Para un experto de agencia es oro: *"según 40 campañas de SaaS, el ángulo de credibilidad gana el 70% de las veces."*

#### Tabla: `angle_performance`

```
id UUID
user_id FK → users.id            # opcional: histórico por cuenta/agencia
account_id UUID | null           # agregación a nivel de agencia (parent_account_id)
plan_id FK → plans.id
business_type     string         # saas | ecommerce | services | app | local
angle             string         # dolor | aspiracion | miedo_urgencia | social_proof | curiosidad | credibilidad
tipo_oferta       string | null  # cruce opcional con Offer Engine
impressions       int
clicks            int
leads             int
spend             Decimal(10,2)
ctr               Decimal(6,4)
cpl               Decimal(10,2) | null
roas              Decimal(8,2) | null
result            string         # winner | loser | inconclusive
period_start      datetime
period_end        datetime | null
created_at, updated_at
```

- Se escribe cuando una campaña multi_angle consolida (fase 2/3) o al cerrar el ciclo de optimización.
- **Alimenta de vuelta al sistema:** el `ResearchAgent` / `CopyAgent` pueden priorizar ángulos con buen histórico para ese `business_type`, y el `FunnelTypeSelector` puede pre-seleccionar los ángulos recomendados con un badge "histórico: 70% win rate".
- Se agrega a nivel de agencia (`account_id`) para el tier `agency`: un experto con varios clientes ve patrones cruzados.

**Endpoints:**

```
GET /analytics/angle-performance              → list[AnglePerformanceRow]
    ?business_type=saas&angle=credibilidad     # filtros opcionales
GET /analytics/angle-performance/summary      → win rate por ángulo × business_type
```

---

## Research Export Mode — Salida temprana de research + ángulos

**Para el perfil que no quiere el flujo completo.** Un media buyer experto de agencia ya tiene sus landings, sus emails y sus sistemas — lo que más le interesa es el output del `ResearchAgent` + `CopyAgent` (pain points reales, ICP, los 6 ángulos con sus hooks). Obligarle a generar funnel completo es fricción innecesaria.

`research_export` no es un producto separado — es un **punto de salida temprano dentro del mismo flujo**. Tras completar Research + Copy, el usuario puede:

- continuar al `FunnelTypeSelector` (flujo normal), **o**
- ver el research + los 6 ángulos **en la propia web**, y exportarlos cuando quiera.

Esto cierra al experto sin partir el producto en dos ni diluir el foco.

### Vista web (no solo export)

Los ángulos **se visualizan en la plataforma** en una vista dedicada (`ResearchModeScreen.tsx`), no se entregan únicamente como archivo. El usuario navega los 6 ángulos de forma interactiva (cada uno con su hook, copy e imagen), revisa el ICP y los pain points, y desde ahí decide:

- copiar un ángulo concreto al portapapeles,
- **exportar todo** (PDF o JSON) con un botón de acción,
- o continuar al funnel completo. si el plan y el nº de campañas lo permiten

La exportación es una **acción dentro de la vista**, no el único destino. Así el experto explora y se queda con lo que necesita aunque no descargue nada.

### Qué incluye (vista y export)

```
- ICP analysis (ResearchAgent)
- Pain points reales con fuentes (Brave Search)
- Los 6 ángulos: nombre, hook, copy completo, imagen DALL-E (si se generó)
- Lenguaje de audiencia / objeciones detectadas
- (si hay histórico) win rate por ángulo para ese business_type
```

### Formatos de export

```
PDF  → documento limpio, listo para compartir con el cliente de la agencia
JSON → para importar en sus propias herramientas
```

### Flujo

```
ResearchAgent + CopyAgent completan
    ↓
plan → awaiting_funnel_choice
    ↓
FunnelTypeSelector ofrece: "Solo quiero el research y los ángulos"
    ↓ (si se elige)
plan → research_view  (estado: research disponible, sin funnel)
    ↓
ResearchModeScreen.tsx → muestra ICP + pain points + 6 ángulos interactivos
    ↓ (acción opcional del usuario)
"Exportar" → POST /plans/:id/export → PDF/JSON en Cloudinary → URL de descarga
    ↓ (si exporta queda registrado)
export_url poblado; el plan permanece en research_view (re-exportable)
```

> El estado se llama `research_view` (no terminal "exported"): el research queda accesible en la web indefinidamente y se puede re-exportar o, más adelante, continuar al funnel.

### Research Library — pestaña propia + generación directa

Además de la salida temprana desde el chat, el research tiene una **pestaña propia** (`/research`, `ResearchLibrary.tsx`) accesible a **todos los usuarios** (CLAUDE.md: el research es pestaña para todos; para usuarios `research_only` el resto de pestañas se ocultan — solo ven Research + Ajustes). Es una **librería**: tarjetas de todos los research generados (`research_export == true`), con badge de estado (`executing` → "Generando…" / `research_view` → "Listo"). Al hacer clic en una tarjeta lista se abre un **drawer** sobre la librería que renderiza `ResearchModeScreen`.

El botón **"Generar nuevo"** abre `ResearchGenerateModal.tsx` (pide **audiencia + objetivo**; el campo audiencia lleva un placeholder con el cliente derivado de Settings, editable en texto plano) y **ejecuta los agentes directamente**, sin pasar por chat, creative-choice ni funnel-choice:

```
POST /plans/research  (ResearchGenerateRequest)
    ↓ require_feature("research_export") + consume_scan() (descuenta 1 escaneo a TODOS los tiers)
    ↓ negocio desde UserSettings (o override en el body); 422 si perfil incompleto
crea Plan (status=executing, research_export=true, ab_mode=multi_angle, num_angles=6,
           steps server-side: ResearchAgent → CopyAgent/generate_multi_angle_copy)
    ↓ Celery task generate_research (no usa _execute_plan_sync — sin pausas)
corre ResearchAgent → CopyAgent (6 ángulos con imagen)
    ↓ al terminar: plan.status = research_view
WS plan_research_view → la tarjeta pasa a "Listo"
```

**Campos en Plan:**

```
research_export      bool    # default false; si true, el plan se queda en modo research (sin funnel)
export_url           string | null   # última URL de export generada (si el usuario exportó)
```

**Endpoints:**

```
POST /plans/research          → ResearchGenerateRequest (target_customer, objective?,
                                business_description?, business_type?) → PlanResponse
                                (gating research_export + consume_scan; lanza generate_research)
GET  /plans/:id/research      → ResearchView (ICP, pain points, 6 ángulos con copy+imagen, histórico)
POST /plans/:id/export        → ExportRequest (format: pdf|json) → ExportResponse (url)
```

### Componente frontend: `ResearchModeScreen.tsx`

Vista dedicada del modo research. Diseño editorial premium (tema oscuro cálido, tipografía serif de carácter + grotesk, un único acento de marca), pensado para el perfil media buyer/agencia — sin estética genérica.

Estructura:

```
ResearchModeScreen
├── Hero          → kicker "Research Mode" + claim + descripción
├── Entregable    → ICP + pain points + "6 ángulos: copy + imagen"
├── Ángulos       → 6 chips interactivos (dolor, aspiración, miedo_urgencia,
│                   social_proof, curiosidad, credibilidad)
│                   → al seleccionar, muestra hook + copy + imagen del ángulo
│                   → botón "copiar ángulo" por cada uno
├── Acciones      → toggle formato (PDF / JSON) + botón "Exportar"
└── Histórico    bloque "win rate por ángulo × business_type" (incluido en ambos planes)
└── Saldo        escaneos restantes del mes + fecha de reinicio + upsell a research_100
```

- Cada generación de research descuenta 1 escaneo del saldo mensual del usuario (`research_10` / `research_100`).
- El saldo se reinicia al tope del plan en cada ciclo de facturación (no acumula).
- La vista web y el export (PDF/JSON) están incluidos en el escaneo — no hay cobro extra por exportar.
- El bloque de histórico de ángulos se muestra en ambos planes (gana valor con el volumen de escaneos).
- Se renderiza cuando el plan está en `research_view` (sustituye al spinner/funnel en el flujo).

> **Pricing (suscripción mensual por escaneos).** Un escaneo = una generación de research (ICP + pain points + 6 ángulos con copy e imagen). Dos planes, se cobra cada mes:
>
> - `research_10` — 10 escaneos/mes por €15/mes (€1,50/escaneo)
> - `research_100` — 100 escaneos/mes por €99/mes (€0,99/escaneo)
>
> El contador se reinicia cada ciclo y no acumula. El histórico de ángulos (`angle_performance`) se acumula con cada escaneo y está incluido en ambos planes. Ver sección Tiers de suscripción.

---

## Stack

### Backend

* **FastAPI** (Python 3.11+) con async/await en todo
* **SQLAlchemy 2.0** + **Alembic** para migraciones
* **PostgreSQL** como fuente de verdad
* **Redis** para colas de tareas, caché y pub/sub de WebSocket
* **Celery** para agentes que corren en background
* **OpenAI Python SDK** (`openai>=1.30`) para todos los agentes (modelo `gpt-4o`)
* **Pydantic v2** para todos los schemas

### Frontend

* **React 18** + **Vite** + **TypeScript**
* **TailwindCSS** para estilos
* **React Router v6** para rutas
* **Zustand** para estado global de UI (NO Redux)
* **WebSockets** nativos para actualizaciones en tiempo real

### Infraestructura

* **Docker Compose** para desarrollo local
* **Railway o Render** para producción
* **Resend** para emails transaccionales y secuencias
* **Brave Search API** para investigación de mercado en ResearchAgent

> ⚠️ **No se usa Vercel** para landing pages. Las landings se sirven desde el propio frontend en rutas `/landing/:id` y `/landing/:id?v=b`.

---

## Arquitectura de agentes

### Orquestador

**`OrchestratorAgent`** — el cerebro que convierte el briefing en un plan.

* Se invoca desde `POST /plans/wizard` (el wizard visual) con `allow_clarification=False` — recibe el briefing estructurado ya completo, no conversa. (El chat fue eliminado por completo: ya no existen `routers/chat.py`, `schemas/chat.py`, ni los modelos `chat_session`/`chat_message`. Las tablas `chat_sessions`/`chat_messages` quedan en la BD sin uso — no se borran por la política de "no DROP en migraciones".)
* Parsea la intención y extrae (o infiere si falta):
  - ¿Qué negocio es y qué hace?
  - ¿Presupuesto mensual?
  - ¿Audiencia objetivo?
* Decide el `post_conversion_goal` adecuado al negocio. No lo pregunta — lo infiere.
* Crea el plan inicial con Research + Copy. Tras completar CopyAgent, el plan pasa a estado `awaiting_funnel_choice` — el frontend muestra el form de selección de funnel en el modal de agentes.
* Captura el `ab_mode` (ab_classic | multi_angle) y `num_angles` junto con la elección de funnel. En `multi_angle` instruye al CopyAgent para generar un copy por ángulo.
* Cuando el usuario envía su elección (POST `/plans/:id/funnel-choice`), el Orchestrator añade los steps restantes y el plan continúa ejecución.
* Incluye `funnel_type`, `sale_type`, `campaign_type`, `post_conversion_goal`, `post_conversion_url`, `redirect_url` y `ab_mode` en todos los steps del plan
* Si falta información crítica usa `request_clarification`
* NUNCA ejecuta acciones reales — solo coordina y propone

### Agentes especializados

| Agente                | Responsabilidad                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Estado                                                               |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `ResearchAgent`     | Búsqueda Brave (pain points, competidores, lenguaje audiencia) + ICP analysis + 6 ángulos de copy (dolor, aspiración, miedo_urgencia, social_proof, curiosidad, credibilidad) + análisis con GPT                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | ✅ Implementado                                                      |
| `CopyAgent`         | Copies de texto para Meta Ads, landing pages y emails. Imágenes con DALL-E 3. En modo `multi_angle` genera 1 copy **+ 1 imagen DALL-E propia por cada ángulo** seleccionado (cada ángulo es un paquete texto+imagen coherente, no solo variantes A/B de uno). Su output alimenta también el `research_export`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | ✅ Implementado (multi_angle + 1 imagen DALL-E por ángulo)      |
| `LandingAgent`      | Genera contenido A/B y lo guarda en DB.`lm`: form captura + entrega recurso. `sale`: CTA → `redirect_url` sin form. En `landing_lm_direct` genera ambos subtipos (lm + sale). No se invoca si `funnel_type=instant_form`. **Selecciona plantilla visual** según `business_type` + `tipo_oferta` (ver sección Plantillas de Landing). Inyecta contenido generado en la plantilla — nunca genera HTML desde cero.                                                                                                                                                                                                                                                                                                                                                                                                                                    | ✅ Implementado                                                      |
| `AdsAgent`          | Genera JSON campaña Meta con Graph API v23.0. Si `instant_form`: Lead Ad con form nativo (sin URL). Si `landing_*`: con `ab_classic` → 1 campaign → 1 ad set → 2 ads A/B; con `multi_angle` → 1 campaign → N ad sets (1 por ángulo) → 1-2 ads cada uno. Presupuesto mensual ÷ 30 = diario (en multi_angle se reparte equitativo entre ad sets en fase 1). Intereses desde ResearchAgent. Publica cuando el usuario aprueba.                                                                                                                                                                                                                                                                                                                                                                                                                               | ✅ Implementado (multi_angle: N ad sets por ángulo)                              |
| `LeadMagnetAgent`   | Genera el PDF del lead magnet con IA. Estructura: portada + 5-8 secciones + CTA final hacia URL post-conversión. Solo se invoca si `funnel_type ∈ {landing_lm, landing_lm_direct}`. Sube PDF a Cloudinary y guarda URL en `lead_magnets`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | ✅ Implementado                                                      |
| `CRMAgent`          | Clasifica leads capturados con scoring 0-100 basado en form_fields (empresa, num_empleados, urgencia, cargo, presupuesto). Asigna segmento:`hot` ≥70, `warm` 40-69, `cold` <40. Sin LLM — reglas deterministas + rubrica por business_type.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | ✅ Implementado                                                      |
| `EmailAgent`        | Genera secuencia de 5 emails de nurturing + secuencia de 5 mensajes WhatsApp + contenido de página de gracias. Ambas secuencias se adaptan a `post_conversion_goal`. Email enviado vía Resend. WhatsApp enviado vía Meta Cloud API (usa `meta_access_token` + `whatsapp_phone_number_id` de Settings). WhatsApp solo se dispara si el lead tiene teléfono. Soporta: `schedule_meeting`, `free_trial`, `demo_request`, `download`, `thank_you_only`, `community`, `pricing_page`                                                                                                                                                                                                                                                                                                                                                                    | ✅ Implementado                                                      |
| `MetaPolicyAgent`   | Valida copies contra políticas de Meta Ads (claims de salud, targeting rules, ratio texto/imagen). Humaniza copy generado por IA. Se ejecuta antes de AdsAgent. En multi_angle valida cada ángulo por separado.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | ✅ Implementado                                                      |
| `OptimizationAgent` | Corre en background cada 24h (Celery beat 86400s). Reglas deterministas a nivel de creative Y de ángulo: copy_refresh (CTR<0.5% con >5k impresiones), audience_expand (CPM>€25 con >€50 gasto), budget_increase (ROAS>3x con <€300 gasto), pause_campaign (€50+ sin leads),**angle_redistribute** (en multi_angle: concentra presupuesto en ángulos ganadores y pausa perdedores tras señal mínima Y significancia estadística). Cada recomendación incluye un **`reasoning` en lenguaje de media buyer** que explica el porqué con números ("ángulo dolor: CTR 0.3% tras 4k impresiones vs. media 0.8% — la audiencia no conecta con el problema planteado"), nunca una caja negra. LLM para análisis narrativo de oferta y copy. Recomendaciones con aprobación en `recommendations` table. Ejecuta via Meta Graph API tras aprobación. | ✅ Implementado (angle_redistribute + z-test + reasoning + offer_test_consolidate) |

### Flujo de aprobación

```
usuario → OrchestratorAgent → Plan (pending_approval)
                                    ↓
                          usuario revisa en UI
                                    ↓
                       aprueba / rechaza / edita
                                    ↓
              approved → Celery ejecuta agentes en orden
              rejected → Orchestrator regenera con feedback
```

### Comunicación en tiempo real

```
Worker (Celery) → Redis pub/sub → Backend subscriber → WebSocket → Frontend
```

Todos los eventos de tareas y planes se emiten por Redis pub/sub para que el worker y el backend no compartan estado en memoria.

### Estado de tareas en DB

Cada `AgentTask`: `pending` → `running` → `completed` / `failed`

Cada `Plan`:

```
pending_approval
  → approved / rejected
  → executing
    → pending_copy_approval  (CopyAgent generó, esperando aprobación del usuario)
    → approved / executing
    → awaiting_creative_choice  (usuario elige tipo creativo: image_ai, upload, video, etc.)
    → executing
    → awaiting_funnel_choice  (CopyAgent completó, elige tipo funnel)
    → research_view  (modo research: ICP + 6 ángulos visibles en web, exportable, sin funnel)
    → approved / executing
    → pending_ads_approval  (AdsAgent generó creatives, esperando aprobación)
    → approved / executing
    → done
```

Los estados `pending_copy_approval` y `pending_ads_approval` permiten que el usuario revise y apruebe antes de continuar ejecución.

### Flujo UI — elección de funnel (modal de agentes)

Cuando el plan pasa a `awaiting_funnel_choice`, el modal `AgentActivityFeed` renderiza el componente `FunnelTypeSelector` en lugar del spinner de siguiente tarea.

```
FunnelTypeSelector
├── Opción 1: "Formulario instantáneo Meta"
│     descripción: "El usuario llena el form sin salir de Meta. Ideal para leads rápidos."
│
├── Opción 2: "Landing de venta directa"
│     descripción: "Una página que lleva al usuario directo a tu pricing o checkout."
│
├── Opción 3: "Landing lead magnet + email nurturing"
│     descripción: "Entrega un recurso gratis, nutre por email y cierra con tu URL de venta."
│     sub-form si se elige:
│       ● Cerrar por llamada (Calendly)   → sale_type: "call"   → input: URL Calendly
│       ● Cerrar por pago directo          → sale_type: "payment" → input: URL de pago
│
├── Opción 4: "Lead magnet + landing de venta propia"
│     descripción: "Captura con recurso gratis, nutre por email y cierra en una landing que generamos nosotros."
│     sub-form si se elige:
│       ● Cerrar por llamada (Calendly)   → sale_type: "call"   → input: URL Calendly
│       ● Cerrar por pago directo          → sale_type: "payment" → input: URL de pago
│
└── Modo de testeo (aplica a cualquier funnel con landing/ads):
      ● A/B clásico   → ab_mode: "ab_classic"  → 2 variantes de copy de 1 ángulo
      ● Multi-Angle   → ab_mode: "multi_angle" → selector de nº ángulos (2-6)
            descripción: "Testea varios ángulos en paralelo y concentra presupuesto en los ganadores."

(salida temprana, fuera del flujo de funnel)
└── "Solo quiero el research y los ángulos"
      → research_export: true → plan pasa a research_view → muestra ResearchModeScreen
      descripción: "Explora el ICP y los 6 ángulos en la web. Expórtalos en PDF o JSON cuando quieras."
```

Al confirmar → `POST /plans/:id/funnel-choice` con `{ funnel_type, sale_type?, redirect_url?, ab_mode, num_angles? }` → backend activa steps restantes → plan vuelve a `executing`.

### Flujo UI — selección de creative (modal de agentes)

Cuando el plan pasa a `awaiting_creative_choice`, el modal renderiza `CreativeChoiceSelector`:

```
CreativeChoiceSelector
├── Opción 1: "Imagen generada por IA (DALL-E 3)"
│     descripción: "Generamos una imagen única para tu anuncio"
│     creative_type: "image_ai"
│
├── Opción 2: "Subir mi propia imagen"
│     descripción: "Usa una imagen que ya tienes"
│     creative_type: "image_upload"
│     input: file upload
│
├── Opción 3: "Subir video"
│     descripción: "Video de promoción o demostración"
│     creative_type: "video_upload"
│     input: file upload
│
├── Opción 4: "Reel de Instagram"
│     descripción: "Video vertical corto para reels"
│     creative_type: "reel_upload"
│     input: file upload
│
└── Opción 5: "Post de Meta"
      descripción: "Anuncio sin imagen (solo texto + link)"
      creative_type: "meta_post"
```

Al confirmar → `POST /plans/:id/creative-choice` con `{ creative_type, uploaded_file? }` → backend continúa ejecución a AdsAgent.

---

## Dynamic Creative Optimization (DCO)

El `CopyAgent` genera variantes A y B de copy (modo `ab_classic`) o un copy por ángulo (modo `multi_angle`). El `AdsAgent` crea los ads correspondientes y los publica en Meta para testing automático.

**Campos en Plan:**

```
creative_type        string (image_ai | image_upload | video_upload | reel_upload | meta_post)
creative_a           JSONB  {url, text, cta, score}
creative_b           JSONB  {url, text, cta, score}
ab_testing           bool   (default true si es A/B, false si es única)
ab_mode              string (ab_classic | multi_angle)  # default ab_classic
num_angles           int    # solo en multi_angle (2-6)
angles_tested        JSONB []  # tracking por ángulo (ver sección Multi-Angle Testing)
```

El `OptimizationAgent` monitorea métricas cada 24h y puede recomendar:

- Pausar el creative peor (ab_classic) o el ángulo peor (multi_angle)
- Aumentar budget al ganador (creative o ángulo)
- Cambiar copy si CTR < 0.5%
- Redistribuir presupuesto entre ángulos (multi_angle, regla `angle_redistribute`)

---

## Estructura de carpetas

```
/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, routers, Redis subscriber
│   │   ├── config.py                # Settings desde .env
│   │   ├── database.py              # SQLAlchemy async engine + session
│   │   ├── auth.py                  # JWT + bcrypt
│   │   ├── pubsub.py                # Redis pub/sub (publish sync + async)
│   │   ├── ws.py                    # WebSocket ConnectionManager
│   │   ├── models/
│   │   │   ├── user.py              # roles, parent_account, founder, superadmin, closer_id, plan, scans_remaining
│   │   │   ├── user_settings.py     # Meta tokens, Resend, WhatsApp, paleta, company_profile
│   │   │   ├── plan.py              # PlanStatus enum + ab_mode, num_angles, angles_tested, research_export, export_url
│   │   │   ├── task.py              # AgentTask + TaskStatus
│   │   │   (chat_session.py / chat_message.py eliminados — el chat ya no existe)
│   │   │   ├── landing_page.py      # Landing A/B con form_fields, métricas, template_id
│   │   │   ├── lead.py              # Lead capturado con score + segment + pipeline status
│   │   │   ├── lead_magnet.py       # PDF metadata + Cloudinary URL
│   │   │   ├── sequence_event.py    # Historial envíos email/WhatsApp por lead
│   │   │   ├── closer.py            # ✅ Comerciales: email, commission_rate, referral_code
│   │   │   ├── commission.py        # ✅ Comisiones automáticas: tipo (first_quota/recurring), status
│   │   │   ├── recommendation.py    # Recomendaciones del OptimizationAgent (+ campo reasoning)
│   │   │   ├── client_account.py    # ✅ Workspaces multi-cliente (owner_id) — agregación por agencia
│   │   │   ├── api_usage.py         # ✅ Registro de costes OpenAI por llamada/agente
│   │   │   ├── angle_performance.py  # ✅ histórico ángulo × business_type × resultado (Capa 7)
│   │   │   ├── metric_snapshot.py    # ✅ snapshots diarios Meta Insights (ad + breakdowns) — series/breakdowns
│   │   │   ├── metric_alert.py       # ✅ alertas automáticas sobre snapshots (cpl_spike/roas_low/...)
│   │   │   └── lead_form.py          # ✅ Lead Ad forms (instant_form) sincronizados con Meta
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   └── plan.py              # PlanResponse, CampaignWizardRequest, ResearchGenerateRequest, RejectRequest…
│   │   ├── services/
│   │   │   ├── permissions.py       # ✅ gating central: TIER_FEATURES/TIER_LIMITS (+ research_10/100, scans_per_month, consume_scan) + require_feature()/require_action()
│   │   │   ├── research_export.py    # ✅ export research a PDF/JSON → Cloudinary (Capa 7)
│   │   │   ├── stripe_service.py    # ✅ helpers Stripe (subs, webhook, checkout)
│   │   │   ├── commissions.py       # ✅ generación automática de comisiones
│   │   │   ├── closers.py           # ✅ lógica de closers
│   │   │   ├── owner.py             # ✅ helpers de cuenta/owner
│   │   │   ├── openai_costs.py      # ✅ cálculo de coste por llamada OpenAI (→ api_usage)
│   │   │   └── cache.py             # ✅ caché JSON en Redis (insights en vivo); degrada a no-op
│   │   ├── routers/
│   │   │   ├── auth.py              # login, register, refresh token + GET /me/features
│   │   │   (chat.py eliminado — el chat ya no existe; la creación de campañas es vía POST /plans/wizard)
│   │   │   ├── plans.py             # CRUD planes + approve/reject/resume + funnel-choice + creative-choice + export + POST /plans/research (librería) + POST /plans/wizard (crea campaña sin chat)
│   │   │   ├── campaigns.py         # ✅ lista, meta-status, patch, publish, meta-insights (caché), metrics, leads
│   │   │   ├── leads.py             # ✅ POST /leads (scoring + secuencia) + PATCH pipeline + CAPI Purchase al cerrar
│   │   │   ├── landings.py          # ✅ CRUD landing pages
│   │   │   ├── settings.py          # ✅ user_settings (Meta, Resend, WhatsApp, paleta, company)
│   │   │   ├── billing.py           # ✅ Stripe subscripción + webhook invoice.paid (genera comisiones)
│   │   │   ├── meta_oauth.py        # ✅ OAuth Meta + refresh token
│   │   │   ├── uploads.py           # ✅ subida de archivos a Cloudinary
│   │   │   ├── analytics.py         # ✅ /dashboard, /timeseries, /breakdown, /alerts + CPL/ROAS + por ángulo + angle-performance
│   │   │   ├── recommendations.py   # ✅ GET/POST recomendaciones de OptimizationAgent
│   │   │   ├── admin.py             # ✅ panel admin (superadmin only): closers, clientes, comisiones
│   │   │   ├── closer_portal.py     # ✅ login y dashboard para closers (acceso independiente)
│   │   │   ├── team.py              # ✅ invitar usuarios, cambiar roles (solo owner)
│   │   │   └── client_accounts.py   # ✅ CRUD workspaces multi-cliente (agency)
│   │   ├── agents/
│   │   │   ├── base.py              # BaseAgent con loop OpenAI function calling
│   │   │   ├── orchestrator.py      # tools: create_plan, request_clarification
│   │   │   ├── research.py          # Brave Search + GPT análisis
│   │   │   ├── copy.py              # generate_ad_copy, generate_landing_copy, generate_email_sequence
│   │   │   ├── landing.py           # ✅ genera A/B, emotional+rational angles, color palettes
│   │   │   ├── ads.py               # ✅ Meta Graph API v23.0, interest mapping, budget, creative, multi-angle ad sets
│   │   │   ├── crm.py               # ✅ scoring determinista 0-100, rubrica por business_type
│   │   │   ├── email.py             # ✅ 5 emails + 5 WhatsApp + thanks_page por goal
│   │   │   ├── lead_magnet.py       # ✅ PDF 5-8 secciones + Cloudinary upload
│   │   │   ├── optimization.py      # ✅ 4 reglas + análisis LLM + angle_redistribute (z-test) + offer_test_consolidate + escribe angle_performance
│   │   │   └── meta_policy.py       # ✅ validación políticas Meta + humanización copy
│   │   ├── tools/
│   │   │   ├── brave_search.py      # Brave Search API client
│   │   │   ├── meta_ads.py          # Meta Graph API helpers + fetch_insights() + send_conversion_event() (CAPI)
│   │   │   ├── whatsapp.py          # send_whatsapp_text() vía Meta Cloud API
│   │   │   └── resend.py            # send_email() async via Resend API
│   │   └── workers/
│   │       ├── celery_app.py        # include: [execution, email_tasks, optimization_tasks, metrics_tasks] + beat (24h optimización, 1h métricas)
│   │       ├── execution.py         # execute_plan task + enrutamiento de agentes + generate_research (research librería, sin pausas)
│   │       ├── optimization_tasks.py # ✅ beat 24h: recomendaciones OptimizationAgent por campaña
│   │       ├── metrics_tasks.py     # ✅ beat 1h: snapshots Meta Insights + sync ángulos en vivo + alertas
│   │       └── email_tasks.py       # send_sequence_email Celery task (emails con delay)
│   ├── alembic/
│   │   └── versions/0001_initial.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Router + RequireAuth
│   │   ├── store/
│   │   │   ├── authStore.ts         # login, register, logout, fetchMe, fetchFeatures
│   │   │   ├── plansStore.ts        # plans, fetchPlans, approvePlan, rejectPlan
│   │   │   └── tasksStore.ts        # tasksByPlan, fetchTasks, upsertTask
│   │   │   (chatStore.ts eliminado — ya no hay chat)
│   │   ├── pages/
│   │   │   ├── NewCampaign.tsx      # ✅ wizard visual por pasos (/campaigns/new) — reemplaza al chat
│   │   │   ├── PlanWorkspace.tsx    # ✅ /plan/:id — renderiza ApprovalCard (aprobación + funnel/creative/ads)
│   │   │   ├── Dashboard.tsx        # ✅ analytics global vía GET /analytics/dashboard: rango 7/30/90d, serie temporal, breakdowns, alertas
│   │   │   ├── Campaigns.tsx        # tabla campañas, métricas, tabs Leads/Secuencias
│   │   │   ├── LandingPage.tsx      # builder landing, preview A/B, publicar
│   │   │   ├── ResearchLibrary.tsx  # ✅ pestaña /research: librería de research + "Generar nuevo" (modal) + drawer ResearchModeScreen
│   │   │   ├── ResearchModeScreen.tsx  # ✅ vista research: ICP + 6 ángulos interactivos + export + saldo escaneos (Capa 7)
│   │   │   ├── Home.tsx             # campaign builder (negocio, audiencia, goal)
│   │   │   ├── Onboarding.tsx       # flujo onboarding usuario
│   │   │   ├── Settings.tsx         # Meta OAuth, Resend, WhatsApp, paleta, logo, empresa
│   │   │   ├── Admin.tsx            # ✅ panel admin (superadmin): overview, clientes, closers, comisiones
│   │   │   ├── ClientAccounts.tsx   # ✅ gestión de workspaces multi-cliente (agency)
│   │   │   ├── CloserLogin.tsx      # ✅ login del portal de closers
│   │   │   ├── CloserDashboard.tsx  # ✅ dashboard de comisiones del closer
│   │   │   ├── Login.tsx            # login usuario
│   │   │   ├── Register.tsx         # registro usuario
│   │   │   ├── MetaCallback.tsx     # OAuth callback handler
│   │   │   └── BillingSuccess.tsx   # confirmación suscripción
│   │   ├── components/
│   │   │   (components/chat/ eliminado — ChatInput/MessageList/ClarificationForm ya no existen)
│   │   │   ├── approval/
│   │   │   │   ├── ApprovalCard.tsx        # estados: pending/approved/rejected/executing/done (lo renderiza PlanWorkspace)
│   │   │   │   ├── AdsApprovalPanel.tsx    # preview creatives + validación políticas Meta
│   │   │   │   └── CopyApprovalPanel.tsx   # selección variante + humanización
│   │   │   ├── campaigns/
│   │   │   │   ├── TabCampaign.tsx         # detalles campaña, analytics, funnel
│   │   │   │   ├── TabLeads.tsx            # lista leads con scoring y segmento
│   │   │   │   ├── TabSequences.tsx        # secuencias email/WhatsApp visualizadas
│   │   │   │   ├── TabAngles.tsx           # ✅ rendimiento por ángulo + reasoning de recomendación (multi_angle)
│   │   │   │   ├── CampaignModal.tsx
│   │   │   │   └── SectionBlock.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── AgentActivityFeed.tsx       # tasks en tiempo real + modal de output
│   │   │   │   ├── FunnelTypeSelector.tsx       # form elección funnel + modo testeo (ab/multi_angle)
│   │   │   │   └── CreativeChoiceSelector.tsx   # selección variante creativa para ads
│   │   │   ├── research/
│   │   │   │   └── ResearchGenerateModal.tsx  # ✅ modal "Generar nuevo": audiencia+objetivo → POST /plans/research
│   │   │   ├── settings/
│   │   │   │   └── TeamSection.tsx   # ✅ invitar usuarios + cambiar roles (owner only) — NO es página, vive en Settings
│   │   │   └── ui/
│   │   │       ├── Layout.tsx        # header, nav (Research visible a todos; research_only oculta el resto), layout wrapper
│   │   │       └── ImageLightbox.tsx # visor de imágenes ampliadas
│   │   ├── hooks/
│   │   │   ├── useWebSocket.ts      # maneja: new_plan, plan_* (incl. plan_research_view), task_update
│   │   │   └── usePlans.ts
│   │   └── lib/
│   │       └── api.ts               # fetch con JWT header automático
│   └── Dockerfile
│
├── docker-compose.yml               # postgres, redis, backend, worker, frontend
├── .env.example
└── CLAUDE.md
```

---

## Convenciones críticas

### Backend — Autenticación y roles

* `get_current_user` — requiere JWT válido de usuario
* `get_current_admin` — requiere `is_superadmin=true`
* `get_current_closer` — requiere JWT válido con `typ=closer` (token independiente)
* Permiso de equipo: `role` en {owner, admin, member, viewer}. Solo `owner` puede cambiar roles o invitar
* Las comisiones se generan **automáticamente** desde webhook Stripe, nunca a mano

### Backend — Desarrollo

* Type hints en **todo** — sin excepción
* Todos los endpoints son `async`
* Schemas Pydantic para request y response en cada endpoint
* Los agentes usan **OpenAI function calling** (no Anthropic)
* `BaseAgent._to_openai_tools()` convierte `input_schema` → `parameters`
* Los errores de tools nunca crashean el agente — se capturan y reportan
* Las API keys externas (Meta, Google) se guardan en DB cifradas, no en .env
* Celery tasks son síncronas — usan `asyncio.run()` internamente
* Todos los eventos WS pasan por Redis pub/sub (nunca directo al ConnectionManager desde worker)

### Frontend

* Componentes en `PascalCase`, hooks con prefijo `use`
* No usar `any` en TypeScript
* Estado del servidor: fetch directo o en stores de Zustand con métodos async
* Zustand solo para estado de UI y caché local de datos del servidor
* WebSocket conecta al montar `Chat`, desconecta al desmontar

### Base de datos

* Toda tabla tiene `id` (UUID), `created_at`, `updated_at`
* Los ENUMs de Python (`PlanStatus`, `TaskStatus`) se almacenan como `String(50)` en DB
* Las migraciones van en `alembic/versions/`
* Nunca hacer `DROP` en migraciones de producción

---

## Variables de entorno (.env)

```
# Base de datos
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/growthOS
REDIS_URL=redis://redis:6379

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Auth
JWT_SECRET=...
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# Búsqueda
BRAVE_API_KEY=BSA...

# Servicios externos (RESEND_API_KEY ya no va en .env — el usuario la pone en Settings)
META_APP_ID=...
META_APP_SECRET=...
# VERCEL_TOKEN eliminado — las landings se sirven desde el propio frontend

# Frontend
VITE_API_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
```

---

## Plantillas de Landing Pages

Las landings no se generan como HTML desde cero. El `LandingAgent` selecciona una plantilla base según `business_type` + `tipo_oferta`, e inyecta el contenido generado. El diseño, jerarquía y composición ya están resueltos en la plantilla.

### Plantillas disponibles

| Template ID           | `business_type` | `tipo_oferta`                          | Composición visual                                                           |
| --------------------- | ----------------- | ---------------------------------------- | ----------------------------------------------------------------------------- |
| `saas_trial`        | `saas`          | `prueba_gratuita`                      | Hero con demo GIF/screenshot + social proof logos + features grid + CTA trial |
| `saas_demo`         | `saas`          | `evergreen` / `lanzamiento`          | Hero bold + pain points numerados + testimonios + CTA demo                    |
| `services_call`     | `services`      | `evergreen` / `lanzamiento`          | Hero con foto/avatar + proceso 3 pasos + resultados clientes + CTA llamada    |
| `services_launch`   | `services`      | `lanzamiento` / `descuento_limitado` | Hero con urgencia + contador + beneficios + garantía + CTA                   |
| `ecommerce_product` | `ecommerce`     | `evergreen` / `descuento_limitado`   | Hero producto + bullets + prueba social + urgencia stock + CTA compra         |
| `app_download`      | `app`           | `prueba_gratuita` / `evergreen`      | Hero móvil + features visuales + ratings + CTA descarga                      |
| `local_offer`       | `local`         | `descuento_limitado` / `evergreen`   | Hero ubicación + oferta destacada + reseñas + mapa/contacto                 |
| `lead_magnet_clean` | cualquiera        | cualquiera (`funnel_type=landing_lm`)  | Hero minimalista + valor del recurso + form captura centrado                  |

### Lógica de selección en `LandingAgent`

```python
def select_template(business_type, tipo_oferta, funnel_type, landing_subtype):
    if landing_subtype == "lm":
        return "lead_magnet_clean"  # siempre, independiente del negocio
    if business_type == "saas" and tipo_oferta == "prueba_gratuita":
        return "saas_trial"
    if business_type == "saas":
        return "saas_demo"
    if business_type == "services" and tipo_oferta in ("lanzamiento", "descuento_limitado"):
        return "services_launch"
    if business_type == "services":
        return "services_call"
    if business_type == "ecommerce":
        return "ecommerce_product"
    if business_type == "app":
        return "app_download"
    if business_type == "local":
        return "local_offer"
    return "services_call"  # fallback genérico
```

### Campos que el LandingAgent inyecta en la plantilla

Además de `headline`, `subheadline`, `benefits`, `cta_text`:

```
transformacion       → H1 principal (viene del Offer Engine)
garantia             → bloque de trust visual (badge o sección dedicada)
urgencia             → si fecha_limite o plazas_limitadas → contador o badge
company_name         → aparece en navbar y footer
logo_url             → navbar (si existe)
primary_color        → color de CTAs y acentos
hero_image_url       → imagen DALL-E del CopyAgent (si existe)
social_proof         → testimonios/logos generados o placeholder según template
```

### Modelo DB: `landing_pages` — campo adicional

```
template_id          string   # ej: "saas_trial", "services_call" — seleccionado por LandingAgent
```

---

## Sistema de Landing Pages

Las landing pages se sirven desde el propio frontend. Sin Vercel, sin deploys externos.

### Rutas

```
/landing/:id        → variante A (pública, sin auth)
/landing/:id?v=b    → variante B (pública, sin auth)
/landing/:id/thanks → página de gracias tras submit del form
```

### Modelo DB: `landing_pages`

```
id UUID
plan_id FK → plans.id
user_id FK → users.id
variant              "a" | "b"
campaign_type        "lead_gen" | "direct_sale"
funnel_type          "instant_form" | "landing_direct" | "landing_lm"
landing_subtype      "lm" | "sale" | null   # solo si funnel_type = landing_lm
sale_type            "call" | "payment" | null  # solo si landing_subtype = sale

# Contenido generado por LandingAgent
headline             string
subheadline          string
benefits             JSONB []string
cta_text             string
hero_image_url       string | null   # imagen DALL-E del CopyAgent si existe

# Configuración desde Settings del usuario
primary_color        string (hex, ej: #6366f1)
secondary_color      string (hex)
logo_url             string | null
meta_pixel_id        string | null   # inyectado en <head>

# Comportamiento
redirect_url         string | null   # solo si campaign_type = "direct_sale"
form_fields          JSONB           # campos cualificadores del lead:
                                     # [{"name": "email", "required": true},
                                     #  {"name": "nombre", "required": true},
                                     #  {"name": "empresa", "required": false},
                                     #  {"name": "telefono", "required": false},
                                     #  {"name": "num_empleados", "required": false}]

# Métricas
views                int default 0
conversions          int default 0
published_at         datetime | null
created_at, updated_at
```

### Modelo DB: `leads`

```
id UUID
landing_page_id FK → landing_pages.id
plan_id FK → plans.id
user_id FK → users.id   # usuario dueño del plan
email                string
nombre               string | null
empresa              string | null
telefono             string | null
num_empleados        string | null
extra_data           JSONB           # campos adicionales
score                int | null      # asignado por CRMAgent
segment              string | null   # asignado por CRMAgent
created_at, updated_at
```

### Modelo DB: `leads` — campos de pipeline (extensión)

```
# Campos adicionales para tracking de pipeline (✅ migración 0018_lead_pipeline)
lead_status          "new" | "contacted" | "showed_up" | "closed" | "lost"
closed_value         decimal | null      # revenue atribuido a este lead
meeting_scheduled_at datetime | null
showed_up_at         datetime | null
closed_at            datetime | null
```

El usuario actualiza `lead_status` y `closed_value` manualmente desde la tabla de Leads.

### Métricas calculadas por el sistema (no por Meta)

```
CPL real             = total_spent / leads_count
Cost per show-up     = total_spent / showed_up_count
Cost per close       = total_spent / closed_count
ROAS                 = revenue_attributed / total_spent
LTV proyectado       = avg_closed_value × recurrencia_estimada

# En modo multi_angle, estas métricas se calculan también por ángulo:
CPL por ángulo       = spent_ángulo / leads_ángulo
ROAS por ángulo      = revenue_ángulo / spent_ángulo
```

Estas métricas se añaden a `campaigns` como campos calculados y se muestran en el dashboard de Campañas junto a los datos de Meta Insights.

---

## Sistema de Métricas y Analytics

> **No hay AnalyticsAgent ni polling en vivo desde el dashboard.** Las métricas de Meta se **persisten en snapshots diarios** (cron horario) y el dashboard lee de BD. Esto da series temporales, breakdowns, comparación de periodos y alertas — y evita chocar el rate limit de Meta (la Graph/Marketing API es **gratuita**, pero limitada por nº de peticiones).

### Pipeline de datos

```
Celery beat (cada 1h) → sync_metrics_for_all_campaigns
    → por cada campaña publicada: sync_metrics_for_plan
        → fetch_insights() a Meta (time_increment=1, ventana last_7d):
            · nivel ad, sin breakdown            → granularidad fina por día
            · nivel campaña × cada breakdown     → age, gender, publisher_platform,
                                                    region, impression_device
        → upsert idempotente en metric_snapshots (reescribe el día en curso)
        → _sync_angles_from_snapshots()  → refresca plan.angles_tested en vivo
        → _evaluate_alerts()             → crea/actualiza metric_alerts
```

- Al **publicar** una campaña se encola un primer `sync_metrics_for_plan` (kick inicial).
- `fetch_insights()` (en `tools/meta_ads.py`) normaliza `actions`/`action_values` → leads, conversiones, revenue. Es la única función de lectura flexible (level, breakdown, time_increment, rango).
- El endpoint legacy `GET /campaigns/:id/meta-insights` sigue pegando a Meta **en vivo pero con caché Redis 15 min** (`services/cache.py`, degrada a no-op si Redis falla).

### Tabla: `metric_snapshots` (migración `0028_metric_snapshots`)

```
id UUID
client_account_id FK, plan_id FK
meta_campaign_id / meta_adset_id / meta_ad_id   string  # "" cuando no aplica (no NULL → unique limpio)
level             string   # campaign | adset | ad
angle             string | null   # derivado de plan.angles_tested por ad set (multi_angle)
breakdown_key     string   # "" | age | gender | publisher_platform | region | impression_device
breakdown_value   string   # "" | "25-34" | "female" | "facebook" ...
snapshot_date     date     # día de los datos (time_increment=1)
impressions, clicks, reach, leads, conversions  int
spend, revenue    Decimal
ctr, cpc, cpm, cpl  Decimal | null
UNIQUE (plan_id, level, meta_adset_id, meta_ad_id, breakdown_key, breakdown_value, snapshot_date)
```

### Tabla: `metric_alerts` (migración `0029_metric_alerts`)

Alertas automáticas **sin LLM**, generadas por el worker tras cada sync. A diferencia de `recommendations` (OptimizationAgent propone una acción a aprobar), una alerta solo **avisa** y el usuario la descarta.

```
id UUID, client_account_id FK, plan_id FK
type        string   # cpl_spike | roas_low | spend_no_leads | ctr_drop
severity    string   # info | warning | critical
title, message  string/text     # mensaje en lenguaje de media buyer, con números
metric_key, current_value, baseline_value
status      string   # active | dismissed
snapshot_date date
UNIQUE (plan_id, type, snapshot_date)   # idempotente: 1 alerta por tipo/plan/día
```

Reglas (alineadas con OptimizationAgent / Multi-Angle): `cpl_spike` (CPL hoy >130% de ayer), `ctr_drop` (CTR<0.5% con >3k impresiones), `spend_no_leads` (≥€30 sin un lead, crítica), `roas_low` (ROAS<1x con revenue atribuido).

### Atribución server-side (CAPI)

Cuando un lead pasa a `lead_status = "closed"` (PATCH `/leads/:id`), se envía un evento **`Purchase` a la Conversions API de Meta** (`send_conversion_event` en `tools/meta_ads.py`): PII (email/teléfono) hasheada SHA-256, `value = closed_value`, `event_id = lead-{id}-closed` para deduplicar contra el pixel web. Requiere `meta_pixel_id` + `meta_access_token` en Settings. No bloquea el PATCH si Meta falla. Así Meta aprende qué audiencia/creativo trae ventas reales, no solo clics.

### Endpoints de analytics

```
GET  /analytics/dashboard?days=30          → 1 sola llamada: totals + timeseries +
                                             by_campaign + by_placement + by_device + alerts (desde snapshots)
GET  /analytics/campaign/:id/timeseries?days=  → serie diaria de la campaña
GET  /analytics/campaign/:id/breakdown?key=age → agregado por dimensión
GET  /analytics/alerts?status=active        → alertas del account
POST /analytics/alerts/:id/dismiss          → descarta una alerta
GET  /analytics/overview                    → (legacy) overview por campaña
GET  /analytics/campaign/:id/angles         → rendimiento por ángulo (multi_angle)
```

El `Dashboard.tsx` consume `GET /analytics/dashboard`: selector de rango (7/30/90 días), gráfica temporal conmutable (gasto, leads, clics, CTR, CPL, revenue…), breakdowns por plataforma/dispositivo y panel de alertas descartables.

### Settings del usuario (`user_settings`)

```
id UUID
user_id FK unique
meta_pixel_id        string | null
meta_access_token    string | null   # cifrado
meta_ad_account_id   string | null
color_palette        string          # hex del color primario elegido
logo_url             string | null
company_name         string | null
resend_api_key            string | null   # API key de Resend del usuario (guardada en Text)
resend_from_email         string | null   # email remitente (ej: hola@sudominio.com)
whatsapp_phone_number_id  string | null   # Phone Number ID de WhatsApp Business
whatsapp_phone_display    string | null   # número legible (ej: +34 600 000 000)
created_at, updated_at
```

> La API key de Resend la introduce el usuario en Settings. La respuesta del endpoint nunca devuelve el valor crudo — solo `has_resend_key: bool`.

### Paletas de color en Settings

El usuario elige entre 10 paletas predefinidas. El agente puede sugerir la más adecuada
al sector, pero el usuario siempre puede cambiarla antes de publicar.

Paletas disponibles:

```
indigo    #6366f1 / #e0e7ff    → tech, SaaS genérico
emerald   #10b981 / #d1fae5    → fintech, salud, sostenibilidad
violet    #8b5cf6 / #ede9fe    → creativo, marketing, diseño
sky       #0ea5e9 / #e0f2fe    → productividad, herramientas
rose      #f43f5e / #ffe4e6    → ecommerce, lifestyle
amber     #f59e0b / #fef3c7    → educación, consulting
cyan      #06b6d4 / #cffafe    → datos, analytics, IA
slate     #475569 / #f1f5f9    → enterprise, legal, B2B
orange    #f97316 / #ffedd5    → food, retail, energía
teal      #14b8a6 / #ccfbf1    → bienestar, RRHH, comunidad
```

### Flujo completo

1. `LandingAgent` recibe contexto de Research + Copy y genera contenido A y B
2. Lee `meta_pixel_id` y `color_palette` de `user_settings`
3. Guarda dos registros en `landing_pages` (variant A y B)
4. Frontend renderiza `/landing/:id` con el contenido de DB
5. Pixel Meta se inyecta en `<head>` via `react-helmet` o `<script>` dinámico
6. Al enviar el form → POST `/leads` → guarda en DB → envía email #1 inmediato + schedula emails 2-5 via Celery con countdown → redirige a `/landing/:id/thanks`
7. Si `campaign_type = direct_sale` → no hay form, CTA redirige a `redirect_url`
8. En Meta Ads se usan las dos URLs para el split test A/B

---

## Estado actual del proyecto (~98% completo)

### ✅ Completado

**Backend — Agentes:**

- `OrchestratorAgent` — pausa en `pending_copy_approval` y `awaiting_funnel_choice`, propaga todos los campos
- `ResearchAgent` — Brave Search + 6 ángulos de copy + ICP analysis
- `CopyAgent` — copies Meta Ads + landing + email, variantes A/B, awaiting approval
- `LandingAgent` — genera A/B con `landing_subtype` (lm/sale), plantillas por business_type + tipo_oferta
- `AdsAgent` — Meta Graph API v23.0, todos los funnel_types, awaiting approval
- `LeadMagnetAgent` — PDF 5-8 secciones con IA + Cloudinary upload
- `EmailAgent` — 5 emails + 5 WhatsApp + thanks_page, adaptados a `post_conversion_goal`
- `CRMAgent` — scoring 0-100 determinista + segmentación hot/warm/cold
- `MetaPolicyAgent` — validación políticas Meta + humanización copy IA
- `OptimizationAgent` — recomendaciones automáticas cada 24h + análisis LLM

**Backend — Routers:**

- `auth`, `plans` (+ resume-copy/ads, funnel-choice, creative-choice, wizard, research) — el chat fue eliminado
- `campaigns` (lista, meta-status, patch, publish, meta-insights con caché, metrics)
- `leads` (POST + PATCH pipeline + CAPI), `landings`, `settings`, `billing`, `meta_oauth`, `uploads`, `lead_forms`
- `analytics` (dashboard, timeseries, breakdown, alerts, CPL/ROAS, por ángulo, angle-performance)
- `recommendations` (GET/POST recomendaciones OptimizationAgent)
- `admin` ✅ (overview, clientes, closers, comisiones — superadmin only)
- `closer_portal` ✅ (login, me, dashboard — acceso independiente para closers)
- `team` ✅ (invitar usuarios, cambiar roles)

**Backend — Modelos DB:**

- `users` (con roles, parent_account, founder, superadmin, closer_id, scans_remaining)
- `user_settings` (+ company_profile fields)
- `plans` (con creative_type, ab_mode, angles_tested, research_export, nuevos estados de approval)
- `tasks` (las tablas `chat_sessions`/`chat_messages` quedan en BD sin uso — chat eliminado, no se hace DROP)
- `landing_pages` (con template_id), `leads` (con pipeline status), `lead_magnets`, `sequence_events`, `lead_forms`
- `closer` ✅, `commission` ✅, `recommendation` ✅, `angle_performance` ✅, `metric_snapshot` ✅, `metric_alert` ✅

**Frontend — Páginas:**

- `Dashboard` — approval workflow + funnel/creative choice
- `Campaigns` — tabla campañas + tabs Leads/Secuencias + recomendaciones OptimizationAgent
- `LandingPage` — builder + preview A/B + publicar
- `Settings` — Meta OAuth, Resend, WhatsApp, paleta, logo, empresa
- `Admin` ✅ — panel admin (superadmin): overview MRR, clientes, closers, comisiones
- `Team` ✅ — invitar usuarios, cambiar roles (owner only)
- `Home`, `Onboarding`, `Login`, `Register`, `MetaCallback`, `BillingSuccess`

**Frontend — Componentes:**

- `AgentActivityFeed` — tasks en tiempo real WebSocket + approval modals
- `FunnelTypeSelector`, `CreativeChoiceSelector`
- `AdsApprovalPanel`, `CopyApprovalPanel`
- `TabLeads` — scoring, segmento, lead_status editable, closed_value
- `TabSequences` — visualización email + WhatsApp
- `RecommendationCards` ✅ — aprobación recomendaciones OptimizationAgent

### ✅ Completado (Capas 0–3)

**Capa 0 — Configuración de empresa**

- ✅ `user_settings` — `business_description` + `business_type` (migración `0017_company_profile`)
- ✅ `OrchestratorAgent` — inyecta `<company_profile>` en system prompt; bloquea plan si faltan campos
- ✅ `GET /settings/completeness` — devuelve `{complete, missing}`
- ✅ `Settings.tsx` — sección "Tu empresa" con nombre, tipo (select) y descripción (textarea) + badge ámbar
- ✅ `NewCampaign.tsx` (wizard) — paso 1 bloquea con aviso + enlace a Ajustes si falta el perfil de empresa

**Capa 1 — Offer Engine + Plantillas de Landing**

- ✅ `OrchestratorAgent` — captura y propaga `precio_base`, `tipo_oferta`, `urgencia`, `garantia`, `transformacion`
- ✅ Migración `0018_offer_engine` — 5 columnas en `plans` + `template_id` en `landing_pages`
- ✅ `LandingAgent` — `select_template()` por `business_type` + `tipo_oferta`; usa `transformacion` como H1 y `garantia` como bloque de trust
- ✅ Frontend — 8 plantillas React en `LandingPage.tsx` (saas_trial, saas_demo, services_call, services_launch, ecommerce_product, app_download, local_offer, lead_magnet_clean)
- ✅ `AdsAgent` — `urgencia` mapeada a copy real (fecha_limite, plazas_limitadas, bonus_temporal)
- ✅ `FunnelTypeSelector` — pre-selección según `tipo_oferta` con badge "Recomendado"

**Capa 2 — Pipeline de métricas**

- ✅ Migración `0018_lead_pipeline` — `lead_status`, `closed_value`, `meeting_scheduled_at`, `showed_up_at`, `closed_at` en `leads`
- ✅ `PATCH /leads/:id` — actualiza status + auto-timestamping al cambiar estado
- ✅ `analytics.py` router — CPL real, Cost per show-up, Cost per close, ROAS calculados
- ✅ `TabLeads.tsx` — `lead_status` editable inline + campo `closed_value`

**Capa 3 — OptimizationAgent**

- ✅ `optimization.py` — 4 reglas deterministas (copy_refresh, audience_expand, budget_increase, pause_campaign) + análisis LLM
- ✅ Modelo `recommendations` + migración `0019_recommendations`
- ✅ `recommendations.py` router — `GET /campaigns/:id` + `POST /:id/approve` + `POST /:id/reject`
- ✅ Celery beat task `run_optimization_for_all_campaigns` — cada 24h (86400s)
- ✅ `RecommendationCards.tsx` — cards accionables con Aprobar / Rechazar / Analizar ahora

### ✅ Completado (Capas 4–8)

**Capa 4 — Secuencias dinámicas por pipeline**

- ✅ `email_tasks.py` — pausa la secuencia si `lead_status ∈ {closed, lost}` (`_should_stop`) y adapta el asunto si `showed_up`
- ✅ `CRMAgent` — `rescore_on_status_change` al cambiar `lead_status` (en `PATCH /leads/:id`)

**Capa 5 — Offer Testing**

- ✅ Migración `0019_offer_testing` — `parent_plan_id`, `is_offer_test`, `offer_test_label` en `plans`
- ✅ `POST /plans/:id/offer-test` — crea la 2ª campaña (oferta B) con feature `offer_testing`
- ✅ `GET /plans/:id/offer-comparison` — vista comparativa de las variantes del test
- ✅ `OptimizationAgent` — regla `offer_test_consolidate`: tras `OFFER_TEST_MIN_LEADS` (20) compara variantes y recomienda consolidar la ganadora
- ✅ Dashboard `Campaigns.tsx` — comparador de ofertas (`onCompare`)

**Capa 6 — Limpieza**

- ✅ Dashboard Campañas — `analytics/overview` ordena por ROAS descendente
- ✅ Página de gracias — `GET /landings/:id/thanks` + `LandingThanks` con `EmailAgent.thanks_page` + descarga de lead magnet
- ✅ `TabCampaign.tsx` — `FunnelMetricsSection` (CPL real, ROAS, cost per show-up/close, funnel visual) vía `GET /campaigns/:id/metrics`
- ⏳ AdsAgent Google — una vez Meta está estable (futuro)

**Capa 7 — Multi-Angle Testing (MAT)** ✅

*Core:*

- ✅ Migración `0025_multi_angle_research` — `ab_mode`, `num_angles`, `angles_tested` (JSONB con `image_url`), `research_export`, `export_url` en `plans` + `scans_remaining`/`scans_reset_at` en `users`
- ✅ `CopyAgent` — modo `multi_angle`: 1 copy **+ 1 imagen DALL-E propia** por ángulo (mood de imagen por ángulo). El step se añade en `funnel-choice`
- ✅ `AdsAgent` — `_build_multi_angle_campaign`: 1 campaign → N ad sets (1 por ángulo), presupuesto equitativo (CBO off en fase 1); persiste `angles_tested` en el plan
- ✅ `MetaPolicyAgent` — valida cada ángulo (step extra tras el copy multi_angle; pausa de aprobación condicionada a fase inicial)
- ✅ `OptimizationAgent` — `evaluate_angles` + `angle_redistribute`: señal mínima (3k impresiones / €30) **Y** z-test de proporciones (p<0.05). Estados: active / winner / loser / inconclusive / insufficient_data
- ✅ `analytics.py` — `GET /analytics/campaign/:id/angles` (por ángulo)
- ✅ `FunnelTypeSelector.tsx` — selector A/B vs Multi-Angle + nº de ángulos (2-6)
- ✅ `TabAngles.tsx` — tab en Campaigns: rendimiento por ángulo + `reasoning` de la recomendación

*Activo a largo plazo (defendibilidad):*

- ✅ Migración `0026_angle_performance` — tabla `angle_performance` (agregable por `account_id`)
- ✅ `OptimizationAgent` — escribe en `angle_performance` al consolidar (`_write_angle_performance`)
- ✅ `analytics.py` — `GET /analytics/angle-performance` + `/summary` (win rate por ángulo × business_type)
- ✅ Feedback loop — `funnel-choice` calcula `priority_angles` por win rate histórico (`_recommended_angles`) y el `CopyAgent` los antepone; `FunnelTypeSelector` muestra badges "X% win" desde `/analytics/angle-performance/summary`

*Salida temprana (research export):*

- ✅ `research_export` + `export_url` en `plans`; estado `research_view`
- ✅ `FunnelTypeSelector.tsx` — opción "Solo quiero el research y los ángulos"
- ✅ `ResearchModeScreen.tsx` — ICP + pain points + 6 ángulos interactivos (copy + imagen) + copiar + exportar + bloque histórico + saldo de escaneos
- ✅ `GET /plans/:id/research` + `POST /plans/:id/export` (PDF/JSON → Cloudinary vía `services/research_export.py`)

*Opcional (cruce con Capa 5):*

- ✅ Matriz `ángulo × oferta`: `offer_test_consolidate` detecta el mejor ángulo de la oferta ganadora y recomienda la combinación `(ángulo, oferta)` en `winning_combo`

**Capa 8 — Gating de funcionalidades por plan**

- ✅ `app/services/permissions.py` — `TIER_FEATURES`/`TIER_LIMITS` con `multi_angle`/`optimization`/`angle_history`/`research_export`, planes `research_10`/`research_100`, `scans_per_month`, `is_research_only()`, `consume_scan()` (reset por ciclo) + `require_feature()`/`require_action()`
- ✅ `GET /auth/me/features` — features + límites + saldo de escaneos del usuario
- ✅ `funnel-choice` respeta el gating (402/403 si el plan no incluye `multi_angle` o `research_export`)
- ✅ `billing.py` / `stripe_service.py` — suscripción mensual de research (`research_10`/`research_100`, prices auto-creados sin fundador, `GET /billing/research-plans`); `_sync_subscription` recarga `scans_remaining` al activar/renovar; `POST /plans/research` descuenta 1 escaneo por research generado vía `consume_scan` (402 sin saldo)
- ✅ Frontend — `authStore` (`fetchFeatures`/`hasFeature` desde `/auth/me/features`); `FunnelTypeSelector` bloquea Multi-Angle/Research con badge "Disponible en Growth/Starter+"

**Capa 9 — Sistema de Métricas y Analytics** ✅

Ver sección "Sistema de Métricas y Analytics" para el detalle.

- ✅ Migración `0028_metric_snapshots` — snapshots diarios Meta Insights (ad + breakdowns), upsert idempotente
- ✅ `tools/meta_ads.py` — `fetch_insights()` (level/breakdown/time_increment/rango) + `send_conversion_event()` (CAPI Purchase)
- ✅ `workers/metrics_tasks.py` — beat horario: snapshots + `_sync_angles_from_snapshots` (multi_angle en vivo) + `_evaluate_alerts`
- ✅ Migración `0029_metric_alerts` — alertas automáticas (cpl_spike, roas_low, spend_no_leads, ctr_drop)
- ✅ `services/cache.py` — caché Redis para `meta-insights` en vivo (15 min)
- ✅ `analytics.py` — `/dashboard`, `/timeseries`, `/breakdown`, `/alerts` (+ dismiss)
- ✅ `leads.py` — CAPI `Purchase` server-side al marcar lead `closed`
- ✅ `Dashboard.tsx` — 1 llamada a `/analytics/dashboard`: rango 7/30/90d, serie temporal, breakdowns, panel de alertas

> **Nota de despliegue:** las migraciones `0025_multi_angle_research`, `0026_angle_performance`, `0027_lead_forms`, `0028_metric_snapshots` y `0029_metric_alerts` aún deben aplicarse con `alembic upgrade head`.

## EmailAgent — post_conversion_goal

El `post_conversion_goal` se propaga desde el Orchestrator a todos los steps. El EmailAgent lo usa para:

1. Adaptar el CTA del primer email (acción inmediata tras el form)
2. Generar el contenido de la página de gracias (`thanks_page`)
3. Definir el tono de toda la secuencia de nurturing

| Goal                 | Cuándo usarlo                                            | Primer email CTA             |
| -------------------- | --------------------------------------------------------- | ---------------------------- |
| `schedule_meeting` | SaaS/services que venden por llamada. URL: Calendly       | "Agenda tu sesión gratuita" |
| `free_trial`       | SaaS con trial activo. URL: página de registro del trial | "Empieza tu prueba gratis"   |
| `demo_request`     | SaaS sin trial / con demo grabada                         | "Ver la demo personalizada"  |
| `download`         | Lead magnet, recurso descargable                          | "Descargar ahora"            |
| `thank_you_only`   | Validación de idea, sin producto activo aún             | "Cuéntame más sobre ti"    |
| `community`        | Comunidad, programa, Slack/Discord                        | "Unirme a la comunidad"      |
| `pricing_page`     | Venta directa con nurturing post-contacto                 | "Ver planes y precios"       |

## Lo que NO hacer

* **No comprobar el plan de forma dispersa** en cada router — el gating de funcionalidades va centralizado en `app/services/permissions.py` con `require_feature(...)`/`require_action(...)`. El frontend lee `GET /me/features`
* **No ocultar sin más** una función no disponible en el frontend — mostrar el upsell ("Disponible en Growth") para empujar el upgrade
* **No ejecutar** ninguna acción externa sin que el plan esté en estado `approved`
* **No redistribuir presupuesto entre ángulos** automáticamente — el `angle_redistribute` siempre propone, el usuario aprueba
* **No declarar ganador/perdedor un ángulo** antes de la señal mínima (3k impresiones / €30 por ad set) **ni sin significancia estadística** — si la diferencia no es concluyente, el estado es `inconclusive`, no `winner`
* **No mostrar recomendaciones como caja negra** — toda recomendación del OptimizationAgent lleva un `reasoning` con los números que la justifican
* **No pegar a Meta Insights en vivo desde el dashboard** — leer de `metric_snapshots` (los pobla el beat horario). El único punto que pega en vivo es `meta-insights`, y va con caché Redis
* **No duplicar snapshots/alertas** — el upsert es idempotente por su clave única (snapshot: plan+level+adset+ad+breakdown+día; alerta: plan+tipo+día)
* **No reutilizar la misma imagen para todos los ángulos** en `multi_angle` — cada ángulo lleva su propia imagen DALL-E coherente con su mensaje
* **No calcular comisiones a mano** — siempre automáticas desde webhook de Stripe
* **No asignar roles** desde fuera del endpoint `/team/invite` — solo el owner puede hacerlo
* **No crear Closer directo en BD** — siempre a través de admin panel. Cambios: email, commission_rate, is_active requieren superadmin
* **No usar Redux** — Zustand es suficiente
* **No hardcodear** API keys en ningún sitio
* **No crear endpoints** sin su schema Pydantic correspondiente
* **No mezclar** lógica de agentes con lógica de routers HTTP
* **No llamar** al `ConnectionManager` directamente desde el worker — siempre via Redis pub/sub
* **No hacer** llamadas síncronas a OpenAI desde un router — siempre a través de Celery

## Modelo a usar

`gpt-4o` para todos los agentes.
`max_tokens: 4096` para orquestador y agentes de generación.
`max_tokens: 1024` para agentes de decisión (analytics, scoring).
`response_format: {"type": "json_object"}` en todos los agentes que devuelven datos estructurados.
