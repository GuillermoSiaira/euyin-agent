# SPEC-HF-V7-01 — Harmony Field v7: completitud doctrinal + umbrales preregistrados

> **Estado**: PREREGISTRO (Fable+G, 2026-06-12) — congelar ANTES de calibrar.
> **Fase**: F1 · h2 (bloquea impl. h4-h6 y backtest h7 → compuerta h8)
> **Owner**: F+G (diseño doctrinal — NO delegable). Implementación: AG.
> **Fuente**: jerarquía de juicio de la skill `lilly-interpretacion` + propuesta
> NotebookLM (recepción/antiscios/tránsito, Lilly+Ptolomeo) + verificación contra
> `abu_engine/harmony/` (field_v3, angularity, resonance — 2026-06-12).
> **Depende de**: nada. **Bloquea**: `SPEC-HF-CORPUS-01`, `SPEC-HF-BACKTEST-01`.

---

## 0. Principio rector — completitud ≠ confianza

Dos condiciones, separadas, ambas necesarias antes de ofrecer el HF:

- **Completitud (doctrinal)**: el campo no deja afuera ningún factor que su propia
  jerarquía de juicio trate como determinante. Se cierra **por diseño** (este spec).
- **Confianza (empírica)**: el campo predice la realidad. Se cierra **por validación**
  contra un corpus con ubicación+fecha por evento (`SPEC-HF-CORPUS-01`).

No confundirlas: pulir el algoritmo cierra la primera, no la segunda. Este spec
cierra la completitud. La confianza la decide la compuerta h8 con datos.

**Regla de preregistro**: los 527 eventos ya calibraron v3/v6. Por eso los
parámetros de v7 **no se ajustan por grid search** — se fijan acá por doctrina y
se evalúan congelados. Todo número de este documento es inmutable una vez
commiteado; un cambio posterior es v7.1 con su fecha.

---

## 1. El diagnóstico — el campo viola su propia jerarquía

La skill define la jerarquía de juicio (orden en que la tradición pesa la
evidencia). Estado verificado del campo HF v6:

| Nivel | Factor | En el campo hoy |
|---|---|---|
| 1 | **Secta** | ❌ ausente — el campo es ciego a la secta |
| 2 | **Dignidad esencial** | ❌ ausente — `ASPECT_WEIGHTS`=1.0 y angularidad pesan todo igual |
| 3 | Angularidad | ✅ (4 ángulos) pero sin ponderar por 1-2; sin parans |
| 4 | Casas | ✅ |
| 5 | Activadores temporales | ⚠️ parcial (SR separado; tránsito→ángulo relocalizado falta) |

Los dos factores que la doctrina rankea **más alto** —los que "tiñen todo lo
demás"— están ausentes. v7 los incorpora **top-down**: primero secta y dignidad
(lo estructural), después los refinamientos de NotebookLM, después la precisión
espacial de relocalización.

---

## 2. Arquitectura de v7 — peso por planeta

El núcleo de v7 es un **peso compuesto por planeta** `W(p)` que modula su
participación en TODOS los términos del campo (aspectos y angularidad). Hoy todo
planeta participa con peso 1.0; v7 lo reemplaza por:

```
W(p) = σ_secta(p) × σ_dignidad(p)
```

- En un **aspecto** entre p y q: la contribución del aspecto se multiplica por
  `(W(p) + W(q)) / 2` (media — acotada, no sobre-amplifica).
- En la **angularidad** de p a un ángulo: la fuerza gaussiana se multiplica por `W(p)`.

`HF_aspects` y `HF_angles` se recalculan con estos pesos. `HF_houses` se mantiene.

### Nivel 1 — σ_secta(p) (preregistrado)

Secta del nativo desde el campo `sect` del engine (diurna = Sol sobre horizonte).
Multiplicador por rol de secta:

| Rol | Planeta (diurna / nocturna) | σ_secta |
|---|---|---|
| Luminaria de secta | Sol / Luna | 1.15 |
| Benéfico de secta | Júpiter / Venus | 1.15 |
| Benéfico contrario | Venus / Júpiter | 1.00 |
| Maléfico de secta (contenido) | Saturno / Marte | 0.85 |
| Maléfico contrario (disruptivo) | Marte / Saturno | 1.15 |
| Sin doctrina de secta | Mercurio, Urano, Neptuno, Plutón | 1.00 |
| Luminaria **fuera** de secta | Sol nocturno / Luna diurna | 1.00 |

> **Decisión 2026-06-13 (implementado h4):** la tabla no cubría la luminaria
> fuera de secta (Sol en carta nocturna, Luna en diurna). Se fija en **1.00
> (neutro)** — no se la penaliza ni premia. Default conservador; registrado para
> que el parámetro no quede sin documentar.

Doctrina: la secta determina qué planetas operan a plena fuerza. El maléfico
contrario a la secta es el más dañino → su participación se **amplifica** (y como
su contribución de tensión es negativa, amplificar = más impedancia, signo
correcto). Mercurio y los exteriores no tienen doctrina tradicional de secta →
neutros, marcado explícitamente (honestidad: no inventamos doctrina para Plutón).

### Nivel 2 — σ_dignidad(p) (preregistrado)

Dignidad esencial **tradicional** del engine (FIX-C03 — Saturno rige Acuario, etc.;
NO rulerships modernos). Multiplicador por estado dignitario:

| Estado | σ_dignidad |
|---|---|
| Domicilio | 1.30 |
| Exaltación | 1.20 |
| Triplicidad | 1.10 |
| Término | 1.05 |
| Faz | 1.00 |
| Peregrino | 0.90 |
| Detrimento | 0.75 |
| Caída | 0.70 |

Doctrina: un planeta en domicilio es "confiable y autodirigido"; uno peregrino
"actúa sin principio"; uno en caída expresa su significación degradada. La
dignidad escala cuánta autoridad lleva la geometría del planeta.

> **Elección de forma funcional (congelada, marcada para ablación):** σ_dignidad
> escala la magnitud total de participación, simétrico para contribuciones
> armónicas y tensas. La skill nota que un maléfico **debilitado y angular hace
> MÁS daño** — efecto que acá lo captura la secta (maléfico contrario ×1.15) y el
> signo negativo de la tensión, no la dignidad. La variante asimétrica (dignidad
> distinta para armónico vs tenso) queda como **v7.1**, a evaluar SOLO si la
> ablación muestra que el brazo nivel-2 no mejora. No sobre-ajustar la forma de
> entrada.

---

## 3. Refinamientos de aspecto (niveles 2-3) — operadores NotebookLM

### Nivel 3a — Recepción mutua (atenuador)

- **Condición**: `aspect_type ∈ {square, opposition}` Y recepción mutua por
  **domicilio o exaltación** (cada planeta en signo regido/exaltado por el otro).
  Triplicidad/término/faz excluidos en v7 (recepción débil — conservador).
- **Impacto**: el peso de tensión del aspecto se reduce **50%**.
- **Cómputo**: NO existe en el campo. Portar lógica de
  `abu_engine/core/solar_return_ranking.py`; tabla dignidades tradicional.
- Doctrina: Lilly — la recepción "mitiga la malevolencia de la infortuna".

### Nivel 3b — Antiscios

- **Antiscio**: espejo respecto al eje 0° Cáncer–0° Capricornio. **Contra-antiscio**:
  su opuesto.
- **Orbe**: ±2° estricto (no el ±6° operativo — operan "en la sombra").
- **Pesos**: Antiscio **+1.0** · Contra-antiscio **−0.8**.
- **Alcance v7**: **planeta↔planeta** (constante por carta, citable — Lilly tabula
  antiscios de planetas). La variante planeta↔ángulo (location-dependent) es
  extensión nuestra → brazo separado, solo si v7 base pasa.
- **Cómputo**: net-new — `abu_engine/harmony/antiscia.py`.

---

## 4. Precisión espacial de relocalización (niveles 3-5)

Estos SÍ mueven el mapa (varían con lat/lon) — el corazón de la killer feature.

### Nivel 3c — Parans (co-angularidad por latitud)

Dos planetas simultáneamente angulares a una latitud dada (técnica núcleo de
astrocartografía, Jim Lewis). Latitude-dependiente, no longitude.
- **Condición**: dos planetas natales ambos a ≤ orbe de un ángulo (no
  necesariamente el mismo) en la misma latitud.
- **Orbe**: ±1° de latitud (paran exacto) — angosto, son cruces precisos.
- **Peso**: realza el HF de esa banda de latitud. Peso base **+0.8** por par en
  paran, modulado por `W(p)·W(q)` de los planetas involucrados.
- **Cómputo**: net-new. Requiere barrer latitudes; integrar al grid existente.

### Nivel 3d — Aspectos a ángulos relocalizados

No solo planetas SOBRE el ángulo, sino planetas natales que aspectan el ASC/MC
**local** (trígono/sextil/cuadratura/oposición al ángulo relocalizado).
- **Orbe**: σ=3° gaussiano (consistente con el campo, sin corte duro).
- **Pesos (explícitos, NO `GROUP_WEIGHTS`)**: armónico (sextil/trígono) **+1.0**
  (suma), tenso (cuadratura/oposición) **−1.0** (resta), modulados por `W(p)`.
  *Decisión 2026-06-13 (h6a): NO se reusa `GROUP_WEIGHTS` (que tiene
  w_harmony=w_tension=−1.0, calibrado para el agregado global donde ambos restan).
  Acá la distinción armónico/tenso al ángulo ES el punto del operador; `W(p)`
  modula fuerza, no valencia del aspecto.*
- **Destino**: acumulador `hf_angles` (coef. β=0.6), no `hf_aspects`.
- **Cómputo**: extensión de `angularity.py` (hoy solo conjunción al ángulo).

### Nivel 5 — Tránsito → ángulo relocalizado (el mapa vivo)

La versión **espacial** del operador C (la global se descarta — no movía el mapa).
- `HF_dinámico(lat,lon,fecha) = HF_base(lat,lon) × M(lat,lon,fecha)`
- **M** según el tránsito lento (Jup/Sat/Ura/Nep/Plu) al ASC/MC **local**:
  - Armónico (conj. de benéfico, trígono, sextil) a ≤3°: **M = 1.5**
  - Duro (conj. de maléfico, cuadratura, oposición) a ≤3°: **M = 0.5**
  - Sin tránsito exacto al ángulo local: **M = 1.0**
- Como el ASC/MC local varía con lat/lon, **M varía con el lugar Y la fecha** →
  mapa vivo: "dónde el cielo ilumina tu carta este mes".
- Conflicto armónico+duro al mismo ángulo: prevalece el de menor orbe.
- **Cómputo**: tránsitos a la fecha (el engine ya los tiene) × ángulos del grid.

---

## 5. Ablación obligatoria

El runner h7 evalúa cada brazo por separado sobre el mismo split, para atribuir
mejora/daño a cada nivel (un nivel malo puede cancelar uno bueno):

```
v6_base
v6 + N1(secta)
v6 + N1 + N2(dignidad)
+ N3a(recepción)
+ N3b(antiscios)
+ N3c(parans)
+ N3d(aspectos-a-ángulos)
+ N5(tránsito→ángulo)  = v7 completo
```

Acumulativo top-down (cada brazo agrega un nivel). La compuerta h8 decide **por
nivel**: es válido adoptar solo los que mejoraron.

---

## 6. Criterio de compuerta (h8) — preregistrado

Un nivel **pasa** si, en su brazo:
- mejora la métrica del corpus respecto al brazo anterior en **≥ +0.05** (Pearson)
  **o** **≥ +0.10** (rank-biserial / hit-rate espacial), **y**
- no degrada ningún dominio con N≥30 en más de **−0.05**.

Si ningún nivel pasa: v7 = v6 y el HF sale "en validación". El Gantt lo contempla.

---

## 7. Dependencias de implementación (para AG, estimar h4-h6)

| Nivel | Cómputo | Reuso |
|---|---|---|
| 1 secta | multiplicador por rol; `sect` ya existe | tabla de roles (este spec) |
| 2 dignidad | multiplicador por estado; dignidad ya se computa | tabla tradicional FIX-C03 |
| 3a recepción | detección recepción mutua dom/exalt | `solar_return_ranking.py` |
| 3b antiscios | `antiscia.py` net-new | loop de pares de `field_v3` |
| 3c parans | barrido de latitud co-angular | grid existente |
| 3d aspectos-ángulo | aspectos a ASC/MC local | `angularity.py` |
| 5 tránsito→ángulo | tránsitos a fecha × ángulos del grid | engine ya computa tránsitos |

---

## 8. Preguntas para G

1. **Outers (Urano/Neptuno/Plutón)**: el campo los incluye pero no tienen doctrina
   tradicional de secta ni dignidad. v7 los deja en σ=1.0 (neutros). ¿OK, o se
   excluyen del campo para pureza tradicional? (Recomiendo neutros — sacarlos
   cambiaría la línea base v6 y rompería comparabilidad.)
2. **Parans planeta-planeta** vs solo planeta-ángulo: ¿ambos cruces o solo el
   clásico de Lewis? (Recomiendo el clásico primero.)
3. **Citas**: anclar recepción/antiscios/tránsitos a CA una vez indexado (OCR-01),
   o dejar como referencia NotebookLM sin página. No atribuir página falsa.
