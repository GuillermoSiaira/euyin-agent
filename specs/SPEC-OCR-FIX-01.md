# SPEC-OCR-FIX-01 — Corrección de la 's larga' en el OCR de Christian Astrology

> **Estado**: APROBADO con receta exacta (Fable 2026-06-13) — AG/Aider solo ejecuta.
> **Fase**: F0 · cierre de f05 (bloquea: índice BM25 usable).
> **Owner**: A (delegado). Revisión del diff: F.
> **Depende de**: el OCR ya corrido (`data/doctrinal_corpus/christian_astrology_ocr.txt`,
> 444 págs). **Bloquea**: que `consultar_biblioteca` encuentre CA por término.

## Problema (verificado 2026-06-13)

Cloud Vision a 300 DPI leyó la **s larga medial (ſ) como 'f'** de forma sistemática.
Mayúsculas OK (Saturn ✓), minúsculas internas rotas:

| Término | bien | corrupto | % roto |
|---|---|---|---|
| ascendant | 25 | afcendant 1287 | 98% |
| disposition | 3 | difpofition 41 | 93% |
| opposition | 3 | oppofition 21 | 87% |
| house | 1145 | houfe 833 | 42% |
| significator | 568 | fignificator 93 | 14% |

BM25 es léxico → los términos clave son invisibles. **El índice ya se reconstruyó
con el texto malo (3.123 chunks CA contaminados) — hay que corregir y re-indexar.**

## Estrategia (NO re-OCR)

Corrección post-proceso guiada por diccionario. Regla robusta:
> Si una palabra contiene 'f', NO es una palabra inglesa válida, y reemplazar
> una o más 'f'→'s' la convierte en una palabra válida → corregir. Si la forma
> con 'f' YA es válida (of, for, fortune, fixed, affliction…), dejarla intacta.

Esto arregla afcendant→ascendant, houfe→house, poffeffion→possession, y protege
las f legítimas. El vocabulario es acotado; recupera casi todo el recall.

## Receta — crear `scripts/doctrinal_corpus/fix_long_s.py`

```python
"""
Corrige la 's larga' (ſ) leída como 'f' en el OCR de Christian Astrology.
Regla: si word-con-f no es palabra válida pero word-con-s sí, reemplazar.
Las f legítimas (of, for, fortune, fixed...) se preservan.
"""
import re
import sys
from pathlib import Path
from itertools import combinations

try:
    from spellchecker import SpellChecker
except ImportError:
    print("pip install pyspellchecker"); sys.exit(1)

REPO = Path(__file__).resolve().parents[2]
TXT = REPO / "data" / "doctrinal_corpus" / "christian_astrology_ocr.txt"

spell = SpellChecker()  # diccionario inglés con frecuencias, sin descarga
# Vocabulario astrológico que el dict general puede no tener:
DOMAIN = {
    "ascendant", "significator", "significators", "disposition", "dispositor",
    "retrograde", "combust", "cazimi", "almuten", "antiscion", "antiscions",
    "profection", "firdaria", "decumbiture", "sextile", "trine", "quartile",
    "horary", "querent", "quesited", "hyleg", "alcocoden", "exaltation",
}
KNOWN = set(spell.word_frequency.dictionary.keys()) | DOMAIN

def is_word(w: str) -> bool:
    return w.lower() in KNOWN

def fix_token(word: str) -> str:
    if "f" not in word.lower():
        return word
    if is_word(word):              # f legítima → no tocar
        return word
    idxs = [i for i, c in enumerate(word) if c.lower() == "f"]
    # probar de más reemplazos a menos (ſſ dobles primero)
    for r in range(len(idxs), 0, -1):
        for combo in combinations(idxs, r):
            chars = list(word)
            for i in combo:
                chars[i] = "S" if word[i].isupper() else "s"
            cand = "".join(chars)
            if is_word(cand):
                return cand
    return word

TOKEN = re.compile(r"[A-Za-z]+")

def fix_line(line: str) -> str:
    if line.startswith("--- PAGE "):      # no tocar marcadores
        return line
    return TOKEN.sub(lambda m: fix_token(m.group(0)), line)

def main():
    raw = TXT.read_text(encoding="utf-8")
    fixed = "\n".join(fix_line(ln) for ln in raw.split("\n"))
    TXT.write_text(fixed, encoding="utf-8")
    print(f"[FIX] corregido in-place: {TXT}")

if __name__ == "__main__":
    main()
```

## Ejecución

```bash
.\.venv311\Scripts\pip install pyspellchecker
.\.venv311\Scripts\python scripts\doctrinal_corpus\fix_long_s.py
.\.venv311\Scripts\python scripts\mundana\doctrinal_rag.py build
```

## Verificación (OBLIGATORIA — reportar)

Re-correr el test de términos sobre el `.txt` ya corregido:

| Check | Criterio |
|---|---|
| ascendant | "ascendant" sube a ~1300; "afcendant" cae a ~0 |
| opposition | "oppofition" → ~0 |
| house / significator | "houfe"/"fignificator" → ~0 |
| f legítimas intactas | "fortune", "fixed", "affliction", "of", "for" siguen presentes con su conteo original (no convertidos a sortune/sixed/etc.) |
| Índice | re-`build`; `consultar_biblioteca("ascendant", libro="Christian Astrology")` ≥3 resultados |
| Volumen | chunks CA siguen ~3.123 (la corrección no cambia el conteo, solo el texto) |

Regla dura: si alguna f legítima se rompió (ej. "fortune"→"sortune" aparece), el
diccionario falló — reportar antes de re-indexar. **No push hasta verificación OK.**
