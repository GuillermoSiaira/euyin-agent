# SPEC-KEYS-01 — Webhook Paddle → Emisión de API Key

> **Estado**: ✅ APROBADO CON CORRECCIONES MAYORES (auditoría Fable 2026-06-12)  

## ⚖️ AUDITORÍA FABLE — leer antes de implementar

**Veredicto: el alcance original duplica infraestructura que YA EXISTE.** Antigravity
no tenía visibilidad de `next_app/`: el webhook Paddle ya está implementado en
`next_app/app/api/webhook/paddle/route.ts`, y `next_app/lib/provision-user.ts` ya
crea usuario Firebase + doc Firestore `users/{uid}` con `api_key: uuidv4()`, `plan`,
`quota_used/quota_limit` y manda welcome email (Resend). **NO construir webhook nuevo,
NO crear colección `api_keys/` paralela.** El alcance real es soldar 3 cabos:

1. **Engine acepta la key** *(lo implementa Fable — auth no se delega)*: branch
   `X-Abu-Api-Key` en `verify_token_or_service_key` (`abu_engine/core/auth.py`) →
   query `users` where `api_key == header` → mismo flujo de `payment_verified` +
   quota que ya existe en `verify_token`.
2. **La key llega al cliente** *(delegable)*: agregarla al welcome email de
   `provision-user.ts` (bloque "Tu API key + config MCP") y mostrarla en la app
   (sección cuenta). Hoy se genera y muere en Firestore.
3. **Formato de key** *(delegable, junto con 2)*: en `provision-user.ts` cambiar
   `uuidv4()` → `"ak_" + crypto.randomBytes(24).toString("hex")`. Sin migración:
   hay 0 keys emitidas a usuarios.

**Respuestas a las preguntas abiertas:**
1. **Scopes**: enum de tier con permisos implícitos — NADA de listas planas. v1: el
   corte es binario (endpoints públicos sin key / protegidos con key válida) + quota
   por plan (`QUOTA_LIMITS` ya existe en provision-user). Scopes granulares = v2.
   El tier Free NO recibe key en v1 (lo público no la pide).
2. **Firestore** — sí. Cloud SQL rechazado: todo el sistema de usuarios vive en
   Firestore; agregar SQL es complejidad sin beneficio a este volumen.
3. **Rate limiting en el engine** (middleware). Gateway/Apigee rechazado: overkill
   absoluto para <1.000 req/día y suma costo fijo. Ver SPEC-METER-01.
4. **Ni hash ni encriptada en v1: texto plano en Firestore** (ya es así). Razón:
   permite reenvío por email y dashboard sin fricción; la DB no es pública y las
   rules la protegen. Hash+prefix = v2 cuando haya volumen real. El borrador
   recomendaba hash — rechazado por ahora: rompe el caso de soporte "perdí mi key"
   con 0 usuarios y soporte manual.
5. **Header nuevo `X-Abu-Api-Key`** — no reutilizar `X-Abu-Service-Key` (semánticas
   distintas: servicio interno vs cliente pago; logs y revocación separados).

**Otras correcciones**: el "patrón existente" citado está en
`abu_engine/core/auth.py` (no en config.py/abu_client.py del MCP — esos son el
*consumidor*). Revocación admin endpoint: fuera de alcance v1 — se revoca
regenerando/borrando `api_key` en Firestore console. El schema `api_keys/{hash}`
del cuerpo de abajo queda como referencia histórica: **el schema real es
`users/{uid}.api_key`**. La tabla de verificación sigue válida cambiando el header.

---
> **Estado original**: BORRADOR (Antigravity)  
> **Fase**: F1 · Infra monetización  
> **Owner ejecución**: F+A (diseño Fable, implementación delegada)  
> **Roadmap ref**: m2 (after m1, 4 días)  
> **Depende de**: m1 (diseño llaves por tier + scopes — decisión de Fable+G)

## Objetivo

Cuando un usuario compra una suscripción vía Paddle (checkout embebido en la
web de Abu Oracle), un webhook dispara la creación automática de una API key
en Firestore, y un email de bienvenida con la key se envía al comprador.

Esta es la **infraestructura central de monetización**: la misma key que
desbloquea endpoints pagos del engine (`/api/astro/biography`,
`/api/astro/relocation`, HF) es la que se usará para autenticar el MCP remoto
en Cloud Run (p4, julio). **El conector público autenticado ES el producto
B2B.**

## Contexto

### Patrón existente

El engine ya tiene un patrón de service key (`X-Abu-Service-Key` header) en
`config.py` (líneas 40-43, 54-61) y `abu_client.py` (líneas 21-26). Hoy es
una key única compartida (machine-to-machine). Este spec extiende el patrón a
**keys por usuario**, emitidas automáticamente al pago.

### Stack indicado en el roadmap

- **Paddle**: procesador de pagos (checkout + webhooks)
- **Firestore**: almacén de keys (ya usado en el proyecto web de Abu Oracle)
- **Resend**: envío de email transaccional (key al comprador)

### Tiers del roadmap

| Tier | Precio | Scopes esperados |
|---|---|---|
| Free | $0 | `cielo`, `doctrina`, `biblioteca` (endpoints públicos) |
| Monthly | $5/mes | + `natal`, `biografia`, `relocation` |
| Annual | $45/año | = Monthly |
| Genesis | $100 lifetime ×100 | = Monthly + badge Genesis |
| B2B/API | $50-200/mes | Todos + rate limits elevados |

> **⚠️ DECISIÓN PENDIENTE (m1, Fable+G):** schema exacto de scopes, rate
> limits por tier, expiración de keys. Este spec asume un modelo sencillo que
> Fable debe validar.

## Alcance

### 1. Webhook receiver (Cloud Function o Cloud Run endpoint)

- Endpoint: `POST /webhooks/paddle`
- Verifica la firma del webhook (Paddle signature verification)
- Parsea el evento `subscription.created` (y `subscription.activated`)
- Extrae: `customer_email`, `product_id` (→ mapeado a tier), `subscription_id`

### 2. Emisión de API key

- Genera key: `secrets.token_hex(32)` (64 chars hex, como la service key actual)
- Escribe en Firestore:

```
api_keys/{key_hash_sha256} → {
  key_prefix: "ak_...",      // primeros 8 chars para display
  customer_email: "...",
  tier: "monthly|annual|genesis|b2b",
  scopes: ["cielo", "doctrina", "biblioteca", "natal", "biografia"],
  paddle_subscription_id: "...",
  created_at: timestamp,
  active: true,
  usage: {
    total_calls: 0,
    last_call: null
  }
}
```

- La key se almacena hasheada (SHA-256). El texto plano se envía al usuario
  **una sola vez** por email. Si la pierde, se regenera (no se recupera).

### 3. Email de bienvenida (Resend)

- Template con: key en texto plano, instrucciones de uso (header
  `X-Abu-Api-Key`), link a docs, tier adquirido.
- Sender: `noreply@abu-oracle.com` o similar.

### 4. Middleware de validación en el engine

- El engine actual ya lee `X-Abu-Service-Key`. Se extiende para también aceptar
  `X-Abu-Api-Key` → lookup en Firestore → verificar `active: true` + scope
  incluye el endpoint solicitado.
- Rate limiting básico por key (leaky bucket o similar, configurable por tier).

### 5. Endpoint de revocación (admin)

- `POST /admin/keys/revoke` con service key de admin → marca `active: false`.

## NO alcance

- UI de gestión de keys (portal del usuario). Fase posterior.
- Rotación automática de keys. Manual para v1.
- Billing complejo (proration, upgrades mid-cycle). Paddle lo maneja.
- MCP remoto autenticado (p4, julio) — CONSUME esta infra pero se implementa
  aparte.

## Verificación

| Check | Criterio |
|---|---|
| Webhook e2e (sandbox) | Simular compra en Paddle sandbox → key aparece en Firestore → email recibido con key funcional |
| Key funciona | Llamar `GET /api/astro/biography` con `X-Abu-Api-Key: {key}` → 200 |
| Key inválida | Llamar con key inventada → 401 |
| Scope check | Llamar endpoint de tier superior con key de tier inferior → 403 |
| Revocación | Revocar key → siguiente llamada → 401 |
| Idempotencia | Webhook duplicado de Paddle no crea key duplicada |

## Preguntas abiertas para Fable

1. **Schema de scopes**: ¿lista plana de strings (`["cielo", "biografia"]`) o
   un enum de tiers con scopes implícitos? Lo segundo es más simple; lo primero
   permite combos custom (B2B).
2. **¿Firestore o Cloud SQL?** Firestore es el path de menor resistencia (ya
   existe en el proyecto). ¿Hay razón para SQL?
3. **Rate limiting**: ¿por key en el engine (middleware) o en un API gateway
   (Cloud Endpoints / Apigee)? Gateway es más robusto pero agrega complejidad.
4. **¿Key hash o key encriptada?** Hash (SHA-256) es irreversible — si se pierde,
   se regenera. Encriptada permite mostrarla en un portal futuro. Recomiendo
   hash para v1 (más seguro, más simple).
5. **Header name**: ¿`X-Abu-Api-Key` (nuevo) o reutilizar `X-Abu-Service-Key`
   con lookup dual? El segundo evita cambios en clientes existentes pero mezcla
   semánticas.
