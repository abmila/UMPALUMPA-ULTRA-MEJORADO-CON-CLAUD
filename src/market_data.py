# -*- coding: utf-8 -*-
"""
src/market_data.py — Datos de mercado: precios, sectores, ETFs

Orquesta la descarga y limpieza de precios de acciones, ETFs
y sectores. Usa data_sources.py para las descargas reales.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.config_loader import CFG
from src.data_sources import download_prices_yahoo, download_universe_with_fallbacks

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


def _compute_dates(years: int) -> Tuple[str, str]:
    """Calcula fechas de inicio y fin a partir de años de historial."""
    end = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(years=years)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def get_prices(
    tickers: List[str],
    years: int = 5,
    base_currency: str = "USD",
    min_points: int = 50,
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """Descarga y limpia precios históricos de cierre ajustados.

    Args:
        tickers: Lista de tickers.
        years: Años de historial.
        base_currency: Moneda base (TODO: conversión FX en Fase 3).
        min_points: Mínimo de puntos de datos.

    Returns:
        Tupla (prices_df, tickers_ok, tickers_failed).
        prices_df tiene fechas como índice y tickers como columnas.
    """
    start, end = _compute_dates(years)
    log.info("Descargando precios: %d tickers, %s → %s", len(tickers), start, end)

    prices, ok, failed = download_prices_yahoo(tickers, start, end, min_points=min_points)

    if failed:
        log.warning("Tickers sin datos suficientes: %s", failed)
    log.info("Precios descargados: %d/%d tickers, %d filas",
             len(ok), len(tickers), len(prices))

    return prices, ok, failed


def get_sector_etf_prices(years: int = 5) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """Descarga precios de los 11 ETFs de sector S&P 500.

    Args:
        years: Años de historial.

    Returns:
        Tupla (prices_df, ok, failed).
    """
    sector_tickers = list(SECTOR_ETFS.keys())
    return get_prices(sector_tickers, years=years)


def get_ticker_info(ticker: str) -> Dict:
    """Obtiene metadata de un ticker (sector, país, industria, moneda).

    Args:
        ticker: Símbolo de Yahoo Finance.

    Returns:
        Dict con campos normalizados. Campos faltantes = 'N/A'.
    """
    import yfinance as yf

    defaults = {
        "sector": "N/A",
        "industry": "N/A",
        "country": "N/A",
        "currency": "USD",
        "quoteType": "EQUITY",
        "longName": ticker,
        "marketCap": np.nan,
    }

    try:
        info = yf.Ticker(ticker).info or {}
        for key in defaults:
            if key in info and info[key] is not None:
                defaults[key] = info[key]
    except Exception as exc:
        log.warning("No se pudo obtener info de %s: %s", ticker, exc)

    return defaults


def get_returns(prices: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """Calcula retornos a partir de una matriz de precios.

    Args:
        prices: DataFrame de precios (fechas × tickers).
        freq: 'D' = diario, 'W' = semanal, 'M' = mensual.

    Returns:
        DataFrame de retornos (filas = periodos - 1).
    """
    if freq == "W":
        p = prices.resample("W-FRI").last()
    elif freq == "M":
        p = prices.resample("ME").last()
    else:
        p = prices

    return p.pct_change().dropna(how="all")


def get_forward_returns(
    prices: pd.DataFrame,
    horizons_bdays: List[int],
) -> pd.DataFrame:
    """Calcula retornos futuros para múltiples horizontes.

    Args:
        prices: DataFrame de precios.
        horizons_bdays: Horizontes en días hábiles.

    Returns:
        DataFrame con columnas tipo '{TICKER}_{H}d_fwd'.
    """
    result = pd.DataFrame(index=prices.index)

    for h in horizons_bdays:
        for col in prices.columns:
            fwd = np.log(prices[col].shift(-h) / prices[col])
            result[f"{col}_{h}d_fwd"] = fwd

    return result
