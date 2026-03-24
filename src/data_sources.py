# -*- coding: utf-8 -*-
"""
src/data_sources.py — Capa de descarga de datos

Centraliza TODA la descarga de datos externos (Yahoo Finance, FRED).
El resto del sistema nunca llama a yfinance o pandas_datareader
directamente — solo usa este módulo.

Rescatado de:
  - que_va_a_pasar_en_el_mercado_.py líneas 94-251
  - umpa_ultra_mejorado_2_0_15_01_2026.py líneas 129-147
"""

import logging
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf

log = logging.getLogger(__name__)

# FRED via pandas_datareader (opcional) o requests directo
_HAS_PDR = False
try:
    from pandas_datareader import data as pdr
    _HAS_PDR = True
except (ImportError, TypeError):
    pdr = None

# Fallback: requests directo a la API de FRED
try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False

if not _HAS_PDR:
    log.info("pandas_datareader no disponible — usando fallback HTTP para FRED.")


# ─────────────────────────────────────────────
# Yahoo Finance
# ─────────────────────────────────────────────

def _download_one_ticker(
    ticker: str, start: str, end: str, auto_adjust: bool = True,
) -> pd.Series:
    """Descarga precios de cierre de un solo ticker de Yahoo Finance.

    Args:
        ticker: Ticker de Yahoo Finance.
        start: 'YYYY-MM-DD'.
        end: 'YYYY-MM-DD'.
        auto_adjust: Usar precios ajustados.

    Returns:
        pd.Series de precios de cierre (puede estar vacía).
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            df = yf.download(
                tickers=ticker,
                start=start,
                end=pd.Timestamp(end) + pd.Timedelta(days=1),
                auto_adjust=auto_adjust,
                progress=False,
                threads=False,
                group_by="column",
            )
        if df is None or len(df) == 0:
            return pd.Series(dtype=float, name=ticker)

        # Manejar MultiIndex (yfinance a veces devuelve columnas multi-nivel)
        if isinstance(df.columns, pd.MultiIndex):
            if ticker in df["Close"].columns:
                s = df["Close"][ticker].copy()
            else:
                s = df["Close"].iloc[:, 0].copy()
        else:
            s = df["Close"].copy() if "Close" in df.columns else df.iloc[:, 0].copy()

        s = s.dropna()
        s.name = ticker
        return s
    except Exception as exc:
        log.debug("Error descargando %s: %s", ticker, exc)
        return pd.Series(dtype=float, name=ticker)


def download_prices_yahoo(
    tickers: List[str],
    start: str,
    end: str,
    auto_adjust: bool = True,
    min_points: int = 50,
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """Descarga precios de cierre ajustados para una lista de tickers.

    Cada ticker se descarga individualmente para robusted.

    Args:
        tickers: Lista de tickers.
        start: 'YYYY-MM-DD'.
        end: 'YYYY-MM-DD'.
        auto_adjust: Usar precios ajustados.
        min_points: Mínimo de puntos válidos.

    Returns:
        Tupla (prices_df, tickers_ok, tickers_failed).
        prices_df tiene fechas como índice y tickers como columnas.
    """
    prices = {}
    ok = []
    failed = []

    for ticker in tickers:
        s = _download_one_ticker(ticker, start, end, auto_adjust)
        if len(s) >= min_points:
            prices[ticker] = s
            ok.append(ticker)
        else:
            failed.append(ticker)
            log.warning("Ticker %s: solo %d puntos (mínimo %d) — omitido.", ticker, len(s), min_points)

    if not prices:
        return pd.DataFrame(), ok, failed

    df = pd.DataFrame(prices).sort_index()
    # Eliminar última fila si es toda NaN
    if len(df) > 0 and df.tail(1).isna().all(axis=1).iloc[0]:
        df = df.iloc[:-1]

    return df, ok, failed


def download_universe_with_fallbacks(
    universe: Dict[str, Tuple[str, List[str]]],
    start: str,
    end: str,
    auto_adjust: bool = True,
    min_points: int = 200,
) -> Tuple[pd.DataFrame, Dict[str, Optional[str]], List[str]]:
    """Descarga un universo de activos, intentando fallbacks por cada uno.

    universe format: { 'clave_interna': ('Nombre completo', ['TICKER1', 'TICKER2']) }

    Args:
        universe: Diccionario con claves internas, nombres y listas de fallback.
        start: 'YYYY-MM-DD'.
        end: 'YYYY-MM-DD'.
        auto_adjust: Usar precios ajustados.
        min_points: Mínimo de puntos de datos válidos.

    Returns:
        Tupla (prices_df, chosen_dict, missing_keys).
        prices_df tiene claves internas como columnas.
        chosen_dict: {clave: ticker_elegido_o_None}.
        missing_keys: claves que no se pudieron descargar.
    """
    prices = pd.DataFrame()
    chosen: Dict[str, Optional[str]] = {}
    missing: List[str] = []

    for key, (full_name, ticker_list) in universe.items():
        best = pd.Series(dtype=float)
        best_ticker = None

        for tkr in ticker_list:
            s = _download_one_ticker(tkr, start, end, auto_adjust)
            if len(s.dropna()) >= min_points:
                best = s
                best_ticker = tkr
                break

        if best_ticker is None:
            missing.append(key)
            chosen[key] = None
            prices[key] = np.nan
        else:
            chosen[key] = best_ticker
            prices[key] = best

    prices = prices.sort_index()
    if len(prices) > 0 and prices.tail(1).isna().all(axis=1).iloc[0]:
        prices = prices.iloc[:-1]

    if missing:
        log.warning("Series Yahoo faltantes: %s", missing)

    return prices, chosen, missing


# ─────────────────────────────────────────────
# FRED (Federal Reserve Economic Data)
# ─────────────────────────────────────────────

def _fred_via_pdr(series_id: str, start: str, end: str) -> Optional[pd.Series]:
    """Intenta descargar serie FRED con pandas_datareader."""
    if not _HAS_PDR:
        return None
    try:
        s = pdr.DataReader(series_id, "fred", start, end)[series_id]
        s = s.dropna()
        return s if len(s) > 0 else None
    except Exception:
        return None


def _fred_via_http(series_id: str, start: str, end: str, api_key: str = "") -> Optional[pd.Series]:
    """Descarga serie FRED vía HTTP directo (fallback sin pandas_datareader)."""
    if not _HAS_REQUESTS:
        return None
    # API pública de FRED (sin key funciona con límites)
    base_url = "https://fred.stlouisfed.org/graph/fredgraph.csv"
    params = {
        "id": series_id,
        "cosd": start,
        "coed": end,
    }
    try:
        resp = _requests.get(base_url, params=params, timeout=15)
        if resp.status_code != 200:
            return None
        from io import StringIO
        df = pd.read_csv(StringIO(resp.text), parse_dates=["DATE"], index_col="DATE")
        if df.empty:
            return None
        s = df.iloc[:, 0].replace(".", np.nan).astype(float).dropna()
        s.name = series_id
        return s if len(s) > 0 else None
    except Exception as exc:
        log.debug("FRED HTTP %s falló: %s", series_id, exc)
        return None


def fred_get_series(
    series_id: str,
    start: str,
    end: str,
    api_key: str = "",
) -> Optional[pd.Series]:
    """Descarga una serie de FRED (intenta pdr, luego HTTP directo).

    Args:
        series_id: ID de la serie (ej. 'DGS10').
        start: 'YYYY-MM-DD'.
        end: 'YYYY-MM-DD'.
        api_key: Clave de FRED (opcional).

    Returns:
        pd.Series con datos, o None si falla.
    """
    # Intentar pandas_datareader primero
    s = _fred_via_pdr(series_id, start, end)
    if s is not None:
        return s

    # Fallback: HTTP directo
    s = _fred_via_http(series_id, start, end, api_key)
    if s is not None:
        return s

    log.debug("FRED %s: no se pudo descargar por ningún método.", series_id)
    return None


def fred_get_multiple(
    series_dict: Dict[str, Tuple[str, List[str]]],
    start: str,
    end: str,
    api_key: str = "",
) -> Tuple[pd.DataFrame, Dict[str, Optional[str]], List[str]]:
    """Descarga múltiples series de FRED con IDs alternativos.

    series_dict format: { 'nombre_interno': ('Nombre completo', ['ID1', 'ID2']) }

    Args:
        series_dict: Diccionario con nombres internos y listas de IDs candidatos.
        start: 'YYYY-MM-DD'.
        end: 'YYYY-MM-DD'.
        api_key: Clave de FRED.

    Returns:
        Tupla (df, chosen, missing).
        df tiene nombres internos como columnas.
        chosen: {nombre: id_elegido_o_None}.
        missing: nombres que no se pudieron descargar.
    """
    data = {}
    chosen: Dict[str, Optional[str]] = {}
    missing: List[str] = []

    for key, (full_name, id_list) in series_dict.items():
        best = None
        best_id = None

        for sid in id_list:
            s = fred_get_series(sid, start, end, api_key)
            if s is not None and len(s) >= 10:
                best = s
                best_id = sid
                break

        if best_id is None:
            missing.append(key)
            chosen[key] = None
            data[key] = pd.Series(dtype=float)
        else:
            chosen[key] = best_id
            data[key] = best

    df = pd.DataFrame(data).sort_index()

    if missing:
        log.warning("Series FRED faltantes: %s", missing)

    return df, chosen, missing


# ─────────────────────────────────────────────
# FX (Tipo de Cambio)
# ─────────────────────────────────────────────

def _fx_pair_ticker(from_ccy: str, to_ccy: str) -> str:
    """Construye ticker Yahoo para un par FX."""
    return f"{from_ccy}{to_ccy}=X"


def get_fx_spot(from_ccy: str, to_ccy: str) -> float:
    """Obtiene tipo de cambio spot actual.

    Args:
        from_ccy: Moneda origen (ej. 'USD').
        to_ccy: Moneda destino (ej. 'MXN').

    Returns:
        Tipo de cambio. 1.0 si misma moneda o en caso de error.
    """
    if not from_ccy or not to_ccy or from_ccy == to_ccy:
        return 1.0
    try:
        px = yf.Ticker(_fx_pair_ticker(from_ccy, to_ccy)).history(
            period="5d", interval="1d"
        )["Close"].dropna()
        if not px.empty:
            return float(px.iloc[-1])
    except Exception:
        pass
    # Intentar el inverso
    try:
        px = yf.Ticker(_fx_pair_ticker(to_ccy, from_ccy)).history(
            period="5d", interval="1d"
        )["Close"].dropna()
        if not px.empty:
            return 1.0 / float(px.iloc[-1])
    except Exception:
        pass
    log.warning("No se pudo obtener FX %s/%s — usando 1.0", from_ccy, to_ccy)
    return 1.0


def get_fx_series(from_ccy: str, to_ccy: str, start: str) -> pd.Series:
    """Serie histórica de tipo de cambio.

    Args:
        from_ccy: Moneda origen.
        to_ccy: Moneda destino.
        start: 'YYYY-MM-DD'.

    Returns:
        pd.Series con tipo de cambio diario.
        Serie de 1.0 si misma moneda o error.
    """
    if not from_ccy or not to_ccy or from_ccy == to_ccy:
        return pd.Series(1.0, index=pd.date_range(start=start, end=datetime.today(), freq="D"))

    # Intentar par directo
    for pair, invert in [(_fx_pair_ticker(from_ccy, to_ccy), False),
                         (_fx_pair_ticker(to_ccy, from_ccy), True)]:
        try:
            s = yf.Ticker(pair).history(start=start, auto_adjust=False)["Close"].dropna()
            if not s.empty:
                return (1.0 / s) if invert else s
        except Exception:
            pass

    log.warning("No se pudo obtener serie FX %s/%s — devolviendo 1.0", from_ccy, to_ccy)
    return pd.Series(1.0, index=pd.date_range(start=start, end=datetime.today(), freq="D"))


# ─────────────────────────────────────────────
# Risk-Free Rate (UST 10Y)
# ─────────────────────────────────────────────

def get_risk_free_usd(fallback: float = 0.04) -> Tuple[float, str]:
    """Obtiene la tasa libre de riesgo USD (UST 10Y).

    Intenta en orden: FRED:DGS10 → Yahoo:^TNX → fallback.

    Args:
        fallback: Tasa por defecto si todo falla.

    Returns:
        Tupla (tasa_decimal, fuente).
    """
    # 1) FRED DGS10
    try:
        today = datetime.today()
        start_d = (today - timedelta(days=400)).strftime("%Y-%m-%d")
        end_d = today.strftime("%Y-%m-%d")
        s = fred_get_series("DGS10", start_d, end_d)
        if s is not None and len(s) > 0:
            rf = float(s.iloc[-1]) / 100.0
            if 0.0 < rf < 0.20:
                log.info("Risk-free USD: %.4f (FRED:DGS10)", rf)
                return rf, "FRED:DGS10"
    except Exception:
        pass

    # 2) Yahoo ^TNX
    try:
        tnx = yf.Ticker("^TNX").history(period="400d")["Close"].dropna()
        if len(tnx) > 0:
            rf = float(tnx.iloc[-1]) / 100.0
            if 0.0 < rf < 0.20:
                log.info("Risk-free USD: %.4f (Yahoo:^TNX)", rf)
                return rf, "Yahoo:^TNX"
    except Exception:
        pass

    # 3) Fallback
    log.warning("Risk-free USD: usando fallback %.4f", fallback)
    return fallback, "config_fallback"


def get_blended_erp_usd(
    rf: float,
    erp_min: float = 0.035,
    erp_max: float = 0.060,
    erp_fallback: float = 0.055,
) -> Tuple[float, str]:
    """Calcula ERP blended USD desde retornos históricos de SPY.

    Promedia ERPs implícitos a 5, 10 y 30 años.

    Args:
        rf: Tasa libre de riesgo actual.
        erp_min: Mínimo del ERP.
        erp_max: Máximo del ERP.
        erp_fallback: Fallback si el cálculo falla.

    Returns:
        Tupla (erp, fuente).
    """
    vals = []
    for yrs in [5, 10, 30]:
        try:
            start = (datetime.today() - timedelta(days=yrs * 365)).strftime("%Y-%m-%d")
            h = yf.Ticker("SPY").history(start=start, interval="1mo")["Close"].dropna()
            if len(h) >= 2:
                dur = (h.index[-1] - h.index[0]).days / 365.25
                if dur > 0:
                    cagr = (h.iloc[-1] / h.iloc[0]) ** (1 / dur) - 1
                    vals.append(float(np.clip(cagr - rf, erp_min, erp_max)))
        except Exception:
            pass

    if not vals:
        log.warning("ERP blended: usando fallback %.4f", erp_fallback)
        return erp_fallback, "config_fallback"

    erp = float(np.mean(vals))
    log.info("ERP blended USD: %.4f (SPY %d/%d/%d años)", erp, 5, 10, 30)
    return erp, f"SPY_blended_{len(vals)}horizons"
