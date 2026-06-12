# Roadmap EuYin / Abu Oracle — v2 · eje: MONETIZACIÓN

> Fuente de verdad del plan. v2: 2026-06-12 (reemplaza v1 — ver git history).
> Estrategia base: diálogo monetización post-MCP (2026-06-12). Objetivo:
> **lanzamiento agosto 2026** — Genesis Access a la venta + MCP público.
> Calibración: días/sesiones. Owners: **G** = Guillermo (decisiones, deploys,
> publicación) · **F** = Fable/Claude Code (arquitectura, juicio, specs) ·
> **A** = agente delegado vía spec (**Antigravity o Aider+Vertex AI**, indistinto —
> mismo criterio: espec-able y verificable se delega; juicio doctrinal/auth no).

## Tesis comercial (del diálogo 2026-06-12)

- El MCP convierte a Abu Oracle de **destino en infraestructura**: el motor vive
  donde la pregunta ocurre. La web no muere: **MCP distribuye, web convierte y cobra**.
- **El patrón de monetización ya existe**: endpoints gratis (cielo, mundana) +
  endpoints con llave (natal, biografía, HF). `Paddle → emisión de llave` =
  suscripción por capacidad. Tiers ya cargados: $5/mes · $45/año · $100 lifetime
  ×100 Genesis (venderlo como pertenencia, no descuento). Falta: tier **B2B/API**
  ($50-200/mes) como "contactame".
- **Dos audiencias, orden inverso al intuitivo**: (1) builders AI — atacable YA
  sin audiencia previa (Show HN, r/ClaudeAI, r/mcp, LinkedIn, directorios MCP:
  registry oficial, Smithery, PulseMCP, mcp.so, Glama); (2) consumidores
  astrología — se construye con meses de pipeline multiplataforma.
- **Safe Wallet = carril value-for-value paralelo** (publicar dirección: costo
  cero, hoy). El ingreso principal es Paddle. Cripto-rieles nuevos: NO hasta
  que el carril 1 facture.
- **HF v1 consistente = corazón del tier pago** (relocalización es la killer
  feature). Antiscios y aspectos nuevos = v2, cuando un suscriptor los pida.
- Timing propio del sistema: julio = Mercurio Rx (revisión, P0s, preparación);
  agosto = Mercurio directo + firdaria Sol/Marte (30-jul) → **lanzamiento**.

## KPIs (empezar a medir desde Fase 1)

| Métrica | Fuente | Baseline 12-jun | Meta 31-ago |
|---|---|---|---|
| Directorios MCP listados | manual | 0 | 5 |
| Instalaciones/usuarios MCP | logs engine (por key) | 1 (Guillermo) | 50 |
| Llaves emitidas (free→paid) | Firestore | 0 | 100 free · 10 paid |
| MRR | Paddle | $0 | primer MRR > $0 |
| Genesis vendidos | Paddle/Safe | 0 | 5 |
| Seguidores pipeline | Bluesky+X+IG | 13 | 300 |
| Donaciones Safe | on-chain | 0 | medir (sin meta) |

## Gantt

```mermaid
gantt
  dateFormat YYYY-MM-DD
  title Abu Oracle — monetización · jun-ago 2026
  axisFormat %d-%b

  section F0 · Cierres (12-17 jun)
  Resubir skill v3 + confirmar firdaria (G)      :f01, 2026-06-12, 1d
  Publicar dirección Safe en sitio/posts (G)     :f02, 2026-06-12, 1d
  Sanitizar repo + push GitHub euyin (F+G)       :f03, 2026-06-13, 2d
  Specs delegables iniciales (F)                 :f04, 2026-06-13, 2d
  OCR biblioteca — CA prioridad (A)              :f05, 2026-06-15, 4d

  section F1 · Infra monetización (16-30 jun)
  Diseño llaves por tier + scopes (F+G)          :m1, 2026-06-16, 2d
  Paddle webhook → emisión de llave (F+A)        :m2, after m1, 4d
  Metering por llave + /v1/me/usage real (A)     :m3, 2026-06-22, 3d
  Tier B2B "contactame" en sitio (G)             :m4, 2026-06-25, 1d
  Export NotebookLM HF (G)                       :h1, 2026-06-13, 1d
  Spec HF v7 + umbrales prereg (F+G)             :h2, 2026-06-17, 3d
  Backtest HF 527 eventos (A+F)                  :h3, 2026-06-22, 9d
  Compuerta HF: pasa/no pasa (G)                 :h4, 2026-07-06, 2d

  section F2 · Rx julio — preparar (1-31 jul)
  P0s engine — bugs vía specs (A)                :p1, 2026-07-01, 6d
  Pipeline Fase 1 multiplataforma X+IG (F+A)     :p2, 2026-07-01, 12d
  Runtime EuYin con juicio + aprobación móvil (F):p3, 2026-07-08, 8d
  MCP remoto auth por llave — Cloud Run (F+G)    :p4, 2026-07-13, 7d
  Listarse en 5 directorios MCP (G+F)            :p5, 2026-07-21, 3d
  Borradores Show HN / r-ClaudeAI / LinkedIn (F) :p6, 2026-07-21, 3d
  Dry-run pipeline completo (F+G)                :p7, 2026-07-24, 5d

  section F3 · LANZAMIENTO (agosto)
  Show HN + r-ClaudeAI + r-mcp + LinkedIn (G)    :l1, 2026-08-03, 3d
  Genesis Access a la venta (G)                  :l2, 2026-08-03, 2d
  Pipeline audiencia 2 en background             :l3, 2026-08-03, 12d
  Medición embudo + iteración (F+G)              :l4, 2026-08-06, 10d
```

## Dependencias duras

- `m1 → m2 → m3` y `m2 → p4` (el MCP remoto autenticado usa la MISMA infra de
  llaves — el conector público autenticado ES el producto B2B)
- `f03 (repo público sanitizado, sin fixtures personales ni secretos) → p5 (directorios)`
- `h1 (export NotebookLM — solo G puede) → h2 → h3 → h4`. Si la compuerta NO pasa,
  el lanzamiento sale igual: el tier pago lidera con natal+biografía y el HF queda
  "en validación" (regla content_generator: capacidad, no números)
- `p2/p3 → p7 → l3` · `p6 → l1` · julio Rx = preparar, NO lanzar; agosto = lanzar

## Postergado explícito (disciplina de foco)

- Antiscios + aspectos nuevos del HF → cuando un suscriptor pagante los pida
- Rieles cripto/ERC-8004 → cuando el carril Paddle facture
- Motor Doctrinal Comparado (Jyotish) → post-lanzamiento (sigue siendo el norte académico)
- Blind Validation / arXiv → continúa de fondo, sin fecha en este ciclo
- Embeddings biblioteca → cuando la recuperación BM25 quede corta en uso pago

## Specs para el delegado (Antigravity / Aider+Vertex)

| Spec | Fase | Contenido | Verificación |
|---|---|---|---|
| `SPEC-OCR-01` | F0 | OCR 10 PDFs sin texto (prioridad: Christian Astrology) | >200 chars/pág muestreados; reindex con chunks CA |
| `SPEC-KEYS-01` | F1 | Webhook Paddle → crear API key en Firestore + email Resend (sobre el patrón crypto-payment existente) | test e2e sandbox Paddle; key emitida funciona contra endpoint protegido |
| `SPEC-METER-01` | F1 | Metering por key + `/api/v1/me/usage` real (hoy devuelve mock) | usage refleja llamadas reales por key |
| `SPEC-P0S-01` | F2 | BUG-04 (LINK_LOST), BUG-09 (errores form), BUG-10 (alias BV) | repro + test por bug |
| `SPEC-HF-BACKTEST-01` | F1 | Runner backtest HF v7 vs 527 eventos held-out (espera spec h2) | métricas reproducibles, seed fija, JSON |
| `SPEC-PIPE-01` | F2 | Publishers X + Instagram sobre kernel existente + cola de aprobación | dry-run multiplataforma con drafts |
