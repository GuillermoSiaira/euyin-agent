# evals/

Cómo medimos si EuYin **interpreta bien** — no solo si las herramientas responden.

Los `tests/` verifican las *manos* (que el MCP devuelve datos válidos del engine).
Los `evals/` verificarán el *método*: dado un cielo + doctrina, ¿la lectura es
rigurosa, fiel a la voz de Lilly, y específica a la carta (no genérica)?

Vacío por ahora — placeholder deliberado. Se llena cuando la skill
`lilly-interpretacion` esté en uso y queramos calibrar su calidad.
Posible base: el protocolo de validación ciega de ai-oracle
(`BLIND_VALIDATION_PROTOCOL.md`) y `skill-creator` (tiene runner de evals).
