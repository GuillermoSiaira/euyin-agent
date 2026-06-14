# SPEC-MCP-TOOLS-01 — Expansión del toolset del MCP (4 tools no-gateadas)

> **Estado**: APROBADO (Fable+G, 2026-06-13). Verificado contra engine vivo.
> **Fase**: F1/F2 · paralelo a la cadena HF (toca `euyin-agent/mcp_server/`, otro repo).
> **Owner**: A (delegado) — wrappers finos sobre endpoints existentes. Revisión: F.
> **Depende de**: nada. Relocalización queda FUERA (gateada por h8 + guardrail habitabilidad).

## Principio

El MCP autenticado **es el producto B2B** (roadmap p4). Más tools = más valor.
Todas las tools son **wrappers finos sobre endpoints que el engine YA expone** — el
MCP no computa nada (toda la lógica determinista vive en el engine). El cliente
`abu_client.py` ya manda `auth_headers()` (service key), así que los endpoints
protegidos funcionan igual que `biography`.

## Estado actual (verificado 2026-06-13)

5 tools: `calcular_transitos`, `cielo_instante`, `traer_doctrina`,
`consultar_biblioteca`, `linea_biografica`.

`chart-detailed` (que usan `calcular_transitos` y `cielo_instante`) devuelve:
positions (con `dignity_traditional`, `house`), aspects, `arabic_parts`
(**solo `part_of_fortune`**), houses, asc, mc. **NO devuelve `sect`, ni los otros
lotes, ni señores de ASC/MC.** Ese es el hueco principal.

## Tools a agregar (4 — ninguna gateada)

### 1. `carta_natal(fecha, lat, lon)` — PRIORIDAD ALTA · tier pago

El hueco más grave: hoy ninguna tool da el frame doctrinal completo de una carta.
- **Endpoint**: `GET /api/astro/analyze` (protegido — usa la auth que ya manda el
  cliente). Es la fuente de `abuData`: trae `sect`, planetas con dignidades+casas,
  `derived.lots` (Fortuna/Espíritu/Eros/Necesidad con su señor), profección, firdaria.
  *(Verificar el path exacto: puede ser `/analyze` o `/api/astro/analyze` — confirmar
  contra `abu_engine/main.py` antes de escribir.)*
- **Qué AGREGA sobre `cielo_instante`** (justifica no ser duplicado): `sect`
  (nivel 1 de la jerarquía de juicio), lotes completos (no solo Fortuna), señor del
  año de la profección, firdaria activo. `cielo_instante` sigue siendo "carta de un
  momento+lugar" (horaria/eventos); `carta_natal` es "la identidad natal doctrinal".
- **Salida** (shape sugerido, null-safe): `{fecha, ubicacion, secta, ascendente,
  medio_cielo, posiciones[{planeta,signo,grado,casa,dignidad,retrogrado}],
  lotes[{nombre,signo,grado,casa,senor,senor_dignidad}], profeccion{casa,signo,senor},
  firdaria{mayor,menor,cierre}, fuente}`.

### 2. `revolucion_solar(fecha_nacimiento, lat, lon, anio, ciudad?)` — MEDIA-ALTA · tier pago

- **Endpoint**: `GET /api/astro/solar-return` (verificar params exactos en main.py:
  birthDate, lat, lon, year, y ciudad/lat-lon de relocalización SR opcional).
- **Salida**: datetime del SR, posiciones del retorno, ASC/MC del SR, aspectos.
  Pulso anual — distinto cada año.

### 3. `lunaciones_eclipses(fecha, lat, lon)` — MEDIA · tier gratis

- **Endpoint**: `GET /api/astro/lunar` (existe, no expuesto en ninguna tool).
- **Salida**: sol/luna (signo/grado), fase (nombre/%/separación), próxima luna
  nueva y llena (con días restantes), próximo eclipse solar y lunar (tipo/signo/
  casa natal). Pulso lunar mensual.

### 4. `mundana_pronostico(dias=90, tipo_config?)` — BAJA-MEDIA · tier gratis

- `calcular_transitos` ya enriquece con `mundana sky+forecast` → esta tool agrega
  acceso **directo y explícito** + el endpoint de **historia** que hoy no se expone.
- **Endpoints**: `GET /api/mundana/forecast?days=` + `GET /api/mundana/sky` +
  `GET /api/mundana/history?config_type=` (este último NO está expuesto en ninguna
  tool). Graceful `None` si el router mundana no está en la imagen (patrón ya en
  `abu_client.mundana_sky`).
- **Salida**: configuraciones activas + próximas (con p-value/densidad) + contexto
  histórico por tipo de configuración.

## Tiering (coincide con KEYS-01)

| Tier | Tools |
|---|---|
| **Gratis** (sin key / key free) | `cielo_instante`, `traer_doctrina`, `consultar_biblioteca`, `calcular_transitos`, **`lunaciones_eclipses`**, **`mundana_pronostico`** |
| **Pago** (key con plan) | `linea_biografica`, **`carta_natal`**, **`revolucion_solar`** |

El enforcement del tier lo hace el engine (la API key de KEYS-01) cuando el MCP
remoto se despliegue (p4). En el MCP local (stdio) no se enforça — corre con la
service key, acceso total.

## Reglas duras

- NO computar nada en el MCP. Wrapper fino → engine → normalizar shape.
- Agregar el método correspondiente en `abu_client.py` (un `_get` por endpoint) y
  la tool con `@mcp.tool()` en `server.py`, con docstring claro (los docstrings son
  lo que el LLM lee para decidir cuándo usar la tool — que sean precisos).
- **NO** agregar relocalización / ranking de ciudades — gateadas por h8 + el
  guardrail de habitabilidad (recomendar solo ciudades pobladas, nunca el argmax
  crudo de la grilla).
- Verificar el path/params exacto de cada endpoint contra `abu_engine/main.py`
  ANTES de escribir el wrapper (no asumir — `analyze` vs `/api/astro/analyze`, etc.).
- Reutilizar `_anotar_fase` / helpers existentes donde aplique (fase aplicativo/
  separativo de los aspectos).

## Verificación

| Check | Criterio |
|---|---|
| `carta_natal` trae secta | la salida incluye `secta` no-null (lo que chart-detailed NO tiene) |
| No duplica | `carta_natal` usa `/analyze`, no `chart-detailed`; aporta secta+lotes+señores |
| Lunar | `lunaciones_eclipses` devuelve próxima luna nueva/llena + eclipses con días |
| SR | `revolucion_solar` devuelve datetime del retorno distinto por año |
| Mundana history | `mundana_pronostico` expone `/history` (nuevo) además de forecast/sky |
| Graceful | si un endpoint protegido falla por auth, error claro; si mundana no está, None |
| Docstrings | cada tool tiene docstring que un LLM puede usar para decidir invocarla |
