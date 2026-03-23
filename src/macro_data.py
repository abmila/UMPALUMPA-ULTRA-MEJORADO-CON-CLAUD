# -*- coding: utf-8 -*-
"""
src/macro_data.py — Datos macroeconómicos

Descarga y estructura datos macro de EUA y México:
  - Tasas de interés
  - Inflación
  - Curva de bonos y spreads
  - Commodities y FX
  - Condiciones financieras

Rescatado de que_va_a_pasar_en_el_mercado_.py líneas 168-267.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.config_loader import CFG
from src.data_sources import (
    download_universe_with_fallbacks,
    fred_get_multiple,
)

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Catálogos de series FRED (rescatados del original)
# ─────────────────────────────────────────────

FRED_CANDIDATES: Dict[str, Tuple[str, List[str]]] = {
    # EUA tasas / curva
    "EFFR":        ("Tasa Fed Funds efectiva (EFFR)",    ["EFFR", "DFF"]),
    "UST_2Y":      ("Treasury 2 años (yield)",            ["DGS2"]),
    "UST_5Y":      ("Treasury 5 años (yield)",            ["DGS5"]),
    "UST_10Y":     ("Treasury 10 años (yield)",           ["DGS10"]),
    "UST_30Y":     ("Treasury 30 años (yield)",           ["DGS30"]),
    "UST_3M":      ("Treasury 3 meses (yield)",           ["TB3MS", "DGS3MO"]),

    # EUA inflación (niveles para YoY)
    "CPI_US":      ("CPI EUA (nivel)",                    ["CPIAUCSL"]),
    "CORE_CPI_US": ("Core CPI EUA (nivel)",               ["CPILFESL"]),
    "PCEPI":       ("PCE Price Index EUA (nivel)",         ["PCEPI"]),
    "PCEPILFE":    ("Core PCE Price Index EUA (nivel)",    ["PCEPILFE"]),

    # EUA actividad/consumo/empleo
    "UNRATE_US":   ("Desempleo EUA",                      ["UNRATE"]),
    "PAYEMS_US":   ("Empleo no agrícola EUA (PAYEMS)",     ["PAYEMS"]),
    "INDPRO_US":   ("Producción industrial EUA",           ["INDPRO"]),
    "RETAIL_US":   ("Ventas minoristas EUA",               ["RSXFS"]),
    "PCE_REAL":    ("Consumo real EUA (PCE real)",          ["PCEC96"]),
    "SENT_US":     ("Sentimiento del consumidor EUA",      ["UMCSENT"]),
    "ISM_PMI":     ("ISM PMI manufacturero EUA",           ["NAPM"]),
    "ICSA":        ("Solicitudes iniciales desempleo",     ["ICSA"]),
    "HOUST":       ("Housing starts EUA",                  ["HOUST"]),
    "PERMIT":      ("Building permits EUA",                ["PERMIT"]),

    # Riesgo/condiciones
    "NFCI":        ("Condiciones financieras (NFCI)",      ["NFCI"]),
    "HY_SPREAD":   ("Spread high-yield (OAS)",             ["BAMLH0A0HYM2"]),
    "BAA":         ("Yield corporativo Baa",               ["BAA"]),

    # Inflación esperada (breakeven)
    "BE_5Y":       ("Breakeven inflación 5Y",              ["T5YIE"]),
    "BE_10Y":      ("Breakeven inflación 10Y",             ["T10YIE"]),

    # Fortaleza USD alternativa
    "USD_BROAD":   ("Índice dólar amplio (trade-weighted)", ["DTWEXBGS"]),

    # Liquidez
    "M2":          ("M2 EUA",                              ["M2SL"]),

    # México
    "CPI_MX_YOY":  ("Inflación México (YoY)",             ["CPALTT01MXM659N"]),
    "MX_3M":       ("Tasa México 3M (proxy)",              ["IR3TIB01MXM156N"]),
    "MX_10Y":      ("Bono México 10Y (proxy)",             ["IRLTLT01MXM156N"]),
}

# Series de Yahoo Finance para macro
YAHOO_MACRO: Dict[str, Tuple[str, List[str]]] = {
    "DXY":     ("Fortaleza del dólar (Dollar Index DXY)",  ["DX-Y.NYB", "^DXY"]),
    "UUP":     ("ETF del dólar (UUP, proxy de USD)",       ["UUP"]),
    "USDMXN":  ("Tipo de cambio USD/MXN",                  ["MXN=X"]),
    "WTI":     ("Petróleo WTI (proxy)",                    ["CL=F", "USO"]),
    "GOLD":    ("Oro (ETF GLD)",                           ["GLD", "GC=F"]),
    "SILVER":  ("Plata (ETF SLV)",                         ["SLV", "SI=F"]),
    "VIX":     ("Volatilidad implícita (VIX)",             ["^VIX"]),
    "SPY":     ("S&P 500 (ETF SPY)",                       ["SPY", "^GSPC"]),
    "QQQ":     ("Nasdaq 100 (ETF QQQ)",                    ["QQQ", "^NDX"]),
    "TLT":     ("Bonos 20Y+ (ETF TLT)",                   ["TLT"]),
    "HYG":     ("ETF High Yield (HYG)",                    ["HYG"]),
    "LQD":     ("ETF Investment Grade (LQD)",              ["LQD"]),
}

# Sectores S&P
SECTOR_UNIVERSE: Dict[str, Tuple[str, List[str]]] = {
    "XLC":  ("Sector Comunicación",          ["XLC"]),
    "XLY":  ("Sector Consumo Discrecional",  ["XLY"]),
    "XLP":  ("Sector Consumo Básico",        ["XLP"]),
    "XLE":  ("Sector Energía",               ["XLE"]),
    "XLF":  ("Sector Financiero",            ["XLF"]),
    "XLV":  ("Sector Salud",                 ["XLV"]),
    "XLI":  ("Sector Industriales",          ["XLI"]),
    "XLB":  ("Sector Materiales",            ["XLB"]),
    "XLRE": ("Sector Bienes Raíces",         ["XLRE"]),
    "XLK":  ("Sector Tecnología",            ["XLK"]),
    "XLU":  ("Sector Utilities",             ["XLU"]),
}


def download_all_macro(
    start: str,
    end: str,
    fred_api_key: str = "",
) -> Dict[str, object]:
    """Descarga todas las series macro (FRED + Yahoo).

    Args:
        start: Fecha inicio 'YYYY-MM-DD'.
        end: Fecha fin 'YYYY-MM-DD'.
        fred_api_key: API key de FRED.

    Returns:
        Dict con:
          - 'fred_raw': DataFrame de series FRED
          - 'fred_chosen': {nombre: id_elegido}
          - 'fred_missing': [nombres faltantes]
          - 'yahoo_prices': DataFrame de precios Yahoo macro
          - 'yahoo_chosen': {nombre: ticker_elegido}
          - 'yahoo_missing': [nombres faltantes]
          - 'sector_prices': DataFrame de precios sectoriales
          - 'sector_chosen': {nombre: ticker}
          - 'sector_missing': [faltantes]
    """
    log.info("Descargando datos macro: FRED + Yahoo (%s → %s)", start, end)

    # FRED
    fred_raw, fred_chosen, fred_missing = fred_get_multiple(
        FRED_CANDIDATES, start, end, fred_api_key,
    )
    log.info("FRED: %d/%d series descargadas", len(fred_chosen) - len(fred_missing), len(FRED_CANDIDATES))

    # Yahoo macro
    yahoo_prices, yahoo_chosen, yahoo_missing = download_universe_with_fallbacks(
        YAHOO_MACRO, start, end, min_points=100,
    )
    log.info("Yahoo macro: %d/%d series", len(yahoo_chosen) - len(yahoo_missing), len(YAHOO_MACRO))

    # Sectores
    sector_prices, sector_chosen, sector_missing = download_universe_with_fallbacks(
        SECTOR_UNIVERSE, start, end, min_points=100,
    )
    log.info("Sectores: %d/%d descargados", len(sector_chosen) - len(sector_missing), len(SECTOR_UNIVERSE))

    return {
        "fred_raw": fred_raw,
        "fred_chosen": fred_chosen,
        "fred_missing": fred_missing,
        "yahoo_prices": yahoo_prices,
        "yahoo_chosen": yahoo_chosen,
        "yahoo_missing": yahoo_missing,
        "sector_prices": sector_prices,
        "sector_chosen": sector_chosen,
        "sector_missing": sector_missing,
    }


def build_macro_df(macro_result: dict, business_days: pd.DatetimeIndex) -> pd.DataFrame:
    """Construye un DataFrame macro unificado alineado a días hábiles.

    Combina FRED + Yahoo en un solo DataFrame con forward-fill
    para series de frecuencia menor (mensuales → diarias).

    Args:
        macro_result: Output de download_all_macro().
        business_days: Índice de fechas de días hábiles.

    Returns:
        DataFrame con una columna por serie y fechas como índice.
    """
    fred_raw = macro_result["fred_raw"]
    yahoo_prices = macro_result["yahoo_prices"]

    # Alinear FRED a días hábiles con forward-fill
    macro = fred_raw.reindex(business_days).ffill()

    # Agregar Yahoo (ya es diario)
    for col in yahoo_prices.columns:
        macro[col] = yahoo_prices[col].reindex(business_days).ffill()

    return macro


def compute_derived_macro(macro: pd.DataFrame) -> pd.DataFrame:
    """Calcula series macro derivadas: inflación YoY, curva de bonos, spreads.

    Args:
        macro: Output de build_macro_df().

    Returns:
        El mismo DataFrame con columnas derivadas añadidas.
    """

    def yoy_from_level(series, periods=252):
        """Inflación YoY de serie de nivel."""
        if series is None or series.dropna().empty:
            return pd.Series(dtype=float, index=macro.index)
        return (series / series.shift(periods) - 1) * 100

    # Inflación YoY EUA
    if "CPI_US" in macro.columns:
        macro["CPI_US_YOY"] = yoy_from_level(macro["CPI_US"])
    if "CORE_CPI_US" in macro.columns:
        macro["CORE_CPI_US_YOY"] = yoy_from_level(macro["CORE_CPI_US"])
    if "PCEPI" in macro.columns:
        macro["PCE_YOY"] = yoy_from_level(macro["PCEPI"])
    if "PCEPILFE" in macro.columns:
        macro["CORE_PCE_YOY"] = yoy_from_level(macro["PCEPILFE"])

    # Curva EUA
    if "UST_10Y" in macro.columns and "UST_2Y" in macro.columns:
        macro["YC_10Y_2Y"] = macro["UST_10Y"] - macro["UST_2Y"]
    if "UST_10Y" in macro.columns and "UST_3M" in macro.columns:
        macro["YC_10Y_3M"] = macro["UST_10Y"] - macro["UST_3M"]

    # Spread Baa - 10Y
    if "BAA" in macro.columns and "UST_10Y" in macro.columns:
        macro["BAA_10Y_SPREAD"] = macro["BAA"] - macro["UST_10Y"]

    # Curva México
    if "MX_10Y" in macro.columns and "MX_3M" in macro.columns:
        macro["MX_YC_10Y_3M"] = macro["MX_10Y"] - macro["MX_3M"]

    # MXNUSD (inverso del USDMXN)
    if "USDMXN" in macro.columns:
        macro["MXNUSD"] = 1.0 / macro["USDMXN"]

    # DXY fallback: si DXY tiene muchos NaN, usar USD_BROAD
    if "DXY" in macro.columns:
        dxy_valid = macro["DXY"].dropna().shape[0]
        if dxy_valid < 200 and "USD_BROAD" in macro.columns:
            usd_broad = macro["USD_BROAD"]
            if usd_broad.dropna().shape[0] > 50:
                macro["DXY"] = usd_broad
                log.info("DXY reemplazado por USD_BROAD como proxy de fortaleza USD.")

    return macro


def build_yield_curve(macro: pd.DataFrame) -> Optional[pd.DataFrame]:
    """Construye la curva de rendimientos UST en el tiempo.

    Args:
        macro: DataFrame macro con series de tasas.

    Returns:
        DataFrame con columnas [3M, 2Y, 5Y, 10Y, 30Y] y fechas como índice.
        None si no hay suficientes series.
    """
    tenor_map = {
        "3M": "UST_3M",
        "2Y": "UST_2Y",
        "5Y": "UST_5Y",
        "10Y": "UST_10Y",
        "30Y": "UST_30Y",
    }

    available = {label: macro[col] for label, col in tenor_map.items() if col in macro.columns}

    if len(available) < 3:
        log.warning("Curva de bonos: solo %d plazos disponibles (mínimo 3)", len(available))
        return None

    return pd.DataFrame(available)


def get_yield_curve_today(macro: pd.DataFrame) -> Dict[str, float]:
    """Curva de bonos del día más reciente.

    Args:
        macro: DataFrame macro con series de tasas.

    Returns:
        Dict {plazo: tasa}.
    """
    curve = build_yield_curve(macro)
    if curve is None:
        return {}

    last_row = curve.dropna(how="all").iloc[-1] if not curve.dropna(how="all").empty else pd.Series()
    return {k: float(v) for k, v in last_row.items() if pd.notna(v)}


def get_macro_summary(macro: pd.DataFrame) -> Dict[str, Optional[float]]:
    """Resumen de indicadores macro actuales (última lectura válida).

    Args:
        macro: DataFrame macro.

    Returns:
        Dict {nombre_indicador: valor_actual_o_None}.
    """
    key_indicators = [
        "EFFR", "UST_2Y", "UST_10Y", "UST_3M",
        "YC_10Y_2Y", "YC_10Y_3M",
        "CPI_US_YOY", "CORE_CPI_US_YOY", "PCE_YOY", "CORE_PCE_YOY",
        "UNRATE_US", "ICSA",
        "NFCI", "HY_SPREAD", "BAA_10Y_SPREAD",
        "BE_5Y", "BE_10Y",
        "DXY", "USDMXN", "WTI", "GOLD", "SILVER", "VIX",
        "CPI_MX_YOY", "MX_3M", "MX_10Y", "MX_YC_10Y_3M",
    ]

    summary = {}
    for k in key_indicators:
        if k in macro.columns:
            s = macro[k].dropna()
            summary[k] = float(s.iloc[-1]) if not s.empty else None
        else:
            summary[k] = None

    return summary
