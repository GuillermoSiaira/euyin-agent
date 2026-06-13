# SPEC-P0S-01 — Bugs P0 del Engine

> **Estado**: ⚠️ CORREGIDO SUSTANCIALMENTE (auditoría Fable 2026-06-12) — las tres
> "inferencias de síntoma" del borrador eran INCORRECTAS. Implementar SOLO lo que
> dice el bloque de auditoría; ignorar las secciones especulativas de abajo.

## ⚖️ AUDITORÍA FABLE — los bugs REALES (fuente: CLAUDE.md de ai-oracle, sección "Bugs Pendientes")

**Respuestas a las preguntas abiertas:** (1) los repro están documentados — van
abajo; (2) BUG-04 y BUG-09 viven en `next_app/` (web), BUG-10 en
`scripts/blind_validation/` — todo en el repo ai-oracle; (3) prioridad:
**BUG-10 > BUG-09 > BUG-04**.

### BUG-04 (real): LINK_LOST intermitente en `/api/chat`
- NO son "links rotos de la app". Es el chat conversacional de Lilly devolviendo
  el error `LINK_LOST` de forma intermitente en producción.
- Contexto: la route fue reescrita a Anthropic SDK directo (commit `3999611`) y el
  LINK_LOST sistemático se eliminó; el residual intermitente se sospecha de
  **cold start de Cloud Run + timeout** (>25s con max_tokens 2500).
- Tarea real: **diagnóstico instrumentado, no fix a ciegas** — agregar logging de
  duración/causa en `next_app/app/api/chat/route.ts`, revisar logs de Cloud Run de
  los últimos 30 días, reproducir con cold start forzado. Si se confirma timeout:
  streaming o keep-warm (min-instances=1 tiene costo — decisión G).
- Verificación: 20 requests tras 15 min de inactividad → 0 LINK_LOST.

### BUG-09 (real): error genérico en el formulario de carta
- NO es validación rota. Es que `birth-data-panel.tsx` + `services/abu.ts` muestran
  el mismo `formErrorGeneric` para CUALQUIER fallo: fecha inválida, ciudad no
  seleccionada, error de red, 401/403 del engine. El usuario no sabe qué corregir.
- Fix real: diferenciar 4 causas con mensajes específicos (validación local antes
  del fetch; catch de red vs status HTTP del engine) + i18n de los 4 mensajes
  (patrón existente en `lib/i18n.ts`, 4 idiomas).
- Verificación: provocar cada causa → mensaje distinto y accionable en los 4 idiomas.

### BUG-10 (real): fuga de identidad en Blind Validation — PRIVACIDAD
- NO es colisión de aliases. Es que `scripts/blind_validation/run_blind_validation.py`
  puede **filtrar el nombre real del nativo** (`subject_real`, `birth_city`) en
  outputs que deben ser ciegos. Bloqueante para las sesiones BV (no para el
  lanzamiento comercial).
- Fix conocido (documentado en CLAUDE.md): auto-generar alias opaco
  `NTV-{hash[:4].upper()}` e higienizar TODOS los campos de texto libre del output;
  `subject_real` solo en los archivos internos, jamás en stdout ni en la ficha.
- Verificación: correr una sesión BV de prueba → grep del nombre real sobre stdout
  y ficha generada → 0 ocurrencias; test automatizado de la higienización.

---
> **Estado original**: BORRADOR (Antigravity) — secciones siguientes SUPERSEDED  
> **Fase**: F2 · Rx julio  
> **Owner ejecución**: A (agente delegado)  
> **Roadmap ref**: p1 (2026-07-01, 6 días)

## Objetivo

Corregir tres bugs conocidos del engine que afectan la calidad percibida del
producto antes del lanzamiento. Cada bug tiene su propia sección con repro,
fix esperado y test.

> **⚠️ NOTA:** Este spec referencia bugs del engine (`ai-oracle`), no de este
> repo (`euyin-agent`). Necesito acceso al código del engine o specs de Fable
> con repro steps detallados para poder implementar. Las secciones de abajo
> están escritas en base a lo que dice el roadmap — los detalles de repro
> deben venir de Fable o de Guillermo.

---

## BUG-04: LINK_LOST

### Síntoma (inferido del nombre)

Links internos de la app web (`app.abu-oracle.com`) que se pierden o rompen
en algún flujo. Posibles escenarios:
- Links de sharing de carta que expiran o devuelven 404
- Deep links desde posts que no resuelven al contenido correcto
- Links de referral/CTA que pierden parámetros

### Repro

**[PENDIENTE — Fable/Guillermo]**: steps exactos de reproducción.

### Fix esperado

Depende del repro. Posibles áreas:
- Persistencia de URLs generadas (¿se invalidan en redeploy?)
- Routing del frontend (Next.js dynamic routes)
- Encoding de parámetros en URLs compartidas

### Verificación

- Generar link → cerrar/abrir browser → link resuelve correctamente
- Link funciona después de redeploy del engine/web
- Test automatizado: generar N links, verificar resolución

---

## BUG-09: Errores de formulario

### Síntoma (inferido)

El formulario de entrada de datos natales (fecha, hora, lugar de nacimiento)
en la web produce errores silenciosos o incorrectos. Posibles escenarios:
- Validación de fecha/hora que rechaza formatos válidos
- Geocoding del lugar que falla silenciosamente (lat/lon = 0,0)
- Timezone handling incorrecto (hora local vs UTC)
- El formulario no muestra errores al usuario cuando el engine devuelve error

### Repro

**[PENDIENTE — Fable/Guillermo]**: formulario específico, inputs que fallan,
error esperado vs error actual.

### Fix esperado

- Validación robusta de inputs con feedback visual
- Geocoding con fallback y error explícito si no resuelve
- Conversión timezone documentada y testeada

### Verificación

- Ingresar fecha en formatos variados (DD/MM/YYYY, YYYY-MM-DD, etc.) → acepta
- Ingresar ciudad inexistente → error claro, no lat/lon 0,0
- Ingresar hora sin timezone → comportamiento documentado (¿assume local? ¿UTC?)
- Test de regresión por cada input que falló en el repro original

---

## BUG-10: Alias BV (Blind Validation)

### Síntoma (inferido)

El sistema de Blind Validation usa alias para anonimizar cartas durante la
validación ciega. El bug sugiere que:
- Los alias no se resuelven correctamente al deanonimizar
- O los alias colisionan (dos cartas, mismo alias)
- O el mapping alias→carta se pierde entre sesiones

### Repro

**[PENDIENTE — Fable/Guillermo]**: flujo exacto de Blind Validation que falla.

### Fix esperado

- Si es colisión: usar UUID en vez de alias cortos
- Si es persistencia: verificar que el mapping se almacena y no es efímero
- Si es resolución: fix en el código de deanonimización

### Verificación

- Crear N cartas con alias → todas resuelven correctamente
- Reboot del servicio → aliases siguen resolviendo
- Test de colisión: generar 1000 alias → 0 duplicados

---

## Preguntas abiertas para Fable

1. **Los tres bugs necesitan repro steps concretos.** El roadmap los nombra
   pero no los describe. ¿Fable tiene los detalles o hay que reproducirlos
   desde cero en el engine?
2. **¿Los tres están en el engine (`ai-oracle`) o alguno está en la web
   (Next.js)?** Esto cambia quién los puede implementar (agente con acceso a
   ai-oracle vs trabajo en el frontend).
3. **¿Hay prioridad entre los tres?** ¿Alguno bloquea el lanzamiento más que
   los otros?
