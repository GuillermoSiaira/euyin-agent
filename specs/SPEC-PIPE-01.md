# SPEC-PIPE-01 — Publishers Multiplataforma + Cola de Aprobación

> **Estado**: ✅ APROBADO COMO DELTA (auditoría Fable 2026-06-12) — el alcance se
> reduce a lo que FALTA: el kernel ya está EN PRODUCCIÓN.

## ⚖️ AUDITORÍA FABLE

**El "kernel existente" no es solo `content_generator.py` — es un pipeline completo
corriendo en producción desde abril 2026** (Antigravity no lo vio):
- `scripts/mundana/main_publisher.py` → **Cloud Run Job `mundana-publisher` +
  Cloud Scheduler diario 08:00 UTC** (el cron de la pregunta 6 YA EXISTE)
- `content_generator.py` → 4 estilos CON rotación automática por día de semana YA
  implementada, voz Lilly, límites por plataforma, multi-idioma, RAG doctrinal
- `publishers/` → Bluesky (automático, funcionando), Twitter (semi-auto: draft +
  email Resend), Farcaster y Reddit (escritos, sin credenciales)
- `publication_filter.py` → juicio de publicación (umbrales de significancia +
  cooldown 3 días) — NO hay cuota fija diaria y eso es correcto
- `image_generator.generate_sky_diagram()` → **ya genera diagramas del cielo**
  (la imagen para IG existe)

**Alcance corregido — SOLO el delta:**
1. **Cola de aprobación** (Firestore `post_queue/`, schema del borrador APROBADO)
   insertada entre generate y publish en `main_publisher.py`, con bypass
   configurable (`APPROVAL_MODE=queue|direct` — Bluesky puede seguir directo).
2. **Aprobación por bot de Telegram** (pregunta 1: Telegram, decidido — y OJO:
   ya existe `cloudbuild-telegram-bot.yaml` en la raíz de ai-oracle; VERIFICAR qué
   hay construido antes de escribir una línea). Draft + botones Aprobar/Rechazar.
   La página web queda rechazada para v1.
3. **Publisher X directo** (reemplaza el draft-por-email) + **publisher Instagram**
   (Meta Graph API, usando `generate_sky_diagram` como imagen).
4. NADA más: no tocar selección, estilos, filtro, cron, ni generación.

**Respuestas a las preguntas restantes:**
2. **LLM**: el que ya usa el kernel — `claude-sonnet-4-6` vía Vertex con fallback
   API directa (ya configurado, con retry 429). No introducir Gemini: la voz de
   Lilly está calibrada en Claude y el costo de este volumen (≤2 posts/día) es
   irrelevante. Migrar la generación a la skill EuYin = v2, no este spec.
3. **Imagen IG**: `generate_sky_diagram` del kernel (coherente con la marca, ya
   escrito). AI-generated rechazado (off-brand, costo, y la skill prohíbe el
   decorativo vacío).
4. Respondida arriba — es mucho más que content_generator.
5. **Posts/día**: gobernado por `publication_filter` (señal + cooldown), NO cuota
   fija. Si G quiere más frecuencia se bajan umbrales — un env var, no
   arquitectura.
6. **El cron ya existe** (Scheduler → Cloud Run Job). Cero infraestructura nueva.

**Nota de verificación extra**: el límite del free tier de X API cambia seguido —
verificar el límite vigente de writes/mes al implementar, no asumir el 1.500 de la
tabla.

---
> **Estado original**: BORRADOR (Antigravity)  
> **Fase**: F2 · Rx julio  
> **Owner ejecución**: F+A (arquitectura Fable, implementación delegada)  
> **Roadmap ref**: p2 (2026-07-01, 12 días)

## Objetivo

Construir un pipeline que genere posts astrológicos (usando la skill
`lilly-interpretacion` + datos del MCP) y los publique en X (Twitter),
Instagram, y opcionalmente Bluesky — con una cola de aprobación móvil para
que Guillermo revise y apruebe cada post antes de publicarse.

El pipeline toma el cielo del día (vía `calcular_transitos`), selecciona la
configuración más relevante, genera un post con la voz de Lilly, lo pone en
cola, y espera aprobación. Aprobado → publica en las plataformas configuradas.

## Contexto

### Kernel existente

El roadmap menciona un "kernel existente" — posiblemente `content_generator.py`
en `ai-oracle`. El pipeline se construye **sobre** ese kernel, no desde cero.

### Skill de interpretación

La skill `lilly-interpretacion` (en este repo) define:
- Los 4 movimientos de un post (gancho, medición, doctrina, CTA)
- 4 estilos rotativos (stats, individual, geographic, doctrine)
- Límites por plataforma (twitter 280, bluesky 300, instagram 2200, etc.)
- Restricciones de voz (no "energía", no genérico, no oracular)

### Flujo esperado

```
[CRON diario] → calcular_transitos() → seleccionar config más relevante
    → traer_doctrina(tema) + consultar_biblioteca(tema)
    → LLM genera post (con skill lilly-interpretacion)
    → formatea por plataforma (respetando límites de caracteres)
    → encola para aprobación
    → [Guillermo aprueba en móvil]
    → publica en X + IG + Bluesky
```

## Alcance

### 1. Generador de contenido (daily job)

- **Trigger**: cron diario (Cloud Scheduler → Cloud Function/Run)
- **Selección**: del output de `calcular_transitos()`, elegir la configuración
  con menor orbe (más exacta) y fase `aplicativo` (preferencia por lo que viene)
- **Retrieval**: `traer_doctrina` + `consultar_biblioteca` sobre el tema de la
  configuración seleccionada
- **Generación**: llamada a LLM (Gemini o Claude) con la skill
  `lilly-interpretacion` como system prompt, y los datos del cielo + doctrina
  como contexto
- **Formateo**: generar variantes por plataforma respetando límites de chars
- **Estilo**: rotar entre los 4 estilos (stats, individual, geographic,
  doctrine) — tracking de qué estilo se usó últimamente

### 2. Cola de aprobación

- **Storage**: Firestore collection `post_queue/`
- **Schema**:

```json
{
  "id": "auto",
  "created_at": "2026-07-15T08:00:00Z",
  "status": "pending|approved|rejected|published",
  "cielo_fecha": "2026-07-15",
  "configuracion": "Mars square Saturn, orb 1.2°",
  "estilo": "doctrine",
  "posts": {
    "twitter": { "text": "...", "chars": 278 },
    "bluesky": { "text": "...", "chars": 295 },
    "instagram": { "text": "...", "chars": 1850, "image_url": null }
  },
  "doctrina_usada": ["fragmento 1...", "fragmento 2..."],
  "approved_by": null,
  "approved_at": null,
  "published_at": null,
  "publish_errors": {}
}
```

### 3. Interfaz de aprobación (móvil-friendly)

- **Mínima viable**: una página web estática (PWA o simple HTML) que:
  - Lista posts pendientes
  - Muestra preview por plataforma
  - Botones: Aprobar / Rechazar / Editar texto
  - Auth: Firebase Auth (solo Guillermo)
- **Alternativa aún más simple**: bot de Telegram que envía el draft y espera
  👍/👎. Más rápido de implementar, nativo en móvil.

> **⚠️ DECISIÓN FABLE:** ¿Página web mínima o bot de Telegram? El bot es más
> rápido de construir y más cómodo en móvil. La página web es más extensible.

### 4. Publishers

APIs de publicación por plataforma:

| Plataforma | API | Auth | Nota |
|---|---|---|---|
| X (Twitter) | Twitter API v2 | OAuth 2.0 + Bearer token | Free tier: 1,500 tweets/mes |
| Instagram | Meta Graph API | Long-lived token | Requiere Business Account + Facebook Page |
| Bluesky | AT Protocol | App password | API abierta, sin rate limit estricto |

- Cada publisher es un módulo independiente (`publishers/twitter.py`,
  `publishers/instagram.py`, etc.)
- Retry con backoff exponencial
- Logging de resultado (éxito/error) en el documento de la cola

### 5. Imágenes para Instagram

Instagram requiere imagen. Opciones:
- Generar imagen con la carta del cielo (el engine puede renderizar SVG)
- Template estático con texto overlay (Pillow/ImageMagick)
- Imagen generada con AI (DALL-E / Imagen) basada en la configuración

> **⚠️ DECISIÓN FABLE:** ¿Qué approach para la imagen de IG?

## NO alcance

- Scheduling (programar publicación para una hora específica). V1 publica
  inmediatamente al aprobar.
- Analytics de engagement por post. Futuro.
- Respuesta automática a comentarios/replies.
- TikTok y Reddit (mencionados en la skill pero postergados — el roadmap
  dice "Fase 1 X+IG").
- Facebook (mencionado en la skill, no en el Gantt de p2).

## Verificación

| Check | Criterio |
|---|---|
| Dry-run completo | El pipeline genera post → encola → se aprueba → se "publica" en modo draft (no real) |
| Límites respetados | Cada variante por plataforma respeta el límite de chars |
| Voz correcta | Post generado pasa las restricciones de la skill (no "energía", no genérico, cita doctrinal) |
| Aprobación funciona | Post en estado `pending` → aprobar → cambia a `approved` → publisher lo publica |
| Rechazo funciona | Rechazar un post → no se publica, status `rejected` |
| Error handling | Si la API de una plataforma falla, las otras siguen publicando; error se loguea |
| Multiplataforma | Un post aprobado se publica en X + Bluesky + IG simultáneamente |

## Preguntas abiertas para Fable

1. **¿Página web de aprobación o bot de Telegram?** Para v1, el bot es más
   rápido. ¿Fable tiene preferencia?
2. **¿Qué LLM para la generación?** ¿El mismo Fable (Claude), Gemini, o un
   modelo más barato (Haiku/Flash)? El skill es lo suficientemente prescriptivo
   como para funcionar bien con un modelo menor.
3. **¿Imágenes para IG**: render de carta SVG, template con overlay, o
   generación AI? El SVG del engine es lo más coherente con la marca.
4. **¿El "kernel existente" es `content_generator.py`?** Necesito verlo para
   no reimplementar lo que ya existe.
5. **¿Cuántos posts por día?** ¿1 diario fijo, o variable según la relevancia
   del cielo (más posts cuando hay configuraciones más exactas)?
6. **¿El cron corre en Cloud Run (job), Cloud Functions, o un scheduled
   GitHub Action?** Cloud Run job es más natural si todo lo demás está ahí.
