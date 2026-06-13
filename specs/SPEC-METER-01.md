# SPEC-METER-01 — Metering por Key + /v1/me/usage Real

> **Estado**: ✅ APROBADO CON CORRECCIONES (auditoría Fable 2026-06-12)  

## ⚖️ AUDITORÍA FABLE

**Corrección estructural**: todo el metering vive en `users/{uid}` (donde ya están
`api_key`, `quota_used`, `quota_limit` y donde `verify_token` YA incrementa
`quota_used` fire-and-forget) — **no en una colección `api_keys/` que no existe**
(ver auditoría SPEC-KEYS-01). Extender el update existente, no crear un write path
nuevo. Reemplazar `api_keys/{key_hash}` por `users/{uid}` en todo el spec.

**Respuestas a las preguntas abiertas:**
1. **Solo counters atómicos** — concuerdo. `usage_log` detallado rechazado para v1
   (latencia + costo Firestore). El log fino, si hace falta, ya existe gratis en
   Cloud Logging (el engine loguea cada request con path+status+dur_ms vía
   `log_event` — minarlo antes que duplicarlo).
2. **Comparación de fecha, sin cron.** Guardar `usage.daily_date: "YYYY-MM-DD"`
   (SIEMPRE UTC — no hay timezone del usuario que valga: es una API). Al validar:
   si `daily_date != hoy_utc` → reset `calls_today=0` + set fecha, en el mismo
   update. El edge case desaparece fijando UTC por contrato. Cero infraestructura.
3. **Hard 429** — concuerdo. Con `Retry-After` hasta medianoche UTC.
4. **Síncrono** — concuerdo (~30ms es nada a este volumen). Nota: que el increment
   sea fire-and-forget como el patrón actual (try/except, no bloquea la respuesta);
   solo la LECTURA del límite es bloqueante.

**Límites por tier**: la tabla propuesta queda APROBADA como inicial con un cambio —
B2B no se hardcodea: `quota_limit`/`daily_limit` se leen del doc del usuario (ya
existen como campos), los defaults por plan son fallback. Así un B2B custom se
ajusta editando su doc, sin deploy.

---
> **Estado original**: BORRADOR (Antigravity)  
> **Fase**: F1 · Infra monetización  
> **Owner ejecución**: A (agente delegado)  
> **Roadmap ref**: m3 (2026-06-22, 3 días)  
> **Depende de**: SPEC-KEYS-01 (keys emitidas y validadas en Firestore)

## Objetivo

Registrar cada llamada autenticada al engine por API key, y exponer un
endpoint real `GET /api/v1/me/usage` que devuelva el consumo acumulado del
usuario. Hoy ese endpoint devuelve datos mock — este spec lo conecta a datos
reales.

El metering es prerequisito para:
- Rate limiting informado (saber si una key excede su cuota)
- Dashboard de uso para el usuario (futuro)
- Detección de abuso
- Decisiones de pricing basadas en datos (cuánto consume un usuario promedio)

## Contexto

### Estado actual

El endpoint `/api/v1/me/usage` ya existe en el engine pero devuelve un mock
hardcodeado. Las llamadas no se registran.

### Patrón de auth (post SPEC-KEYS-01)

Cada request autenticado ya pasa por el middleware de validación de key, que
hace lookup en Firestore y obtiene el documento de la key. El metering se
inserta **en ese mismo middleware**, después de la validación exitosa.

## Alcance

### 1. Registro de llamadas (write path)

Después de que el middleware valida la key y antes de pasar el request al
handler, registrar:

```python
# Atómico en Firestore (o batch write al final del request)
api_keys/{key_hash}/usage_log/{auto_id} → {
  endpoint: "/api/astro/biography",
  timestamp: server_timestamp,
  status: 200,          # se actualiza post-response
  latency_ms: 342,      # se actualiza post-response
}

# Counters agregados (increment atómico)
api_keys/{key_hash}.usage.total_calls += 1
api_keys/{key_hash}.usage.calls_today += 1    # reset diario
api_keys/{key_hash}.usage.last_call = now
api_keys/{key_hash}.usage.by_endpoint.{endpoint} += 1
```

**Alternativa liviana** (recomendada para v1): NO escribir `usage_log` detallado
— solo incrementar los counters atómicos. El log detallado agrega latencia y
costo de Firestore. Activar solo si se necesita debugging o auditoría.

### 2. Endpoint /api/v1/me/usage (read path)

```
GET /api/v1/me/usage
Header: X-Abu-Api-Key: {key}

Response 200:
{
  "key_prefix": "ak_3f8a...",
  "tier": "monthly",
  "usage": {
    "total_calls": 142,
    "calls_today": 7,
    "calls_this_month": 89,
    "last_call": "2026-06-22T14:30:00Z",
    "by_endpoint": {
      "/api/astro/biography": 45,
      "/api/astro/chart-detailed": 97
    }
  },
  "limits": {
    "daily": 100,         // según tier
    "monthly": 3000,
    "remaining_today": 93
  }
}
```

### 3. Rate limiting (enforcement)

- Leer `calls_today` del counter antes de procesar el request.
- Si `calls_today >= daily_limit[tier]` → responder `429 Too Many Requests`
  con header `Retry-After`.
- Límites por tier (propuesta — **decisión Fable+G**):

| Tier | Daily | Monthly |
|---|---|---|
| Free | 20 | 500 |
| Monthly | 100 | 3,000 |
| Annual | 100 | 3,000 |
| Genesis | 200 | 6,000 |
| B2B | 1,000 | 30,000 |

### 4. Reset de counters diarios

- Cloud Scheduler job (cron `0 0 * * *` UTC) que resetea `calls_today` en
  todas las keys activas. O bien: comparar `last_call` date vs today al leer.
  La segunda opción no requiere cron pero es ligeramente más compleja.

## NO alcance

- Dashboard de uso con UI. Solo el endpoint JSON.
- Alertas de uso (email cuando se acerca al límite). Futuro.
- Billing por uso (pay-per-call). El modelo es suscripción fija.
- Metering de endpoints públicos (sin key). Solo se mide tráfico autenticado.

## Verificación

| Check | Criterio |
|---|---|
| Counter incrementa | Hacer 3 llamadas con key → `/me/usage` muestra `total_calls: 3` |
| By endpoint | Llamar 2 endpoints distintos → `by_endpoint` refleja ambos |
| Rate limit | Exceder `daily_limit` → siguiente llamada → 429 |
| Reset diario | Después del reset (o al día siguiente) → `calls_today: 0`, `total_calls` intacto |
| Key inválida | `/me/usage` sin key → 401 |
| Mock eliminado | El endpoint ya no devuelve datos hardcodeados |

## Preguntas abiertas para Fable

1. **¿Counters atómicos o log detallado?** Recomiendo solo counters para v1
   (menos costo Firestore, menor latencia). ¿Fable concuerda?
2. **¿Reset por cron o por comparación de fecha?** Cron es más limpio pero
   agrega infraestructura. Comparación es self-contained pero tiene edge cases
   (timezone del usuario vs UTC).
3. **¿Los rate limits son hard (429) o soft (warn + log)?** Hard es más
   seguro para v1 — evita sorpresas de costos.
4. **¿Metering síncrono o asíncrono?** Síncrono (Firestore increment en el
   request path) agrega ~30ms de latencia. Asíncrono (queue + Cloud Function)
   es más performante pero no garantiza conteo exacto en tiempo real. Para los
   volúmenes iniciales (<1000 req/día), síncrono es aceptable.
