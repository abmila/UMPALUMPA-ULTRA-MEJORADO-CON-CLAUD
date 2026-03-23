# -*- coding: utf-8 -*-
"""
src/feature_engineering.py — Ingeniería de features macro y técnicos

Construye las variables/features usadas como inputs para los modelos
de señales de mercado (kNN, regresión logística, régimen macro).

Origen: rescatado de que_va_a_pasar_en_el_mercado_.py
        (yoy_from_level, delta, bloque de construcción de features
         FEATURES_FRED + FEATURES_YF — líneas 277-416)

Estado: STUB — implementación completa en Fase 2
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def yoy_change(level_series: pd.Series, periods: int = 252) -> pd.Series:
    """Calcula cambio año-contra-año (YoY) de una serie de nivel.

    Útil para convertir CPI, PCE, etc. en tasas de inflación YoY.

    Args:
        level_series: Serie en niveles (ej. índice CPI).
        periods: Periodos para el cálculo YoY (default 252 = días hábiles/año).

    Returns:
        pd.Series con cambio porcentual YoY.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar yoy_change")


def rolling_delta(series: pd.Series, window: int = 21) -> pd.Series:
    """Calcula el cambio de una serie en una ventana de N periodos.

    Útil para capturar cambios recientes en tasas, spreads, etc.
    Ej: delta(EFFR, 21) = cambio del Fed Funds en el último mes.

    Args:
        series: Serie numérica.
        window: Ventana en periodos.

    Returns:
        pd.Series con el delta.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar rolling_delta")


def build_macro_features(
    macro_data: Dict[str, pd.Series],
    focus_start: str,
) -> pd.DataFrame:
    """Construye el DataFrame de features macro para los modelos.

    Features incluidas:
      - Niveles y deltas de tasas (EFFR, 2Y, 10Y, 30Y)
      - Spreads de crédito HY e IG
      - YoY de inflación (CPI, PCE)
      - Spread 2Y-10Y (curva)
      - Retornos de commodities y FX (1M)
      - Retornos de activos macro (TLT, HYG, LQD)
      - VIX nivel y cambio

    Args:
        macro_data: Output de macro_data.download_all_macro().
        focus_start: Fecha de inicio del periodo de análisis 'YYYY-MM-DD'.

    Returns:
        DataFrame con fechas como índice y features como columnas.
        Valores NaN donde no hay datos disponibles.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar build_macro_features")


def build_forward_returns(
    prices: pd.DataFrame,
    horizons_bdays: List[int],
) -> pd.DataFrame:
    """Calcula retornos futuros para múltiples horizontes (labels para modelos).

    Args:
        prices: DataFrame de precios históricos.
        horizons_bdays: Lista de horizontes en días hábiles (ej. [5, 10, 15, 30]).

    Returns:
        DataFrame con columnas tipo 'TICKER_Xd_fwd' y retornos futuros.

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar forward returns")
