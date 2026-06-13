# SPEC-HF-BACKTEST-01 — Runner Backtest Harmony Field v7

> **Estado**: ⚠️ CORREGIDO — dos errores metodológicos graves (auditoría Fable 2026-06-12)

## ⚖️ AUDITORÍA FABLE — leer antes que nada

**Error 1 — "held-out por diseño" es FALSO.** Los 527 eventos
(`ai-oracle/data/biographical_events/*.json` + `biographical_events_v2/`) **SÍ se
usaron para calibrar**: el grid search de pesos del HF (9.261 combinaciones,
documentado en CLAUDE.md) corrió sobre este corpus, y las correlaciones de Fase 4/6
también. Backtestear v7 sobre los 527 completos es evaluación in-sample — invalidaría
la compuerta y cualquier claim público. **Protocolo corregido (obligatorio):**
- Split train/test estratificado por dominio, seed fija, congelado ANTES de calibrar
  v7 (el split se commitea como JSON con hash). v7 se calibra SOLO con train; la
  compuerta (h4) se evalúa SOLO con test.
- Limitación a documentar en el output: el test split influyó en versiones ancestras
  (v3/v6); el gold standard futuro son eventos recolectados post-v7. La compuerta
  igual es informativa: mide si v7 generaliza mejor que el azar en datos que no
  tocó directamente.

**Error 2 — "ubicación del evento" casi no existe en el corpus.** Solo GS_004
(26 eventos) tiene lat/lon por evento; el resto tiene carta natal + fecha + valencia
+ dominio. El diseño "percentil del HF en la ubicación del evento" es imposible para
~500 eventos. **Métricas corregidas** (las que el corpus soporta, mismas familias que
Fase 4/6): correlación HF↔valencia por dominio, Cohen's d, Mann-Whitney/rank-biserial
— donde el HF se evalúa en la dimensión temporal/dominio del evento. El análisis
espacial puro queda como sub-experimento sobre GS_004 únicamente (n=26, reportado
aparte y con esa salvedad).

**Respuestas a las preguntas abiertas:**
1. Sí, h2 es bloqueante y lo escribo yo con G — este runner no arranca antes.
2. **Import directo** — el runner vive en ai-oracle junto al engine. Ojo:
   `harmony_field.py` no existe; los módulos reales son `abu_engine/harmony/field_v3.py`,
   `resonance.py`, `houses.py`, `angularity.py` (v7 definirá el suyo en h2).
3. **El corpus ya existe como JSON** en las rutas de arriba — no hay que parsear
   nada de NotebookLM (el export h1 es para el DISEÑO de v7, no para el corpus).
4. **Plotting fuera** — concuerdo. JSON + script post-hoc.

Lo demás del borrador (reproducibilidad por seed/hash/version pin, output JSON,
runner-no-decide) queda APROBADO — está bien pensado.

---
> **Estado original**: BORRADOR (Antigravity)  
> **Fase**: F1 · Infra monetización  
> **Owner ejecución**: A+F (runner delegado, juicio Fable)  
> **Roadmap ref**: h3 (2026-06-22, 9 días)  
> **Depende de**: h2 (Spec HF v7 + umbrales prereg — Fable+G, 2026-06-17)

## Objetivo

Construir un runner reproducible que evalúe el Harmony Field v7 contra un
corpus held-out de 527 eventos biográficos, generando métricas de precisión
que alimenten la compuerta go/no-go (h4, 2026-07-06).

El HF v1 consistente es el **corazón del tier pago**: la relocalización es la
killer feature. Este backtest determina si la versión actual es suficientemente
fiable para venderla.

## Contexto

### ¿Qué es el Harmony Field?

Un campo escalar geográfico que calcula, para cada punto de la tierra, la
angularidad agregada de los planetas de una carta natal. Mayor angularidad =
mayor activación = condiciones más favorables para manifestar resultados en
ese dominio de vida. Es geometría computacional sobre efemérides, no un modelo
estadístico entrenado.

### Corpus held-out

527 eventos biográficos con:
- Fecha/hora/lugar de nacimiento (carta natal)
- Evento biográfico (tipo: mudanza, logro profesional, crisis, etc.)
- Ubicación del evento
- Dominio de vida afectado (casa astrológica)

Este corpus fue recopilado para validación y **nunca fue usado para calibrar
el HF**. Es held-out por diseño.

### Métrica esperada

Para cada evento, el runner calcula:
1. El HF del dominio relevante en la ubicación del evento
2. El percentil de esa ubicación vs distribución global del HF
3. Si el evento ocurrió en una zona de "alta resonancia" (umbral TBD en h2)

La métrica agregada es: **¿qué porcentaje de los 527 eventos ocurrió en
zonas de alta resonancia, vs lo esperado por azar (baseline)?**

> **⚠️ BLOQUEADO POR h2:** Los umbrales de "alta resonancia" y la definición
> exacta de HF v7 (qué planetas, qué orbes, qué pesos por dominio) son
> decisión de Fable+G en el spec h2. Este borrador describe el **runner**, no
> los umbrales.

## Alcance

### 1. Runner script

```
python scripts/hf_backtest.py \
  --corpus data/hf_corpus/events_527.json \
  --hf-version v7 \
  --seed 42 \
  --output results/hf_backtest_v7_$(date).json
```

- Lee el corpus de eventos
- Para cada evento: calcula HF en la ubicación del evento (llamando al engine
  o calculando directamente con `abu_engine/core/harmony_field.py`)
- Compara contra baseline (distribución nula: mismos eventos, ubicaciones
  shuffleadas con seed fija)
- Output: JSON con métricas por evento y agregadas

### 2. Reproducibilidad

- **Seed fija** para todo lo aleatorio (shuffle de baseline)
- **Versión del engine pinneada** (git hash o Docker tag)
- **Corpus versionado** (hash SHA-256 del JSON de entrada)
- El mismo comando con los mismos inputs produce el mismo output, byte a byte

### 3. Output JSON

```json
{
  "meta": {
    "hf_version": "v7",
    "corpus_hash": "sha256:abc...",
    "engine_version": "git:def456",
    "seed": 42,
    "timestamp": "2026-06-30T...",
    "n_events": 527,
    "thresholds": { "high_resonance_percentile": 75 }
  },
  "aggregate": {
    "events_in_high_resonance": 287,
    "expected_by_chance": 132,
    "hit_rate": 0.544,
    "baseline_rate": 0.250,
    "p_value": 0.00001,
    "effect_size": 0.294
  },
  "by_domain": {
    "H10_career": { "n": 89, "hits": 52, "hit_rate": 0.584 },
    "H7_partnership": { "n": 63, "hits": 31, "hit_rate": 0.492 }
  },
  "per_event": [
    {
      "event_id": 1,
      "domain": "H10_career",
      "location": { "lat": 40.71, "lon": -74.01 },
      "hf_score": 0.82,
      "percentile": 91,
      "in_high_resonance": true
    }
  ]
}
```

### 4. Compuerta go/no-go (alimenta h4)

El runner NO decide. Genera las métricas. La decisión la toma Guillermo (h4)
comparando contra umbrales definidos en h2.

## NO alcance

- Calibración de parámetros del HF (eso es diseño, no backtest)
- UI de resultados (solo JSON + script de plotting opcional)
- Nuevos eventos al corpus (held-out se mantiene cerrado)
- Antiscios o aspectos nuevos (postergados explícitamente en el roadmap)

## Verificación

| Check | Criterio |
|---|---|
| Reproducibilidad | Correr 2 veces con misma seed → output idéntico |
| Corpus integridad | Hash del corpus de entrada coincide con el registrado |
| Baseline sensata | baseline_rate ≈ 0.25 (si umbral = percentil 75) |
| Performance | Corre en <30 min para 527 eventos (batch, no one-by-one API calls) |
| Output parseable | JSON válido, schema validable |

## Preguntas abiertas para Fable

1. **Spec h2 es bloqueante.** Este runner necesita: definición exacta de HF v7
   (planetas, orbes, pesos), umbrales de alta resonancia, y el formato del
   corpus de entrada. Todo eso viene de h2.
2. **¿Calcular HF vía API del engine o vía import directo de `harmony_field.py`?**
   Directo es ~100x más rápido (evita 527 HTTP round-trips) pero acopla el
   runner al engine internals. ¿Qué prefiere Fable?
3. **¿El corpus de 527 eventos ya existe como JSON estructurado o hay que
   parsearlo de otra fuente?** (ej. de un export de NotebookLM, ver h1).
4. **¿El plotting (gráficos de resultados) es parte de este spec o es un spec
   aparte?** Recomiendo dejarlo fuera y hacer un script rápido post-hoc.
