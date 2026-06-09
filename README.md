# EuYin Agent

La entidad agéntica de Abu Oracle: **Lilly**, intérprete astrológica.

Este repo es la *entidad*, no el cómputo. El cómputo determinista vive aparte,
en el Abu Engine (repo `ai-oracle`), y se consulta por HTTP. Acá viven los
órganos del agente:

```
euyin-agent/
├── mcp_server/   ← MANOS: server MCP que expone engine + doctrina como tools
├── skills/       ← MÉTODO: cómo interpreta Lilly (skill lilly-interpretacion)
├── evals/        ← cómo medimos la CALIDAD de la interpretación (a futuro)
└── tests/        ← verifican que las manos (tools) responden
```

> Carpeta `mcp_server/` (no `mcp/`) para no chocar con el paquete `mcp` (el SDK).

## Tools del MCP

| Tool | Qué hace | Endpoint / fuente |
|---|---|---|
| `calcular_transitos(fecha?, ventana_dias?)` | Cielo colectivo del día: configuraciones activas. Se enriquece con p-values empíricos si el engine tiene mundana. | `/api/astro/chart-detailed` (+ `/api/mundana/*`) |
| `cielo_instante(fecha, lat?, lon?)` | Carta del cielo para un instante y lugar arbitrarios (incluye pasado). | `/api/astro/chart-detailed` |
| `traer_doctrina(tema, tags?, k?)` | Recupera fragmentos doctrinales. | repo `ai-oracle` (retrieval léxico) |

Endpoints elegidos: públicos, sin auth.

## Setup

```bash
cd D:/projects/euyin-agent
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
cp .env.example .env        # ajustar si hace falta
```

Toda la config es por **variable de entorno** (ver `.env.example`). Cero
credenciales en el código. Local → nube es cambiar `ABU_ENGINE_URL`.

## Test local

Requiere el engine corriendo (Docker local en `localhost:8000`, o apuntá a la
nube vía `.env`).

```bash
.venv/Scripts/python tests/test_tools.py
```

## Registrar en un cliente MCP

```json
{
  "mcpServers": {
    "abu-oracle": {
      "command": "D:/projects/euyin-agent/.venv/Scripts/python.exe",
      "args": ["D:/projects/euyin-agent/mcp_server/server.py"],
      "env": {
        "ABU_ENGINE_URL": "http://localhost:8000",
        "ABU_DOCTRINE_ROOT": "D:/projects/ai-oracle"
      }
    }
  }
}
```

## Notas de estado

- **Mundana**: la imagen Docker local puede estar vieja (`/api/mundana/*` → 404).
  El Cloud Run de producción SÍ lo tiene y es público
  (`https://abu-engine-bbrsyawaca-uc.a.run.app`). `calcular_transitos` activa
  el enrichment automáticamente según a qué engine apuntes.
- **Auth**: `ABU_AUTH_TOKEN` (JWT Firebase) queda preparado para futuras tools
  contra endpoints protegidos. Las actuales no lo necesitan.
- **Doctrina**: se lee de `ai-oracle`, no de `seventh-vault` (vacío de contenido).
- **Runtime**: hoy el loop sos vos en un cliente MCP. El paso a agente autónomo
  (Agent SDK) agregará una carpeta `runtime/` — la estructura ya lo contempla.
