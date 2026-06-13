# Abu Oracle — MCP Server

An [MCP](https://modelcontextprotocol.io/) server that exposes a professional
astrological computation engine + classical doctrinal retrieval as tools for
any AI assistant. Built on the Abu Engine (deterministic astrological
calculations) and a curated corpus of primary sources.

**Not a horoscope generator.** This is the first MCP that brings rigorous
traditional astrology (Hellenistic-Persian-Lilly tradition) to AI agents:
planetary dignities, sect, profections, firdaria, and BM25 retrieval over
12 classical texts with verifiable page citations.

## Tools

| Tool | What it does | Auth |
|---|---|---|
| `calcular_transitos(fecha?, ventana_dias?)` | Collective sky: active planetary configurations, ordered by exactitude. Enriched with empirical p-values if the mundana module is deployed. | Public |
| `cielo_instante(fecha, lat?, lon?)` | Full chart for any moment and location: Placidus houses, ASC, MC, Part of Fortune, dignities. | Public |
| `traer_doctrina(tema, tags?, k?)` | Internal doctrine of Abu Oracle: Axiomatics of the Heavens, Lilly system prompt, Persian techniques, canon. Keyword retrieval. | Public |
| `consultar_biblioteca(pregunta, tradicion?, libro?, k?)` | Classical primary sources with verifiable citations: Ptolemy, Lilly 1852, Al-Biruni, Jyotish, Kayser. 12 books, ~17k passages, BM25 retrieval. | Public |
| `linea_biografica(fecha_nacimiento, lat, lon, meses_adelante?)` | Deterministic biographical timeline: annual profection, firdaria, and major transits (±18 months). | Service key |

## Quick Start

```bash
git clone https://github.com/<your-org>/euyin-agent.git
cd euyin-agent
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # Linux/Mac
cp .env.example .env   # edit ABU_ENGINE_URL and ABU_DOCTRINE_ROOT
```

All config is via **environment variables** (see `.env.example`). Zero
credentials in code. Local → cloud is just changing `ABU_ENGINE_URL`.

## Register in an MCP Client

### Claude Desktop / Cursor / any MCP client

```json
{
  "mcpServers": {
    "abu-oracle": {
      "command": "python",
      "args": ["path/to/euyin-agent/mcp_server/server.py"],
      "env": {
        "ABU_ENGINE_URL": "https://abu-engine-bbrsyawaca-uc.a.run.app",
        "ABU_DOCTRINE_ROOT": "path/to/ai-oracle"
      }
    }
  }
}
```

Default transport is **stdio**. For SSE (HTTP), set `MCP_TRANSPORT=sse` and
`FASTMCP_PORT=8001` before starting.

## Architecture

```
euyin-agent/
├── mcp_server/       ← MCP server: exposes engine + doctrine as tools
│   ├── server.py     ← Tool definitions (FastMCP)
│   ├── abu_client.py ← Thin HTTP client over Abu Engine
│   ├── doctrine.py   ← Doctrinal retrieval (keyword-based, ~20 sources)
│   ├── biblioteca.py ← Classical sources retrieval (BM25, ~17k passages)
│   └── config.py     ← Env var config, zero hardcoded credentials
├── skills/           ← Interpretive method (how Lilly reads a chart)
├── evals/            ← Interpretation quality measurement (WIP)
└── tests/            ← End-to-end tests against live engine
```

The MCP server **computes nothing** — it delegates all astrology to the Abu
Engine via HTTP and all retrieval to local indices. The interpretive layer
lives in the `lilly-interpretacion` skill, not in the server code.

## Tests

Requires the engine running (local Docker or cloud):

```bash
python tests/test_tools.py
# or: pytest tests/test_tools.py -v
```

## Requirements

- Python 3.11+
- Abu Engine running (local or cloud) — provides the astro computation
- `ai-oracle` repo cloned locally — provides the doctrinal corpus

## Notes

- **Mundana**: the local Docker image may lack `/api/mundana/*`. The Cloud Run
  production endpoint has it and is public.
- **Auth**: `ABU_SERVICE_KEY` unlocks protected endpoints (biography,
  relocation). Generate with `python -c "import secrets; print(secrets.token_hex(32))"`.
- **Doctrine**: reads from `ai-oracle` repo, not from `seventh-vault`.

## License

MIT — see [LICENSE](LICENSE).
