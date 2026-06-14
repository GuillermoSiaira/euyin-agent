"""
abu_client.py — Cliente HTTP fino sobre el Abu Engine.

NO reimplementa cómputo astrológico. Solo llama a los endpoints HTTP que ya
existen y normaliza la respuesta. Toda la lógica determinista vive en el engine.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

import config


class AbuEngineError(RuntimeError):
    """Fallo al hablar con el Abu Engine."""


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=config.ABU_ENGINE_URL,
        timeout=config.ABU_HTTP_TIMEOUT,
        headers=config.auth_headers(),
    )


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    try:
        with _client() as c:
            resp = c.get(path, params=params)
    except httpx.HTTPError as exc:
        raise AbuEngineError(f"No se pudo contactar el engine en {config.ABU_ENGINE_URL}{path}: {exc}") from exc
    if resp.status_code == 404:
        raise AbuEngineError(f"404 Not Found: {path}")
    if resp.status_code >= 400:
        raise AbuEngineError(f"{resp.status_code} en {path}: {resp.text[:200]}")
    return resp.json()


def health() -> bool:
    """True si el engine responde en la raíz."""
    try:
        _get("/")
        return True
    except AbuEngineError:
        return False


def chart_detailed(date_iso: str, lat: float, lon: float) -> dict:
    """
    GET /api/astro/chart-detailed — carta de un instante (público, sin auth).

    Devuelve posiciones planetarias, aspectos, dignidades, nodos, Parte de
    Fortuna y casas Placidus para la fecha/ubicación dadas.
    """
    return _get(
        "/api/astro/chart-detailed",
        {"date": date_iso, "lat": lat, "lon": lon},
    )


def chart_extended(date_iso: str, lat: float, lon: float) -> dict:
    """
    GET /api/astro/chart/extended — carta natal doctrinal completa (protegido).
    """
    return _get("/api/astro/chart/extended", {"date": date_iso, "lat": lat, "lon": lon})


def biography(birth_date_iso: str, birth_lat: float, birth_lon: float) -> dict:
    """
    GET /api/astro/biography — línea temporal biográfica completa:
    profecciones (90 años), firdaria (75 años) y tránsitos ±18 meses.
    Requiere ABU_SERVICE_KEY (o JWT) — endpoint protegido.
    """
    return _get(
        "/api/astro/biography",
        {"birthDate": birth_date_iso, "birthLat": birth_lat, "birthLon": birth_lon},
    )


def solar_return(
    birth_date_iso: str, lat: float, lon: float, year: int | None = None
) -> dict:
    """
    GET /api/astro/solar-return — carta de la revolución solar (protegido).
    """
    params: dict[str, Any] = {"birthDate": birth_date_iso, "lat": lat, "lon": lon}
    if year:
        params["year"] = year
    return _get("/api/astro/solar-return", params)


def lunar(
    birth_date_iso: str, lat: float, lon: float, query_dt: str | None = None
) -> dict | None:
    """
    GET /api/astro/lunar — lunaciones y eclipses próximos relativos a una carta natal.
    None si el endpoint no existe.
    """
    try:
        params: dict[str, Any] = {"birthDate": birth_date_iso, "lat": lat, "lon": lon}
        if query_dt:
            params["dt"] = query_dt
        return _get("/api/astro/lunar", params)
    except AbuEngineError:
        return None


def mundana_sky() -> dict | None:
    """
    GET /api/mundana/sky — cielo colectivo + configuraciones mundanas con
    p-values empíricos. Devuelve None si la ruta no existe en la imagen viva
    (engine sin rebuild del router mundana).
    """
    try:
        return _get("/api/mundana/sky")
    except AbuEngineError:
        return None


def mundana_forecast(days: int = 14) -> dict | None:
    """GET /api/mundana/forecast — configuraciones próximas. None si no existe."""
    try:
        return _get("/api/mundana/forecast", {"days": max(1, min(days, 365))})
    except AbuEngineError:
        return None


def mundana_history(config_type: str | None = None) -> dict | None:
    """GET /api/mundana/history — contexto histórico de configuraciones. None si no existe."""
    try:
        params = {}
        if config_type:
            params["config_type"] = config_type
        return _get("/api/mundana/history", params)
    except AbuEngineError:
        return None


def now_iso() -> str:
    """Fecha/hora actual en ISO UTC, formato que el engine acepta."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_date(fecha: str | None) -> str:
    """
    Normaliza una fecha de entrada a ISO UTC. Acepta 'YYYY-MM-DD',
    'YYYY-MM-DDTHH:MM:SSZ', o vacío (→ ahora). Si viene solo la fecha,
    se asume mediodía UTC (instante neutro para el cielo del día).
    """
    if not fecha or not fecha.strip():
        return now_iso()
    s = fecha.strip()
    if len(s) == 10:  # YYYY-MM-DD
        return f"{s}T12:00:00Z"
    if s.endswith("Z") or "+" in s[10:]:
        return s
    return s + "Z"
