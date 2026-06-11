# Roadmap EuYin / Abu Oracle — junio-julio 2026

> Fuente de verdad del plan. Actualizado: 2026-06-11.
> Calibración: tareas medidas en **días/sesiones** (trabajo diario con agentes).
> Owners: **G** = Guillermo (decisiones, deploys, doctrina) · **F** = Fable/Claude Code
> (arquitectura, juicio doctrinal) · **A** = Antigravity vía spec (mecánico espec-able).

## Criterio de delegación a Antigravity

**Se delega** lo espec-able y verificable mecánicamente: OCR, runners de backtest,
embeddings, fixes con tests claros. **No se delega**: juicio doctrinal (skill,
secta, correcciones de corpus), arquitectura/auth, prompts de Lilly, decisiones
de producto.

Flujo: F redacta spec en `ai-oracle/.claude/specs/active/SPEC-*.md` → Antigravity
ejecuta → review acá (F) → merge → spec a `specs/done/`.

**Specs a redactar primero (12-jun):**
| Spec | Contenido | Verificación |
|---|---|---|
| `SPEC-OCR-01` | OCR (tesseract/PyMuPDF) de los 10 PDFs sin capa de texto en `astro-texts/` — prioridad 1: `Lilly_William-Christian_astrology.pdf` (444 págs) | texto extraído >200 chars/pág en muestreo; reindex produce chunks CA |
| `SPEC-BV-ALIAS-01` | BUG-10: alias opaco `NTV-{hash[:4]}` en run_blind_validation.py + limpieza de campos identificables | stdout sin subject_real ni ciudad; test incluido |
| `SPEC-HF-BACKTEST-01` | Runner de backtest HF v7 contra 527 eventos held-out (cuando D2 defina la spec del algoritmo) | métricas reproducibles, seed fija, reporte JSON |

## Gantt

```mermaid
gantt
  dateFormat YYYY-MM-DD
  title EuYin / Abu Oracle — jun-jul 2026
  axisFormat %d-%b

  section A · Consolidación
  Deploy service key (G)              :a1, 2026-06-11, 1d
  Housekeeping Desktop+skill+GitHub (G):a2, 2026-06-11, 1d
  Verificación prod suite (F)         :a3, after a1, 1d
  Auditoría secta en fixtures (F)     :a4, 2026-06-12, 1d
  Doctrina faltante orbes+H3/H8/H11 (G+F):a5, 2026-06-12, 2d

  section B · Biblioteca
  Redactar 3 specs Antigravity (F)    :b1, 2026-06-12, 1d
  OCR 10 PDFs — CA prioridad (A)      :b2, after b1, 4d
  Reindex + QA corpus (F)             :b3, after b2, 1d
  Separar fixtures personales (F)     :b4, 2026-06-17, 1d
  Embeddings upgrade (A, stretch)     :b5, 2026-06-22, 3d

  section C · Runtime diario
  Diseño loop + juicio publicación (G+F):c1, 2026-06-15, 1d
  Implementación Agent SDK (F)        :c2, after c1, 3d
  Dry-run 3 días (F+G)                :c3, after c2, 3d
  Deploy Job + scheduler (G)          :c4, after c3, 1d
  Posts en vivo + monitoreo           :c5, after c4, 14d

  section D · HF compuerta
  Export NotebookLM (G)               :d1, 2026-06-13, 1d
  Spec HF v7 + umbrales prereg (F+G)  :d2, 2026-06-16, 3d
  Backtest 527 eventos (A+F)          :d3, 2026-06-22, 10d
  Decisión compuerta pasa/no-pasa (G) :d4, 2026-07-06, 3d

  section E · Conector público
  MCP HTTP + deploy Cloud Run (F+G)   :e1, 2026-06-24, 3d
  Auth + rate-limit + beta privada    :e2, 2026-06-29, 5d
  Beta pública / listing (G)          :e3, 2026-07-06, 5d

  section F · Investigación
  Fix BUG-10 alias opaco (A)          :f1, 2026-06-13, 2d
  Blind Validation sesiones 2-10 (G+F):f2, 2026-06-17, 20d
  Motor comparado Jyotish (F+G)       :f3, 2026-07-06, 10d
```

## Dependencias duras

- `A1 → A3 → linea_biografica en prod` (sin deploy de la key, la tool solo anda local)
- `B1 → B2 → B3` (el OCR alimenta el reindex)
- `B4 → E1` (**privacidad**: no exponer el MCP público con fixtures personales en el corpus)
- `D1 → D2 → D3 → D4` (sin export de NotebookLM no hay spec HF v7)
- `F1 → F2` (BUG-10 bloquea Blind Validation)
- `C4` y `E1` requieren deploys de G

## Hitos

| Fecha | Hito |
|---|---|
| 12-jun | linea_biografica viva en producción |
| 17-jun | Christian Astrology completa en la biblioteca |
| 22-jun | EuYin publica sola (runtime en producción) |
| ~3-jul | Backtest HF v7 terminado → datos para la compuerta |
| ~10-jul | Conector público en beta |
| ~17-jul | Primer experimento Motor Comparado (Lilly vs Jyotish) |

## Backlog sin fecha (se prioriza al cerrar lo anterior)

- BUG-04 (LINK_LOST /api/chat) · BUG-09 (errores form genéricos) — delegables vía spec
- Eval loop formal de la skill (iteration-2 con feedback de uso real) + description optimization
- Tool `puntaje_dominio` (HF por ciudad vía /api/astro/domain-score)
- Astrología horaria (prioridad 5 del roadmap de Lilly)
- OIDC para reemplazar service key estática (madurez de seguridad)
- arXiv Blind Validation (requiere F2 ≥ 10 sesiones)
