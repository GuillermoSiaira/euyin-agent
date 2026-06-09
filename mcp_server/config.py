"""
config.py — Configuración del MCP server, leída SIEMPRE desde variables de
entorno. Cero credenciales hardcodeadas.

Cargá un archivo .env manualmente (ver .env.example) o exportá las variables
en tu shell antes de arrancar el server. Se busca .env en la raíz del repo
y en este directorio.
"""
from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Carga .env si existe (raíz del repo o este dir), sin dependencia externa."""
    here = Path(__file__).resolve().parent
    candidates = [here.parent / ".env", here / ".env"]
    for env_path in candidates:
        if not env_path.exists():
            continue
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            # No pisar lo que ya esté exportado en el entorno real.
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()

# URL base del Abu Engine. Default local — la promoción a la nube es cambiar
# esta sola variable.
ABU_ENGINE_URL: str = os.environ.get("ABU_ENGINE_URL", "http://localhost:8000").rstrip("/")

# Token Bearer opcional para endpoints protegidos. Vacío = no se envía header.
ABU_AUTH_TOKEN: str = os.environ.get("ABU_AUTH_TOKEN", "").strip()

# Raíz del repo ai-oracle (fuente de doctrina).
ABU_DOCTRINE_ROOT: Path = Path(
    os.environ.get("ABU_DOCTRINE_ROOT", "D:/projects/ai-oracle")
).expanduser()

# Timeout HTTP en segundos.
ABU_HTTP_TIMEOUT: float = float(os.environ.get("ABU_HTTP_TIMEOUT", "45"))


def auth_headers() -> dict[str, str]:
    """Header Authorization solo si hay token configurado."""
    if ABU_AUTH_TOKEN:
        return {"Authorization": f"Bearer {ABU_AUTH_TOKEN}"}
    return {}
