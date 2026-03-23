# -*- coding: utf-8 -*-
"""
src/market_data.py — Datos de mercado: precios, sectores, ETFs

Orquesta la descarga y limpieza de precios de acciones, ETFs
y sectores. Usa data_sources.py para las descargas reales.

Funciones de nivel alto que el resto del sistema consume:
  - get_prices()      → precios históricos limpios por ticker
  - get_sector_map()  → mapeo ticker → sector
  - get_market_summary() → resumen de mercado actual

Estado: STUB — implementación completa en Fase 2
"""

import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd

log = logging.getLogger(__name__)

# Sectores S&P 500 con sus ETFs de referencia
SECTOR_ETFS: Dict[str, Tuple[str, str]] = {
    "XLC":  ("Comunicación",          "Communication Services"),
    "XLY":  ("Consumo Discrecional",  "Consumer Discretionary"),
    "XLP":  ("Consumo Básico",        "Consumer Staples"),
    "XLE":  ("Energía",               "Energy"),
    "XLF":  ("Financiero",            "Financials"),
    "XLV":  ("Salud",                 "Health Care"),
    "XLI":  ("Industriales",          "Industrials"),
    "XLB":  ("Materiales",            "Materials"),
    "XLRE": ("Bienes Raíces",         "Real Estate"),
    "XLK":  ("Tecnología",            "Technology"),
    "XLU":  ("Servicios Públicos",    "Utilities"),
}


def get_prices(
    tickers: List[str],
    years: int = 5,
    base_currency: str = "USD",
) -> pd.DataFrame:
    """Descarga y limpia precios históricos de cierre ajustados.

    Args:
        tickers: Lista de tickers a descargar.
        years: Años de historial.
        base_currency: Moneda base para conversión FX.

    Returns:
        DataFrame con fechas como índice y tickers como columnas.
        Columnas con menos del 70% de datos válidos se marcan con warning.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar get_prices")


def get_sector_etf_prices(years: int = 5) -> pd.DataFrame:
    """Descarga precios de los 11 ETFs de sector S&P 500.

    Returns:
        DataFrame con precios de cierre de los ETFs sectoriales.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar sector ETF prices")


def get_ticker_info(ticker: str) -> Dict:
    """Obtiene metadata de un ticker (sector, país, industria, moneda).

    Args:
        ticker: Símbolo de Yahoo Finance.

    Returns:
        Dict con campos: sector, industry, country, currency, quoteType, longName.
        Campos faltantes regresan como 'N/A'.

    TODO (Fase 2): Implementar con yf.Ticker.info y manejo de errores.
    """
    raise NotImplementedError("Fase 2: implementar ticker info")


def get_returns(prices: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """Calcula retornos a partir de una matriz de precios.

    Args:
        prices: DataFrame de precios (fechas × tickers).
        freq: 'D' = diario, 'W' = semanal, 'M' = mensual.

    Returns:
        DataFrame de retornos del mismo shape (menos una fila).

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar cálculo de retornos")
