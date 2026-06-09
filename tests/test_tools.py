"""
test_tools.py — Test local de las tools del MCP contra el Abu Engine vivo.

Requiere el engine corriendo en ABU_ENGINE_URL (default http://localhost:8000),
o apuntá a la nube (ver .env.example).

Uso:
    python tests/test_tools.py          # runner con salida legible
    pytest tests/test_tools.py -v       # vía pytest
"""
from __future__ import annotations

import sys
from pathlib import Path

# Permitir importar los módulos del server (viven en ../mcp_server).
_MCP_DIR = Path(__file__).resolve().parent.parent / "mcp_server"
sys.path.insert(0, str(_MCP_DIR))

import abu_client  # noqa: E402
import config  # noqa: E402
import server  # noqa: E402


def test_engine_alcanzable() -> None:
    assert abu_client.health(), f"Engine no responde en {config.ABU_ENGINE_URL}"


def test_calcular_transitos() -> None:
    out = server.calcular_transitos()
    assert out["fecha"], "falta fecha"
    assert out["posiciones"], "sin posiciones planetarias"
    assert isinstance(out["configuraciones_activas"], list), "configuraciones no es lista"
    assert "mundana_enrichment" in out, "falta flag mundana_enrichment"
    nombres = {p["planeta"] for p in out["posiciones"]}
    assert "Sun" in nombres, f"Sol ausente: {nombres}"


def test_cielo_instante() -> None:
    out = server.cielo_instante("2020-03-20", lat=-34.6, lon=-58.4)
    assert out["ascendente"], "sin ascendente (casas no calculadas)"
    assert out["posiciones"], "sin posiciones"
    assert out["ubicacion"]["lat"] == -34.6, "ubicación no propagada"


def test_traer_doctrina() -> None:
    out = server.traer_doctrina("dignidad esencial y secta del planeta", tags=["dignity"])
    encontradas = [f for f in out["fuentes_indexadas"] if f["encontrada"]]
    assert encontradas, "no se encontró ninguna fuente doctrinal en ABU_DOCTRINE_ROOT"
    assert out["resultados"], "retrieval vacío para una consulta doctrinal básica"
    assert out["resultados"][0]["fragmento"], "fragmento vacío"


_TESTS = [
    ("engine alcanzable", test_engine_alcanzable),
    ("calcular_transitos", test_calcular_transitos),
    ("cielo_instante", test_cielo_instante),
    ("traer_doctrina", test_traer_doctrina),
]


def _run() -> int:
    print(f"Engine: {config.ABU_ENGINE_URL}")
    print(f"Doctrina: {config.ABU_DOCTRINE_ROOT}")
    print("-" * 60)
    fallos = 0
    for nombre, fn in _TESTS:
        try:
            fn()
            print(f"  PASS  {nombre}")
        except AssertionError as exc:
            fallos += 1
            print(f"  FAIL  {nombre}: {exc}")
        except Exception as exc:  # noqa: BLE001
            fallos += 1
            print(f"  ERROR {nombre}: {type(exc).__name__}: {exc}")
    print("-" * 60)
    print("TODO OK" if fallos == 0 else f"{fallos} fallo(s)")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(_run())
