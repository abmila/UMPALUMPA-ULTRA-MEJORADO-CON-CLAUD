# -*- coding: utf-8 -*-
"""
src/macro_data.py — Datos macroeconómicos

Descarga y estructura datos macro de EUA y México:
  - Tasas de interés (Fed Funds, UST 2Y/5Y/10Y/30Y, CETES, TIIE)
  - Inflación (CPI EUA, INPC México)
  - Curva de bonos y spreads de crédito
  - Commodities (WTI, oro, plata)
  - Tipo de cambio (USD/MXN, DXY)
  - Condiciones financieras

Origen: rescatado de que_va_a_pasar_en_el_mercado_.py
        (bloque de descarga FRED + Yahoo, FEATURES_FRED, FEATURES_YF
         líneas 226-416)

Estado: STUB — implementación completa en Fase 2
"""

import logging
from typing import Dict, Optional

import pandas as pd

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Catálogo de series FRED relevantes
# ─────────────────────────────────────────────

FRED_SERIES: Dict[str, list] = {
    # Tasas EUA
    "EFFR":      ["EFFR", "DFF"],           # Fed Funds efectiva
    "UST_2Y":    ["DGS2"],                  # UST 2 años
    "UST_5Y":    ["DGS5"],                  # UST 5 años
    "UST_10Y":   ["DGS10"],                 # UST 10 años (Rf principal)
    "UST_30Y":   ["DGS30"],                 # UST 30 años
    "UST_3M":    ["DTB3", "DGS3MO"],        # UST 3 meses
    # Spreads de crédito
    "HY_SPREAD": ["BAMLH0A0HYM2EY"],        # High Yield OAS
    "IG_SPREAD": ["BAMLC0A0CMEY"],          # Investment Grade OAS
    # Inflación EUA
    "CPI_YOY":   ["CPIAUCSL"],              # CPI nivel (calcular YoY)
    "PCE_YOY":   ["PCEPI"],                 # PCE (preferido por la Fed)
    "INFL_EXPEC":["MICH"],                  # Expectativas de inflación Michigan
    # Mercado laboral
    "UNRATE":    ["UNRATE"],                # Desempleo EUA
    # Tasas México (FRED tiene algunas)
    "MX_CETES":  ["INTDSRMXM193N"],         # CETES 28 días (mensual)
    # Condiciones financieras
    "FCI_CHI":   ["NFCI"],                  # Chicago Fed National Financial Conditions
}

# Series de Yahoo Finance para macro
YAHOO_MACRO: Dict[str, list] = {
    "DXY":       ["DX-Y.NYB", "^DXY"],      # Índice Dólar
    "USDMXN":    ["MXN=X"],                 # USD/MXN
    "WTI":       ["CL=F", "USO"],           # Petróleo WTI
    "GOLD":      ["GC=F", "GLD"],           # Oro
    "SILVER":    ["SI=F", "SLV"],           # Plata
    "VIX":       ["^VIX"],                  # Volatilidad implícita
    "SPY":       ["SPY", "^GSPC"],          # S&P 500
    "TLT":       ["TLT"],                   # Bonos 20Y+ (proxy duración)
    "HYG":       ["HYG"],                   # ETF High Yield
    "LQD":       ["LQD"],                   # ETF Investment Grade
}


def download_all_macro(
    start: str,
    end: str,
    fred_api_key: str = "",
) -> Dict[str, pd.Series]:
    """Descarga todas las series macro configuradas (FRED + Yahoo).

    Las series que fallan se omiten con warning, no rompen el flujo.

    Args:
        start: Fecha inicio 'YYYY-MM-DD'.
        end: Fecha fin 'YYYY-MM-DD'.
        fred_api_key: API key de FRED (opcional).

    Returns:
        Dict {nombre_interno: pd.Series} con las series descargadas.
        Las series faltantes NO están en el dict.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar descarga macro completa")


def build_yield_curve(macro_data: Dict[str, pd.Series]) -> Optional[pd.DataFrame]:
    """Construye la curva de rendimientos UST en el tiempo.

    Args:
        macro_data: Output de download_all_macro().

    Returns:
        DataFrame con columnas [3M, 2Y, 5Y, 10Y, 30Y] y fechas como índice.
        None si no hay suficientes series.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar curva de bonos")


def get_yield_curve_today(macro_data: Dict[str, pd.Series]) -> Dict[str, float]:
    """Devuelve la curva de bonos del día más reciente.

    Args:
        macro_data: Output de download_all_macro().

    Returns:
        Dict {plazo: tasa} donde plazo es '3M', '2Y', '5Y', '10Y', '30Y'.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar curva actual")


def get_spread_2y10y(macro_data: Dict[str, pd.Series]) -> Optional[pd.Series]:
    """Calcula el spread 10Y - 2Y (indicador de curva normal/invertida).

    Spread positivo = curva normal. Negativo = curva invertida (señal recesiva).

    Args:
        macro_data: Output de download_all_macro().

    Returns:
        pd.Series con el spread en puntos básicos, o None si faltan datos.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar spread 2y10y")
