# -*- coding: utf-8 -*-
"""
src/scoring_engine.py — Motor de scoring y ranking de activos

Combina todas las señales del sistema en un score final por activo:
  - Score fundamental: upside DCF + salud financiera
  - Score de mercado: señales kNN + logística por horizonte
  - Score de régimen: alineación con el entorno macro actual
  - Score de riesgo/incertidumbre (inverso)

Produce el ranking final de activos por:
  - Atractivo general
  - Convicción (señales consistentes, baja incertidumbre)
  - Riesgo (fragilidad financiera + incertidumbre)

Estado: STUB — implementación completa en Fase 4
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Pesos para el score compuesto (deben sumar 1.0)
SCORE_WEIGHTS = {
    "fundamental": 0.35,   # Valuación DCF + salud financiera
    "momentum_macro": 0.30, # Señales kNN + logística
    "regime_fit": 0.15,    # Alineación con régimen macro
    "uncertainty_inv": 0.20, # Inverso de incertidumbre (certeza = bueno)
}


def compute_fundamental_score(
    dcf_result: dict,
    health_result: dict,
) -> float:
    """Score fundamental basado en valuación + salud financiera (0-100).

    Combina:
      - Upside del DCF base (mayor upside = mejor)
      - Health score (mayor salud = mejor)
      - Penalización por flags de riesgo

    Args:
        dcf_result: Output de valuation_dcf.dcf_valuation().
        health_result: Output de financial_health.compute_ratios().

    Returns:
        Score entre 0 y 100.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar fundamental score")


def compute_market_score(
    probs: Dict[int, float],
    horizon_weights: Optional[Dict[int, float]] = None,
) -> float:
    """Score de mercado basado en probabilidades de subida (0-100).

    Promedia probabilidades ponderadas por horizonte.
    Horizontes más cortos tienen más peso por defecto.

    Args:
        probs: Dict {horizonte_dias: P(subida)}.
        horizon_weights: Pesos por horizonte. None = equitativo.

    Returns:
        Score entre 0 y 100. 50 = neutral, >50 = señal alcista.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar market score")


def compute_regime_fit_score(
    ticker: str,
    sector: str,
    favored_sectors: List[str],
    pressured_sectors: List[str],
) -> float:
    """Score de alineación entre el activo y el régimen macro (0-100).

    Activos en sectores favorecidos por el régimen reciben score alto.
    Activos en sectores presionados reciben score bajo.

    Args:
        ticker: Símbolo.
        sector: Sector ETF del activo (ej. 'XLK').
        favored_sectors: Sectores favorecidos por el régimen.
        pressured_sectors: Sectores presionados por el régimen.

    Returns:
        Score entre 0 y 100.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar regime fit score")


def compute_composite_score(
    fundamental_score: float,
    market_score: float,
    regime_fit_score: float,
    uncertainty_score: float,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """Score compuesto final combinando todas las dimensiones.

    Args:
        fundamental_score: Output de compute_fundamental_score().
        market_score: Output de compute_market_score().
        regime_fit_score: Output de compute_regime_fit_score().
        uncertainty_score: Score de incertidumbre (0-100).
        weights: Pesos por dimensión. None = usa SCORE_WEIGHTS default.

    Returns:
        Dict con:
          - 'score_total': Score compuesto 0-100
          - 'atractivo': 'MUY_ALTO', 'ALTO', 'MODERADO', 'BAJO', 'MUY_BAJO'
          - 'conviccion': 'ALTA', 'MEDIA', 'BAJA' (basado en consistencia señales)
          - 'componentes': Dict de scores individuales
          - 'interpretacion': String explicativo en español

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar composite score")


def rank_universe(
    scores: Dict[str, Dict[str, float]],
    sort_by: str = "score_total",
    ascending: bool = False,
) -> pd.DataFrame:
    """Genera el ranking final de activos del universo.

    Args:
        scores: Dict {ticker: output_de_compute_composite_score}.
        sort_by: Columna por la cual ordenar.
        ascending: True = menor primero, False = mayor primero.

    Returns:
        DataFrame con el ranking completo, una fila por activo.
        Columnas: ticker, score_total, atractivo, conviccion, upside_dcf,
                  health_score, market_score, uncertainty, sector, ...

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar ranking")
