# -*- coding: utf-8 -*-
"""
src/data_sources.py — Capa de descarga de datos

Centraliza TODA la descarga de datos externos (Yahoo Finance, FRED).
El resto del sistema nunca llama a yfinance o pandas_datareader
directamente — solo usa este módulo.

Diseño:
  - Fallbacks robustos (si un ticker falla, intenta alternativas)
  - Warnings claros cuando faltan series
  - Sin input() — todo configurado externamente
  - Fácil de cambiar la fuente sin romper la lógica de negocio

Origen: rescatado de que_va_a_pasar_en_el_mercado_.py
        (_download_one_ticker, download_universe_yahoo,
         fred_try_series, download_fred_candidates — líneas 94-276)
        y de umpa_ultra_mejorado_2_0_15_01_2026.py
        (fx_spot, get_fx_series — líneas 129-147)

Estado: STUB — implementación completa en Fase 2
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd

log = logging.getLogger(__name__)


def download_prices_yahoo(
    tickers: List[str],
    start: str,
    end: str,
    auto_adjust: bool = True,
    min_points: int = 200,
) -> Dict[str, pd.Series]:
    """Descarga precios de cierre ajustados desde Yahoo Finance.

    Intenta cada ticker de forma individual con fallbacks.
    No falla si un ticker no existe — lo omite con warning.

    Args:
        tickers: Lista de tickers de Yahoo Finance.
        start: Fecha inicio 'YYYY-MM-DD'.
        end: Fecha fin 'YYYY-MM-DD'.
        auto_adjust: Si True, usa precios ajustados por splits y dividendos.
        min_points: Mínimo de puntos requeridos para incluir un ticker.

    Returns:
        Dict {ticker: pd.Series de precios de cierre}.

    TODO (Fase 2): Implementar con lógica completa de fallbacks y caché.
    """
    raise NotImplementedError("Fase 2: implementar descarga Yahoo Finance")


def download_universe_with_fallbacks(
    universe: Dict[str, Tuple[str, List[str]]],
    start: str,
    end: str,
    min_points: int = 200,
) -> Dict[str, pd.Series]:
    """Descarga un universo de activos con lista de tickers fallback por activo.

    universe format: { 'clave_interna': ('Nombre completo', ['TICKER1', 'TICKER2']) }

    Args:
        universe: Diccionario con claves internas, nombres y listas de fallback.
        start: Fecha inicio.
        end: Fecha fin.
        min_points: Mínimo de puntos de datos válidos.

    Returns:
        Dict {clave_interna: pd.Series} con los activos que se pudieron descargar.

    TODO (Fase 2): Implementar con fallbacks completos.
    """
    raise NotImplementedError("Fase 2: implementar universo con fallbacks")


def fred_get_series(
    series_id: str,
    start: str,
    end: str,
    api_key: str = "",
) -> Optional[pd.Series]:
    """Descarga una serie de FRED (Federal Reserve Economic Data).

    Args:
        series_id: ID de la serie FRED (ej. 'DGS10', 'CPIAUCSL').
        start: Fecha inicio.
        end: Fecha fin.
        api_key: API key de FRED (opcional, mejora límites).

    Returns:
        pd.Series con la serie, o None si falla.

    TODO (Fase 2): Implementar con pandas_datareader y fallback.
    """
    raise NotImplementedError("Fase 2: implementar descarga FRED")


def fred_get_multiple(
    series_dict: Dict[str, List[str]],
    start: str,
    end: str,
    api_key: str = "",
) -> Dict[str, pd.Series]:
    """Descarga múltiples series de FRED con IDs alternativos por serie.

    series_dict format: { 'nombre_interno': ['ID_PRINCIPAL', 'ID_ALTERNATIVO'] }

    Args:
        series_dict: Diccionario con nombres internos y listas de IDs candidatos.
        start: Fecha inicio.
        end: Fecha fin.
        api_key: API key de FRED.

    Returns:
        Dict {nombre_interno: pd.Series} con lo que se pudo descargar.
        Las series faltantes se omiten con warning.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar descarga FRED múltiple")


def get_fx_spot(from_ccy: str, to_ccy: str) -> float:
    """Obtiene tipo de cambio spot actual entre dos monedas.

    Args:
        from_ccy: Moneda origen (ej. 'USD').
        to_ccy: Moneda destino (ej. 'MXN').

    Returns:
        Tipo de cambio como float. Devuelve 1.0 si from_ccy == to_ccy.

    TODO (Fase 2): Implementar con yfinance.
    """
    if not from_ccy or not to_ccy or from_ccy == to_ccy:
        return 1.0
    raise NotImplementedError("Fase 2: implementar FX spot")


def get_fx_series(from_ccy: str, to_ccy: str, start: str) -> pd.Series:
    """Descarga serie histórica de tipo de cambio.

    Args:
        from_ccy: Moneda origen.
        to_ccy: Moneda destino.
        start: Fecha inicio.

    Returns:
        pd.Series con tipo de cambio diario.

    TODO (Fase 2): Implementar con yfinance e inversión automática.
    """
    if not from_ccy or not to_ccy or from_ccy == to_ccy:
        return pd.Series(dtype=float)
    raise NotImplementedError("Fase 2: implementar FX histórico")


def get_risk_free_usd() -> Tuple[float, str]:
    """Obtiene la tasa libre de riesgo USD (UST 10Y) desde FRED o Yahoo.

    Returns:
        Tupla (tasa_decimal, fuente_string).
        Ej: (0.042, 'FRED:DGS10') o (0.04, 'fallback_config')

    TODO (Fase 2): Implementar con FRED DGS10 → ^TNX → config fallback.
    """
    raise NotImplementedError("Fase 2: implementar risk-free USD")
