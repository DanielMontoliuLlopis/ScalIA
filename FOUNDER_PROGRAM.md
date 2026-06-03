# Programa Fundadores — Solo 20 cupos

> **50% DE DESCUENTO. DE POR VIDA.**
> Para los primeros 20 clientes que entren al programa fundadores.
> Sin fecha de vencimiento. Sin condiciones. Para siempre.

El precio fundador queda **bloqueado de por vida** (`user.is_founder = true`). Cupos
limitados a `FOUNDER_SPOTS_LIMIT = 20` (ver `backend/app/config.py`). El backend cuenta
usuarios con `is_founder = true` y cierra el programa cuando se agotan
(`GET /billing/founder-status`).

## Tiers y precios

| Tier    | Precio normal | Precio fundador (de por vida) | Campañas activas | Asientos equipo |
| ------- | ------------- | ----------------------------- | ---------------- | --------------- |
| Starter | 97 €/mes      | **48 €/mes**                  | 1                | 1               |
| Growth  | 247 €/mes     | **123 €/mes**                 | 3                | 3               |
| Agency  | 497 €/mes     | **248 €/mes**                 | ∞                | ∞               |

> Precios definidos en `Settings` (`STRIPE_PRICE_*_AMOUNT` y `STRIPE_PRICE_*_FOUNDER_AMOUNT`).
> Stripe crea dos precios por tier: normal y fundador (`metadata.founder = "true"`).

---

## Cómo usarlo en la conversión

Esta oferta **no se menciona al principio** — se reserva para el momento de cierre o
cuando el prospecto pide tiempo para pensarlo.

### Cuando el prospecto dice "lo pienso y te aviso"

> "Entiendo. Lo único que te digo es que esta oferta es para los primeros 20 clientes
> fundadores. Una vez que se completen, el precio vuelve al normal y no hay forma de
> recuperar este descuento. No te lo digo para presionarte, sino para que lo tengas en
> cuenta al decidir. ¿Qué necesitas resolver para definirte hoy?"

### Cuando el prospecto dice "está un poco caro"

> "Entiendo. Por eso existe el programa fundadores. Si entras hoy, el precio que pagas
> ahora lo mantienes para siempre. Growth a 123 €/mes en lugar de 247 €."

### Cuando ya está convencido pero duda en el plan

> "Si te interesa el plan Growth pero el precio te genera ruido, el programa fundadores
> lo deja en 123 €/mes de por vida. Es básicamente el precio de Starter con todas las
> funcionalidades de Growth. No creo que vuelvas a ver esta oportunidad una vez que los
> cupos se llenen."

---

## Seguimiento de cupos — úsalo como herramienta

Llevar un conteo visible de los cupos disponibles aumenta la urgencia percibida. En cada
conversación puedes mencionar cuántos quedan:

> **"Ya tenemos 14 fundadores confirmados. Quedan 6 cupos."**

La escasez real — no artificial — es el argumento más honesto y efectivo que existe.
El conteo en vivo lo da `GET /billing/founder-status` → `{ spots_total, spots_taken, spots_left, is_open }`.

---

_Growth OS — Confidencial para equipo de ventas_
