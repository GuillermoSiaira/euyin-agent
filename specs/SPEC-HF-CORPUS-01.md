# SPEC-HF-CORPUS-01 — Corpus de relocalización para validación espacial del HF

> **Estado**: APROBADO (Fable+G, 2026-06-12) — el sustrato que faltaba.
> **Fase**: F1 · h3 (paralelo a impl. h4-h6; bloquea backtest espacial h7)
> **Owner**: AG (recolección + estructura) + G (verificación biográfica)
> **Depende de**: `SPEC-HF-V7-01` (define qué se mide). **Bloquea**: backtest espacial.

---

## 0. Por qué existe

El HF responde **una** pregunta: ¿dónde funciona mejor la vida del nativo? Validar
eso necesita eventos con **ubicación + fecha + valencia + dominio**. El corpus
actual (527 eventos) tiene carta+fecha+valencia+dominio pero **casi sin ubicación**
— solo GS_004 (n=26). Sin ubicaciones, el *dónde* nunca se pudo medir, y por eso
la compuerta espacial quedó siempre en "evidencia mixta".

**La solución son las celebridades.** Su vida está documentada: dónde vivieron,
desde cuándo, y qué les pasó ahí. Construir líneas de relocalización biográficas
da, por primera vez, un ground truth espacial.

---

## 1. Estructura del dato

Para cada sujeto, una **línea de relocalización**: tramos de residencia con
ubicación y fechas, y dentro de cada tramo, los eventos biográficos ocurridos
**en ese lugar**.

```json
{
  "subject": "Albert Einstein",
  "natal": { "date": "1879-03-14", "time": "11:30", "lat": 48.40, "lon": 9.99, "rodden": "AA" },
  "relocations": [
    {
      "place": "Zürich, Switzerland",
      "lat": 47.37, "lon": 8.54,
      "from": "1896-10", "to": "1902-06",
      "events": [
        { "date": "1900-07", "desc": "se gradúa en el ETH", "valence": "+", "domain": "h10", "rodden_event": "biografía" }
      ]
    },
    {
      "place": "Bern, Switzerland",
      "lat": 46.95, "lon": 7.45,
      "from": "1902-06", "to": "1909-10",
      "events": [
        { "date": "1905", "desc": "Annus Mirabilis — 4 papers", "valence": "+", "domain": "h10" },
        { "date": "1903-01", "desc": "casamiento con Mileva", "valence": "+", "domain": "h7" }
      ]
    }
  ]
}
```

Campos por evento: `date` (mín. año-mes), `desc`, `valence` (+/−/0), `domain`
(h1-h12 del esquema HF), `lat`/`lon` heredados del tramo. La ubicación del evento
**es la del tramo** (donde vivía cuando ocurrió) — eso es lo que el HF necesita.

---

## 2. Selección de sujetos (F0 inicial: 8-12)

Prioridad: celebridades del demo pack con **relocalizaciones mayores y bien
documentadas** (mudanza internacional = cambio de campo HF grande, señal limpia):

| Sujeto | Relocalizaciones clave |
|---|---|
| Einstein | Ulm → Zürich → Bern → Berlín → Princeton |
| Freud | Freiberg → Viena → Londres (1938) |
| Gandhi | India → Londres → Sudáfrica → India |
| Picasso | Málaga → Barcelona → París |
| Van Gogh | Países Bajos → París → Arlés → Saint-Rémy |
| Bowie | Londres → Los Ángeles → Berlín → Nueva York |
| Jung | Basilea → Zürich (estable — control de baja movilidad) |
| Tesla | Croacia → Budapest → París → Nueva York |

Jung como **control**: baja movilidad → el HF debería predecir poco cambio. Útil
para descartar que el modelo "vea" señal donde no hay relocalización.

---

## 3. Fuentes y método (AG)

- **Residencias**: Wikipedia (secciones biográficas), cronologías publicadas. Cada
  tramo con fecha de inicio aproximada (año-mes basta) y lat/lon de la ciudad
  (usar `data/external/worldcities.csv` para geocodificar).
- **Eventos**: cruzar con `data/biographical_events/*.json` ya existentes (varios
  de estos sujetos ya tienen eventos sin ubicación → **estampar la ubicación del
  tramo correspondiente**). Completar con eventos biográficos mayores faltantes.
- **Valencia/dominio**: seguir el criterio del corpus existente (mismo esquema de
  dominios h1-h12). Ante duda de valencia, marcar `"valence": "0"` y dejar para
  revisión de G — NO inventar.

**Regla dura**: cada evento debe ser **verificable** (fuente citable). AG marca
con `"source": "..."`. G verifica una muestra antes de aceptar el corpus. Mismo
principio que la skill: dato verificable o no entra.

---

## 4. Salida

- `data/hf_relocation_corpus/{subject_slug}.json` (uno por sujeto)
- `data/hf_relocation_corpus/index.json` — manifiesto: sujetos, n_tramos,
  n_eventos, balance de valencias, hash SHA-256 de cada archivo
- Reporte: total eventos con ubicación, balance +/−/0 por dominio, cobertura
  temporal. Meta mínima F0: **≥ 80 eventos ubicados** (vs 26 actuales) para que
  el test espacial tenga potencia mínima.

---

## 5. Verificación

| Check | Criterio |
|---|---|
| Estructura | JSON válido contra el schema de §1; lat/lon no nulos por tramo |
| Trazabilidad | cada evento con `source`; muestra de 10 verificada por G |
| Geocodificación | lat/lon de cada tramo coincide con la ciudad (±0.5°) |
| Balance | reportar +/−/0 por dominio; señalar dominios con N<10 (potencia baja) |
| Reuso | eventos ya en `biographical_events/` se reusan estampando ubicación, no se duplican |
| Volumen | ≥ 80 eventos ubicados en F0 |

---

## 6. NO alcance

- NO recolección masiva (los 5.359 sujetos) — F0 son 8-12 curados.
- NO inferir ubicación de eventos sin residencia documentada — si no se sabe dónde
  vivía, el evento no entra al corpus espacial (puede quedar en el temporal).
- NO modificar `biographical_events/` original — el corpus de relocalización es un
  artefacto nuevo que referencia/estampa, no muta la fuente.
- NO juicio de valencia automático por LLM sin verificación de G.
