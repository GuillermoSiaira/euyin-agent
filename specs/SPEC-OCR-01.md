# SPEC-OCR-01 — OCR Biblioteca: PDFs sin texto

> **Estado**: ✅ APROBADO CON 3 CORRECCIONES (auditoría Fable 2026-06-12)  

## ⚖️ AUDITORÍA FABLE

El mejor spec del lote — la decisión anti-Tesseract está bien fundada (BM25 es
léxico: un error de OCR en la palabra clave hace el pasaje irrecuperable).
Tres correcciones y la pregunta resuelta:

1. **Ruta incorrecta**: los PDFs están en `ai-oracle/astro-texts/` — NO existe
   `ai-oracle/data/books/`. El archivo exacto:
   `astro-texts/Lilly_William-Christian_astrology.pdf` (444 págs, 51 MB).
2. **Página PDF ≠ página impresa.** El OCR numera páginas del PDF; la skill cita
   páginas del libro. Para no fabricar citas falsas: `page` = página del PDF, y el
   `book` label lo declara: `"Christian Astrology (1647) — pág. de PDF"`. Detectar
   el folio impreso en el header escaneado es frágil — rechazado para v1. (La
   edición Zadkiel 1852 ya indexada sí tiene paginación impresa real — conviven.)
3. **Integración**: no inventar parser nuevo — `doctrinal_rag.py` ya tiene patrón
   de tipos de fuente (`type: "html_pre"` con su iterador). Agregar
   `type: "ocr_txt"` + `_iter_ocr_pages()` que lee los marcadores `--- PAGE N ---`,
   y la entrada en `CORPUS_SOURCES` con `tradition: "occidental-lilly"`,
   `short: "CA"`. El chunking existente se reutiliza tal cual.

**Pregunta abierta — RESUELTA: Google Document AI.** Razones: ya está en el stack
GCP (billing y auth existentes), 444 págs ≈ centavos (free tier 1.000 págs/mes lo
cubre o casi), y su OCR maneja tipografía histórica razonablemente. Claude Vision
queda como fallback selectivo: si el muestreo de calidad falla en >2 de 10 páginas
(criterio de la tabla), re-procesar SOLO las páginas malas con Claude. No usar
Vision para los 444 — costo sin necesidad demostrada.

**Nota de verificación extra**: incluir en el muestreo la palabra "Saturn" y
"opposition" — términos que la skill consulta de verdad; si la 's' larga los rompe
("Faturn"), el OCR falló funcionalmente aunque se vea bien.

---
> **Estado original**: BORRADOR v2 (Antigravity + feedback NotebookLM)  
> **Fase**: F0 · Cierres  
> **Owner ejecución**: A (agente delegado)  
> **Roadmap ref**: f05 (2026-06-15, 4 días)

## Objetivo

Extraer texto de **Christian Astrology** (William Lilly, 1647/1852) — escaneo
PDF sin texto seleccionable — e integrarlo al índice BM25 que alimenta
`consultar_biblioteca()` del MCP.

Prioridad exclusiva en CA para F0. Los demás PDFs sin texto son un spec
futuro.

## Contexto

El MCP ya tiene `consultar_biblioteca()` que busca sobre `chunks.json` (12
libros, ~17k pasajes). Los libros con texto digital ya están indexados. Los
PDFs sin texto (escaneos) no participan del índice — su contenido es
invisible al retrieval.

Ruta del corpus: `ai-oracle/data/doctrinal_corpus/`  
Builder del índice: `ai-oracle/scripts/mundana/doctrinal_rag.py`

### Por qué CA es la prioridad absoluta

1. **Voz**: la personalidad completa de Lilly (el agente) está modelada sobre
   William Lilly. Sin CA indexado, la skill `lilly-interpretacion` no puede
   citar la fuente primaria de su propia voz.
2. **Cálculo**: el puntaje D4 de Dignidad Esencial del Harmony Field se basa
   en las tablas de Lilly. Las citas deben ser verificables.
3. **Pipeline**: el publicador multiplataforma (SPEC-PIPE-01) necesita citas
   precisas de CA para posts mundanos (ej. tránsitos Marte-Saturno).

## Alcance

### 1. Whitelist curada (NO detección automática)

**Guillermo define la lista exacta** de archivos a procesar en
`ai-oracle/data/books/`. No se hace detección automática con `pdftotext` —
el corpus primario es estricto y la inclusión descuidada de PDFs esotéricos
genéricos o escaneos corruptos contaminaría el BM25, violando la regla
principal de la skill: citar fuentes primarias con autoridad.

Para F0: solo **Christian Astrology**.

### 2. OCR con servicio de alta calidad (NO Tesseract)

**Descartar Tesseract.** CA es un texto del siglo XVII con:
- Tipografía de la época (la 's' larga confundida con 'f')
- Caracteres desgastados por la tinta
- Posible tipografía gótica en encabezados

Dado que `consultar_biblioteca` usa BM25 (retrieval léxico), **un error de
OCR en una palabra clave hace que el pasaje sea invisible al MCP**. La
calidad del OCR no es cosmética — es funcional.

Opciones recomendadas (en orden de preferencia):
1. **Google Document AI** — mejor manejo de tipografía histórica, integrado
   con GCP (ya es parte del stack)
2. **Claude Vision API** — calidad excelente en texto antiguo, pero más caro
   por página
3. **Tesseract** — solo como último recurso, con post-procesamiento manual

> **DECISIÓN GUILLERMO**: ¿Document AI o Claude Vision? Si el costo es
> concern, Document AI tiene free tier (1,000 páginas/mes).

### 3. Preservar marcadores de página

La extracción DEBE mantener la paginación intacta. Output: un `.txt` con
marcadores `--- PAGE N ---` entre cada página.

Esto es crítico: la skill `lilly-interpretacion` tiene la instrucción
explícita de citar con número de página:
> *"Lilly (Christian Astrology, p. 361) llama a la oposición..."*

Si el OCR pierde la paginación, el agente genera citas sin página →
rompe la credibilidad del sistema.

### 4. Integrar al builder de chunks

El `.txt` resultante se integra a `doctrinal_rag.py`, respetando el schema:
`{author, book, tradition, page, text}`.

- `author`: "William Lilly"
- `book`: "Christian Astrology"
- `tradition`: "occidental-lilly"
- `page`: extraído del marcador `--- PAGE N ---`

### 5. Re-indexar y verificar

```bash
cd ai-oracle
python scripts/mundana/doctrinal_rag.py build
```

## NO alcance

- NO procesar otros PDFs más allá de CA (los demás son spec futuro).
- NO cambiar el schema de chunks ni la tokenización BM25.
- NO requiere cambios en el MCP server (`biblioteca.py` lee `chunks.json` tal
  cual).
- NO migrar de BM25 a embeddings/vectorial (postergado explícitamente en el
  roadmap; se activa cuando el retrieval léxico se quede corto en uso pago).

## Verificación

| Check | Criterio |
|---|---|
| Calidad OCR | Muestrear 10 páginas aleatorias de CA: >200 chars/pág, 's' larga correctamente interpretada, palabras clave legibles |
| Paginación | Cada pasaje en `chunks.json` tiene `page` no-null y corresponde a la página real del PDF |
| Índice | `chunks.json` crece; `catalogo()` muestra "Christian Astrology" con >500 fragmentos |
| Retrieval | `consultar_biblioteca("dignities of planets", libro="Christian Astrology")` devuelve ≥3 resultados con `pagina` no-null |
| Retrieval semántico-léxico | `consultar_biblioteca("reception of planets")` devuelve pasajes de CA sobre recepción mutua |
| No regresión | Tests existentes (`test_consultar_biblioteca`) siguen pasando |

## Limitación conocida (para el futuro)

BM25 no entiende semántica. Si el usuario pregunta por "limitaciones laborales"
y Lilly habla de "obstructions in preferment", BM25 no los conecta. Para la
v1 con volúmenes bajos esto es aceptable. Cuando se escale a usuarios
paid/B2B, migrar a embeddings vectoriales (roadmap: "Embeddings biblioteca →
cuando la recuperación BM25 quede corta en uso pago").

## Preguntas resueltas (por NotebookLM)

| Pregunta original | Resolución |
|---|---|
| ¿Qué PDFs? | Whitelist curada por Guillermo. F0 = solo CA. |
| ¿Tesseract o cloud? | **No Tesseract.** Document AI o Claude Vision. |
| ¿Solo CA o todos? | Solo CA para F0. Demás PDFs = spec futuro. |

## Pregunta abierta restante

1. **¿Google Document AI o Claude Vision API?** Document AI tiene free tier
   (1,000 pág/mes) y está en el stack GCP. Claude Vision es más caro pero
   potencialmente mejor en tipografía arcaica. ¿Guillermo tiene preferencia?
