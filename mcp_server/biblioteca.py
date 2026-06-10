"""
biblioteca.py — Consulta sobre la biblioteca de fuentes primarias clásicas.

Distinto de doctrine.py (doctrina INTERNA del proyecto: Axiomática, canon,
system prompt). Esto consulta los TEXTOS PRIMARIOS de la disciplina (Ptolomeo,
Lilly, Al-Biruni, Jyotish, Kayser) y devuelve fragmentos con cita verificable
por autor/libro/página.

El índice lo construye ai-oracle (`scripts/mundana/doctrinal_rag.py build`)
→ data/doctrinal_corpus/chunks.json. Acá solo se LEE el chunks.json y se arma
BM25 en memoria — deliberadamente no se carga el index.pkl (deserializar
pickles de otro entorno es frágil e inseguro).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import config

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # se reporta en consultar()
    BM25Okapi = None  # type: ignore[assignment]


def _chunks_path() -> Path:
    return config.ABU_DOCTRINE_ROOT / "data" / "doctrinal_corpus" / "chunks.json"


def _tokenize(text: str) -> list[str]:
    # Misma tokenización que el builder (doctrinal_rag.py) — auto-consistente.
    return re.findall(r"\b[a-záéíóúüñ]+\b", text.lower())


@lru_cache(maxsize=1)
def _load() -> tuple[object | None, list[dict]]:
    """Carga chunks.json y construye BM25 en memoria. Cacheado por proceso."""
    path = _chunks_path()
    if not path.exists():
        return None, []
    chunks = json.loads(path.read_text(encoding="utf-8"))
    if not chunks or BM25Okapi is None:
        return None, chunks
    index = BM25Okapi([_tokenize(c["text"]) for c in chunks])
    return index, chunks


def catalogo() -> list[dict]:
    """Libros disponibles en la biblioteca, con conteo de fragmentos."""
    _, chunks = _load()
    seen: dict[tuple, int] = {}
    for c in chunks:
        key = (c.get("author", "?"), c.get("book", "?"), c.get("tradition", ""))
        seen[key] = seen.get(key, 0) + 1
    return [
        {"autor": a, "libro": b, "tradicion": t, "fragmentos": n}
        for (a, b, t), n in sorted(seen.items())
    ]


def consultar(
    pregunta: str,
    tradicion: str | None = None,
    libro: str | None = None,
    k: int = 5,
) -> dict:
    """
    Recupera los k pasajes más relevantes de la biblioteca para la pregunta.

    tradicion: filtra por escuela (helenistica|occidental-lilly|persa|jyotish|
               armonica|pitagorica). libro: substring del título.
    Returns: {pregunta, resultados: [{autor, libro, tradicion, pagina,
              fragmento, score}], error?}
    """
    if BM25Okapi is None:
        return {"pregunta": pregunta, "resultados": [],
                "error": "rank_bm25 no instalado en el entorno del MCP"}

    index, chunks = _load()
    if index is None:
        return {
            "pregunta": pregunta, "resultados": [],
            "error": f"Índice no encontrado en {_chunks_path()} — "
                     "correr: python scripts/mundana/doctrinal_rag.py build (en ai-oracle)",
        }

    tokens = _tokenize(pregunta)
    if not tokens:
        return {"pregunta": pregunta, "resultados": []}

    scores = index.get_scores(tokens)

    def passes(c: dict) -> bool:
        if tradicion and c.get("tradition", "").lower() != tradicion.lower():
            return False
        if libro and libro.lower() not in c.get("book", "").lower():
            return False
        return True

    ranked = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)
    resultados = []
    for i in ranked:
        if scores[i] <= 0:
            break
        c = chunks[i]
        if not passes(c):
            continue
        resultados.append({
            "autor": c.get("author"),
            "libro": c.get("book"),
            "tradicion": c.get("tradition", ""),
            "pagina": c.get("page"),
            "fragmento": c.get("text"),
            "score": round(float(scores[i]), 2),
        })
        if len(resultados) >= max(1, k):
            break

    return {"pregunta": pregunta, "resultados": resultados}
