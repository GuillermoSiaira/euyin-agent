"""
server.py — MCP server que expone el Abu Engine + la doctrina de Lilly.

Tools:
  calcular_transitos(fecha?, ventana_dias?) — cielo colectivo del día/ventana
  cielo_instante(fecha, lat?, lon?)         — carta de un instante puntual
  traer_doctrina(tema, tags?, k?)           — recuperación doctrinal (ai-oracle)

El server NO calcula nada: delega todo cómputo al engine vía HTTP (abu_client)
y la doctrina a la recuperación léxica (doctrine). Respeta la separación
determinista (engine) / interpretación (capa LLM).

Arranque:  python server.py     (stdio MCP)
Config:    todo por env var — ver .env.example
"""
from __future__ import annotations

from typing import Any

import os

from mcp.server.fastmcp import FastMCP

import abu_client
import biblioteca
import config
import doctrine

# Puerto leído aquí (nivel de módulo) para que el argumento explícito
# al constructor tome el valor de FASTMCP_PORT antes de que lo fije en 8000.
_port = int(os.environ.get("PORT") or os.environ.get("FASTMCP_PORT", "8001"))
_transport = os.environ.get("MCP_TRANSPORT", "stdio")
mcp = FastMCP(
    "abu-oracle",
    host=("0.0.0.0" if _transport != "stdio" else "127.0.0.1"),
    port=_port,
    stateless_http=(_transport != "stdio")
)


def _configuraciones_desde_aspectos(aspectos: list[dict]) -> list[dict]:
    """
    Traduce los aspectos crudos de chart-detailed a 'configuraciones activas'
    del cielo, ordenadas por exactitud (orbe ascendente).
    """
    configs = [
        {
            "planeta_a": a.get("a"),
            "planeta_b": a.get("b"),
            "aspecto": a.get("type"),
            "orbe": a.get("orb"),
            "angulo": a.get("angle"),
        }
        for a in aspectos
    ]
    configs.sort(key=lambda c: (c["orbe"] is None, c["orbe"]))
    return configs


def _anotar_fase(configs: list[dict], fecha_iso: str, lat: float, lon: float) -> None:
    """
    Clasifica cada configuración como aplicativa (el orbe se cierra hacia el
    exacto) o separativa (ya perfeccionó y se abre), comparando contra el
    mismo cielo 12 horas después. Sin este dato el intérprete no puede saber
    la dirección del aspecto — y no debe suponerla.
    Non-fatal: si la segunda lectura falla, fase = "indeterminada".
    """
    try:
        from datetime import datetime, timedelta
        dt = datetime.fromisoformat(fecha_iso.replace("Z", "+00:00")) + timedelta(hours=12)
        futuro = abu_client.chart_detailed(dt.strftime("%Y-%m-%dT%H:%M:%SZ"), lat, lon)
        orbes_futuros: dict = {}
        for a in futuro.get("aspects", []):
            key = (frozenset((a.get("a"), a.get("b"))), a.get("type"))
            orbes_futuros[key] = a.get("orb")
        for c in configs:
            key = (frozenset((c["planeta_a"], c["planeta_b"])), c["aspecto"])
            orb_f = orbes_futuros.get(key)
            if orb_f is None or c["orbe"] is None:
                c["fase"] = "indeterminada"
            elif orb_f < c["orbe"]:
                c["fase"] = "aplicativo"
            elif orb_f > c["orbe"]:
                c["fase"] = "separativo"
            else:
                c["fase"] = "estacionario"
    except Exception:
        for c in configs:
            c.setdefault("fase", "indeterminada")


@mcp.tool()
def calcular_transitos(fecha: str = "", ventana_dias: int = 14) -> dict[str, Any]:
    """
    Cielo colectivo (tránsitos mundanos) para una fecha y su ventana próxima.

    Devuelve las configuraciones planetarias activas del día (aspectos entre
    planetas, independientes de la ubicación) y, si el engine tiene desplegado
    el módulo mundana, lo enriquece con configuraciones nombradas y p-values
    empíricos del corpus H_mundana_A.

    Args:
        fecha: ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SSZ). Vacío = hoy (UTC).
        ventana_dias: días hacia adelante para configuraciones próximas (mundana).

    Returns:
        {
          fecha, posiciones[], configuraciones_activas[],
          mundana_enrichment: bool,
          mundana: {sky, forecast} | null,
          fuente
        }
    """
    fecha_iso = abu_client.normalize_date(fecha)

    # Cielo geocéntrico: los aspectos no dependen de lat/lon → usamos (0,0).
    chart = abu_client.chart_detailed(fecha_iso, lat=0.0, lon=0.0)

    posiciones = [
        {
            "planeta": p.get("name"),
            "longitud": p.get("longitude"),
            "signo": p.get("sign"),
            "posicion": p.get("formatted"),
            "dignidad": p.get("dignity_traditional") or p.get("dignity_score"),
        }
        for p in chart.get("planets", [])
    ]
    configuraciones = _configuraciones_desde_aspectos(chart.get("aspects", []))
    _anotar_fase(configuraciones, fecha_iso, 0.0, 0.0)

    # Enriquecimiento mundana (opcional — solo si la ruta existe en el engine).
    sky = abu_client.mundana_sky()
    forecast = abu_client.mundana_forecast(ventana_dias) if sky is not None else None
    enriched = sky is not None

    return {
        "fecha": fecha_iso,
        "posiciones": posiciones,
        "configuraciones_activas": configuraciones,
        "mundana_enrichment": enriched,
        "mundana": {"sky": sky, "forecast": forecast} if enriched else None,
        "fuente": "abu-engine /api/astro/chart-detailed"
        + (" + /api/mundana/*" if enriched else " (mundana no desplegada en esta imagen)"),
    }


@mcp.tool()
def cielo_instante(fecha: str, lat: float = 0.0, lon: float = 0.0) -> dict[str, Any]:
    """
    Carta del cielo para un instante y ubicación arbitrarios (incluye pasado).

    A diferencia de calcular_transitos (colectivo, geocéntrico), esto sitúa el
    cielo en un lugar: agrega casas Placidus, Ascendente, Medio Cielo y la
    Parte de la Fortuna locales.

    Args:
        fecha: ISO (YYYY-MM-DD o con hora). Requerido.
        lat: latitud decimal (default 0 = ecuador).
        lon: longitud decimal (default 0 = Greenwich).

    Returns:
        {fecha, ubicacion, ascendente, medio_cielo, posiciones[],
         configuraciones[], parte_fortuna, fuente}
    """
    fecha_iso = abu_client.normalize_date(fecha)
    chart = abu_client.chart_detailed(fecha_iso, lat=lat, lon=lon)

    posiciones = [
        {
            "planeta": p.get("name"),
            "longitud": p.get("longitude"),
            "signo": p.get("sign"),
            "posicion": p.get("formatted"),
            "casa": p.get("house"),
            "dignidad": p.get("dignity_traditional"),
        }
        for p in chart.get("planets", [])
    ]

    configuraciones = _configuraciones_desde_aspectos(chart.get("aspects", []))
    _anotar_fase(configuraciones, fecha_iso, lat, lon)
    return {
        "fecha": fecha_iso,
        "ubicacion": chart.get("location"),
        "ascendente": chart.get("asc"),
        "medio_cielo": chart.get("mc"),
        "posiciones": posiciones,
        "configuraciones": configuraciones,
        "parte_fortuna": chart.get("arabic_parts", {}).get("part_of_fortune"),
        "fuente": "abu-engine /api/astro/chart-detailed",
    }


@mcp.tool()
def traer_doctrina(tema: str, tags: list[str] | None = None, k: int = 3) -> dict[str, Any]:
    """
    Recupera fragmentos doctrinales relevantes del corpus de Abu Oracle.

    Fuente: repo ai-oracle (system prompt de Lilly, Axiomática de los Cielos,
    técnicas persas, Grimoire, registro de voz). Retrieval léxico por palabras
    clave — devuelve el material para que la capa interpretativa lo cite.

    Args:
        tema: consulta en lenguaje natural (ej. "dignidad de Saturno", "secta").
        tags: términos adicionales para afinar (ej. ["firdaria", "profección"]).
        k: cantidad de fragmentos a devolver (default 3).

    Returns:
        {tema, resultados: [{fuente, titulo, fragmento, score}], fuentes_indexadas}
    """
    resultados = doctrine.retrieve(tema, tags, k)
    return {
        "tema": tema,
        "tags": tags or [],
        "resultados": resultados,
        "fuentes_indexadas": doctrine.source_status(),
    }


@mcp.tool()
def linea_biografica(
    fecha_nacimiento: str,
    lat: float,
    lon: float,
    meses_adelante: int = 12,
) -> dict[str, Any]:
    """
    Capa temporal DETERMINISTA de una carta natal: profección anual, firdaria
    y tránsitos mayores, calculados por Abu Engine (no improvisados).

    Es la fuente correcta para "¿qué período está hablando ahora?" y "¿qué
    tránsitos vienen?". Devuelve la profección y firdaria activas y siguientes,
    los tránsitos activos hoy y los próximos exactos dentro de la ventana.
    Requiere ABU_SERVICE_KEY configurada (endpoint protegido del engine).

    Args:
        fecha_nacimiento: ISO con hora UTC (ej. "1602-05-11T14:00:00Z").
        lat: latitud natal decimal.
        lon: longitud natal decimal.
        meses_adelante: ventana de tránsitos próximos (default 12, máx ~18).

    Returns:
        {profeccion: {activa, siguiente}, firdaria: {activa, siguientes},
         transitos: {activos[], proximos[]}, fuente}
    """
    fecha_iso = abu_client.normalize_date(fecha_nacimiento)
    bio = abu_client.biography(fecha_iso, lat, lon)

    profs = bio.get("profections", [])
    prof_act_i = next((i for i, p in enumerate(profs) if p.get("is_active")), None)
    profeccion = {
        "activa": profs[prof_act_i] if prof_act_i is not None else None,
        "siguiente": profs[prof_act_i + 1] if prof_act_i is not None and prof_act_i + 1 < len(profs) else None,
    }

    firs = bio.get("firdaria", [])
    fir_act_i = next((i for i, f in enumerate(firs) if f.get("is_active")), None)
    firdaria = {
        "activa": firs[fir_act_i] if fir_act_i is not None else None,
        "siguientes": firs[fir_act_i + 1 : fir_act_i + 3] if fir_act_i is not None else [],
    }

    from datetime import datetime, timedelta, timezone
    hoy = datetime.now(timezone.utc)
    limite = hoy + timedelta(days=30.44 * max(1, meses_adelante))

    def _compacto(t: dict) -> dict:
        return {
            "transito": t.get("transit_planet"),
            "aspecto": t.get("aspect"),
            "natal": t.get("natal_planet"),
            "exacto": t.get("exact_date"),
            "activo": bool(t.get("is_active")),
            "clase": t.get("speed_class", "slow"),
        }

    def _fecha(t: dict):
        try:
            return datetime.fromisoformat(str(t.get("exact_date"))).replace(tzinfo=timezone.utc)
        except Exception:
            return None

    ventana = bio.get("transits_window", [])
    activos = [_compacto(t) for t in ventana if t.get("is_active")]
    # Lentos: toda la ventana pedida. Rápidos (Sol/Mercurio/Venus/Marte): solo
    # los próximos 45 días — relevantes para pronóstico de quincena/mes, pero
    # incluirlos a 12 meses inundaría el contexto. (Gap detectado en uso real:
    # el filtro slow-only ocultó un Marte□Saturno a 2 semanas.)
    limite_rapidos = hoy + timedelta(days=45)
    candidatos = [
        _compacto(t)
        for t in ventana
        if not t.get("is_active")
        and (f := _fecha(t)) is not None
        and hoy <= f <= (limite if t.get("speed_class", "slow") == "slow" else limite_rapidos)
    ]
    # Cupos separados: los rápidos (numerosos) no deben expulsar a los lentos
    # del final de la ventana (un Saturno□Sol a 9 meses pesa más que el enésimo
    # sextil de Venus a 3 semanas).
    candidatos.sort(key=lambda c: c["exacto"] or "")
    lentos = [c for c in candidatos if c["clase"] == "slow"][:25]
    rapidos = [c for c in candidatos if c["clase"] != "slow"][:15]
    proximos = sorted(lentos + rapidos, key=lambda c: c["exacto"] or "")

    return {
        "fecha_nacimiento": fecha_iso,
        "profeccion": profeccion,
        "firdaria": firdaria,
        "transitos": {"activos": activos, "proximos": proximos},
        "fuente": "abu-engine /api/astro/biography (determinista — profecciones 90 años, firdaria 75, tránsitos ±18m)",
    }


@mcp.tool()
def consultar_biblioteca(
    pregunta: str,
    tradicion: str = "",
    libro: str = "",
    k: int = 5,
) -> dict[str, Any]:
    """
    Consulta los textos primarios clásicos de la biblioteca astrológica.

    Distinto de traer_doctrina (doctrina interna de Abu Oracle): esto busca en
    las FUENTES PRIMARIAS — Ptolomeo (Tetrabiblos), William Lilly (Introduction
    to Astrology 1852), Al-Biruni, textos Jyotish, Hans Kayser — y devuelve
    pasajes con cita verificable (autor, libro, página). Usalo para fundamentar
    una interpretación en la tradición o comparar escuelas.

    Args:
        pregunta: consulta en lenguaje natural (ej. "Mars Saturn opposition
                  effects", "combustión del planeta cerca del Sol"). Los textos
                  están mayormente en inglés — consultar en inglés recupera más.
        tradicion: filtro opcional: helenistica | occidental-lilly | persa |
                   jyotish | armonica | pitagorica.
        libro: filtro opcional por substring del título.
        k: cantidad de pasajes (default 5).

    Returns:
        {pregunta, resultados: [{autor, libro, tradicion, pagina, fragmento,
         score}], catalogo_disponible}
    """
    out = biblioteca.consultar(pregunta, tradicion or None, libro or None, k)
    out["catalogo_disponible"] = biblioteca.catalogo()
    return out


@mcp.tool()
def carta_natal(fecha_nacimiento: str, lat: float, lon: float = 0.0) -> dict[str, Any]:
    """
    La carta natal doctrinal completa — lo que cielo_instante NO da: secta, lotes, firdaria, profección.

    Devuelve el frame doctrinal completo de una carta natal, incluyendo la
    secta (diurna/nocturna), las posiciones planetarias con dignidades, los
    lotes arábigos principales con su señor, la firdaria y la profección anual.
    Endpoint protegido: requiere ABU_SERVICE_KEY.

    Args:
        fecha_nacimiento: ISO de nacimiento (YYYY-MM-DD o con hora). Requerido.
        lat: Latitud natal decimal. Requerido.
        lon: Longitud natal decimal (default 0 = Greenwich).

    Returns:
        {fecha, ubicacion, secta, ascendente, medio_cielo, posiciones[...],
         lotes[...], profeccion, firdaria, fuente} | {error}
    """
    fecha_iso = abu_client.normalize_date(fecha_nacimiento)
    chart = abu_client.chart_extended(fecha_iso, lat, lon)

    # La respuesta tiene DOS bloques: `chart` (planetas, asc/mc, location) y
    # `extended` (lotes, fardars, profecciones, dignidades). El frame doctrinal
    # vive en `extended` — verificado contra el engine vivo 2026-06-14.
    data = chart.get("chart", {})
    ext = chart.get("extended", {})
    fardars = ext.get("fardars", {})  # dict: {fardars, current, is_diurnal}

    posiciones = [
        {
            "planeta": p.get("name"),
            "signo": p.get("sign"),
            "grado": p.get("degree_in_sign", p.get("degree")),
            "casa": p.get("house"),
            "dignidad": p.get("dignity_traditional"),
            "retrogrado": p.get("retrograde"),
        }
        for p in data.get("planets", [])
    ]

    lotes = [
        {
            "nombre": lote.get("name"),
            "signo": lote.get("sign"),
            "grado": lote.get("degree"),
            "casa": lote.get("house"),
            "senor": lote.get("lord"),
        }
        for lote in ext.get("lots", [])
    ]

    # Firdaria activa: extended.fardars.current. Profección: extended.profections (dict).
    firdaria_activa = fardars.get("current")
    profeccion_activa = ext.get("profections")

    return {
        "fecha": fecha_iso,
        "ubicacion": data.get("location"),
        "secta": "diurna" if fardars.get("is_diurnal") else "nocturna",
        "ascendente": data.get("asc"),
        "medio_cielo": data.get("mc"),
        "posiciones": posiciones,
        "lotes": lotes,
        "profeccion": profeccion_activa,
        "firdaria": firdaria_activa,
        "fuente": "abu-engine /api/astro/chart/extended",
    }


@mcp.tool()
def revolucion_solar(
    fecha_nacimiento: str, lat: float, lon: float = 0.0, anio: int = 0
) -> dict[str, Any]:
    """
    Carta del retorno solar (revolución solar) para un año — el pulso anual, distinto cada año.

    Calcula la carta para el momento exacto en que el Sol vuelve a su posición
    natal en un año determinado. Útil para pronósticos anuales.
    Endpoint protegido: requiere ABU_SERVICE_KEY.

    Args:
        fecha_nacimiento: ISO de nacimiento (YYYY-MM-DD o con hora). Requerido.
        lat: Latitud natal decimal. Requerido.
        lon: Longitud natal decimal (default 0 = Greenwich).
        anio: Año para el cual calcular el retorno (ej. 2024). Si es 0 o se
              omite, usa el año del retorno solar más próximo.

    Returns:
        {datetime_sr, posiciones[], ascendente_sr, medio_cielo_sr,
         configuraciones[], fuente} | {error}
    """
    fecha_iso = abu_client.normalize_date(fecha_nacimiento)
    sr_data = abu_client.solar_return(fecha_iso, lat, lon, year=anio if anio > 0 else None)

    # La respuesta del engine ya tiene un buen shape. Solo anotamos fuente.
    sr_data["fuente"] = "abu-engine /api/astro/solar-return"
    return sr_data


@mcp.tool()
def lunaciones_eclipses(
    fecha_nacimiento: str, lat: float, lon: float = 0.0, momento: str = ""
) -> dict[str, Any]:
    """
    Pulso lunar (lunaciones, eclipses) relativo a una CARTA NATAL.

    Calcula la fase lunar para un momento dado (`momento`, default=ahora) y
    proyecta las próximas lunaciones y eclipses, indicando en qué CASA NATAL
    del nativo (definido por `fecha_nacimiento`, `lat`, `lon`) caerán.

    Args:
        fecha_nacimiento: ISO de nacimiento (YYYY-MM-DD o con hora). Requerido.
        lat: Latitud natal decimal. Requerido.
        lon: Longitud natal decimal (default 0 = Greenwich).
        momento: Opcional. Fecha/hora ISO para la que se calcula la fase lunar
                 actual (default: ahora).

    Returns:
        {sol, luna, fase, proxima_nueva, proxima_llena, proximo_eclipse_solar,
         proximo_eclipse_lunar, fuente} | {error}
    """
    birth_date_iso = abu_client.normalize_date(fecha_nacimiento)
    query_dt_iso = abu_client.normalize_date(momento) if momento else None
    lunar_data = abu_client.lunar(birth_date_iso, lat, lon, query_dt=query_dt_iso)

    if lunar_data is None:
        return {
            "error": "El endpoint /api/astro/lunar no está disponible en el engine.",
            "fuente": "abu-engine",
        }

    lunar_data["fuente"] = "abu-engine /api/astro/lunar"
    return lunar_data


@mcp.tool()
def mundana_pronostico(dias: int = 90, tipo_config: str = "") -> dict[str, Any]:
    """
    Pronóstico de astrología mundana: configuraciones activas, próximas e históricas.

    Combina tres endpoints del motor de astrología mundana (si está desplegado):
    1. /sky: configuraciones activas ahora (con p-value/densidad).
    2. /forecast: configuraciones que se perfeccionarán en los próximos `dias`.
    3. /history: contexto histórico para un `tipo_config` (ej. "Marte-Saturno").

    Args:
        dias: Días hacia adelante para el pronóstico (default 90).
        tipo_config: Opcional. Filtra el contexto histórico por un tipo de
                     configuración (ej. "Júpiter-Urano").

    Returns:
        {cielo_actual, pronostico, contexto_historico, fuente}
    """
    sky = abu_client.mundana_sky()
    forecast = abu_client.mundana_forecast(dias)
    history = abu_client.mundana_history(tipo_config if tipo_config else None)

    available = sky is not None or forecast is not None or history is not None

    return {
        "cielo_actual": sky,
        "pronostico": forecast,
        "contexto_historico": history,
        "fuente": "abu-engine /api/mundana/*"
        if available
        else "abu-engine (mundana no desplegada en esta imagen)",
    }


if __name__ == "__main__":
    import os
    # Transport se controla con env var MCP_TRANSPORT=sse|stdio (default: stdio).
    # Puerto se controla con FASTMCP_PORT (default FastMCP: 8000).
    # Ambas deben estar seteadas ANTES de iniciar el proceso (no dentro del script).
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)  # type: ignore[arg-type]
