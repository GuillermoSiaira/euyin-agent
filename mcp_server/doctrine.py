"""
doctrine.py — Recuperación doctrinal sobre el corpus del repo ai-oracle.

Indexa un conjunto curado de fuentes (el system prompt de Lilly, la Axiomática,
técnicas persas, el Grimoire, el registro de voz) y devuelve los fragmentos más
relevantes para un tema/tags por solapamiento de palabras clave.

Retrieval léxico, sin embeddings — cero dependencias, determinista y testeable
offline. La mejora a recuperación semántica (embeddings) es un upgrade futuro;
ver scripts/mundana/doctrinal_rag.py en ai-oracle para esa línea.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import config

# Fuentes doctrinales, relativas a ABU_DOCTRINE_ROOT (repo ai-oracle).
# Decisión registrada en Fase 1: la doctrina real vive en ai-oracle, no en
# seventh-vault (que está vacío de contenido).
_SOURCES: list[str] = [
    "next_app/lib/lilly-prompt.ts",
    "AXIOMATICS_OF_HEAVENS_v0.4.md",
    "LILLY_QUOTES.md",
    "obsidian_vault/02_doctrina/AXIOMATICS_v0_4.md",
    "obsidian_vault/persian_techniques.md",
    "docs/concepts/Grimoire_Master.md",
]

_STOPWORDS = {
    "the", "and", "for", "que", "con", "los", "las", "del", "una", "uno",
    "por", "como", "más", "este", "esta", "que", "the", "a", "de", "en", "el",
    "la", "un", "is", "of", "to", "in", "su", "se", "al", "lo",
}


@dataclass
class Fragment:
    fuente: str
    titulo: str
    texto: str


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-záéíóúñü]+", text.lower())
    return [w for w in words if len(w) > 2 and w not in _STOPWORDS]


def _split_ts_prompt(content: str) -> list[tuple[str, str]]:
    """Extrae el string LILLY_SYSTEM_PROMPT del .ts y lo parte por secciones."""
    m = re.search(r"LILLY_SYSTEM_PROMPT\s*=\s*`(.*?)`", content, re.DOTALL)
    body = m.group(1) if m else content
    return _split_blocks(body)


def _split_blocks(content: str) -> list[tuple[str, str]]:
    """
    Parte texto en (titulo, bloque). Usa headings markdown (#...) y separadores
    '---' / líneas en MAYÚSCULAS como límites de sección.
    """
    lines = content.splitlines()
    blocks: list[tuple[str, str]] = []
    title = "(intro)"
    buf: list[str] = []

    def flush() -> None:
        text = "\n".join(buf).strip()
        if text:
            blocks.append((title, text))

    for line in lines:
        stripped = line.strip()
        is_md_heading = stripped.startswith("#")
        # Heading "tradicional" tipo "1. SECT" o "DOCTRINAL FRAMEWORK"
        is_caps_heading = bool(
            stripped
            and len(stripped) < 60
            and re.match(r"^[0-9]*\.?\s*[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ /—-]+$", stripped)
        )
        if is_md_heading or is_caps_heading:
            flush()
            title = stripped.lstrip("#").strip() or title
            buf = []
        else:
            buf.append(line)
    flush()
    return blocks


@lru_cache(maxsize=1)
def _index() -> list[Fragment]:
    fragments: list[Fragment] = []
    root: Path = config.ABU_DOCTRINE_ROOT
    for rel in _SOURCES:
        path = root / rel
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        blocks = _split_ts_prompt(content) if path.suffix == ".ts" else _split_blocks(content)
        for title, text in blocks:
            # Trocear bloques largos para que el fragmento devuelto sea citable.
            for chunk in _chunk(text, max_chars=1200):
                fragments.append(Fragment(fuente=rel, titulo=title, texto=chunk))
    return fragments


def _chunk(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    parts, cur = [], ""
    for para in text.split("\n\n"):
        if len(cur) + len(para) + 2 > max_chars and cur:
            parts.append(cur.strip())
            cur = para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur.strip():
        parts.append(cur.strip())
    return parts


def retrieve(tema: str, tags: list[str] | None = None, k: int = 3) -> list[dict]:
    """
    Recupera los k fragmentos doctrinales más relevantes para tema + tags.

    Returns: [{fuente, titulo, fragmento, score}] ordenado por score desc.
    """
    query_terms = _tokenize(tema) + [t.lower() for t in (tags or [])]
    if not query_terms:
        return []
    query_set = set(query_terms)

    scored: list[tuple[float, Fragment]] = []
    for frag in _index():
        hay = (frag.titulo + " " + frag.texto).lower()
        hay_tokens = set(_tokenize(hay))
        overlap = query_set & hay_tokens
        if not overlap:
            continue
        # Score: solapamiento + bonus por término en el título.
        score = float(len(overlap))
        title_tokens = set(_tokenize(frag.titulo))
        score += 0.5 * len(query_set & title_tokens)
        scored.append((score, frag))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {
            "fuente": frag.fuente,
            "titulo": frag.titulo,
            "fragmento": frag.texto,
            "score": round(score, 2),
        }
        for score, frag in scored[: max(1, k)]
    ]


def source_status() -> list[dict]:
    """Diagnóstico: qué fuentes doctrinales se encontraron en disco."""
    root = config.ABU_DOCTRINE_ROOT
    return [
        {"fuente": rel, "encontrada": (root / rel).exists()}
        for rel in _SOURCES
    ]
