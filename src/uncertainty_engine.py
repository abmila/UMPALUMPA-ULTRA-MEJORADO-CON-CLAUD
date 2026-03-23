# -*- coding: utf-8 -*-
"""
src/uncertainty_engine.py — Cuantificación de incertidumbre

Cuantifica cuánta incertidumbre existe en el análisis para:
  - Cada activo individual
  - Cada sector
  - El mercado general

Combina múltiples fuentes de incertidumbre:
  1. Volatilidad histórica del activo
  2. Dispersión de retornos de vecinos históricos (kNN)
  3. Dispersión entre escenarios bear/base/bull del DCF
  4. Contradicción entre señales (kNN dice subir, logística dice bajar)
  5. Proxy de estrés de mercado (VIX, spreads de crédito)
  6. Completitud de datos (más datos faltantes = más incertidumbre)

Estado: STUB — implementación completa en Fase 4
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def compute_volatility_score(
    returns: pd.Series,
    benchmark_vol: Optional[float] = None,
) -> float:
    """Score de incertidumbre basado en volatilidad histórica (0-1).

    Score de 0 = muy estable, 1 = extremadamente volátil.

    Args:
        returns: Serie de retornos diarios del activo.
        benchmark_vol: Volatilidad de referencia (ej. SPY). Si se provee,
                       normaliza el score relativo al mercado.

    Returns:
        Score entre 0 y 1.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar volatility score")


def compute_knn_dispersion(
    knn_returns: List[float],
) -> float:
    """Score de incertidumbre basado en dispersión de retornos de vecinos kNN.

    Alta dispersión = los días similares tuvieron resultados muy variados.
    Baja dispersión = los días similares tuvieron resultados consistentes.

    Args:
        knn_returns: Lista de retornos futuros de los vecinos históricos.

    Returns:
        Score entre 0 y 1 (desviación estándar normalizada).

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar kNN dispersion score")


def compute_dcf_dispersion(
    intrinsic_bear: float,
    intrinsic_base: float,
    intrinsic_bull: float,
) -> float:
    """Score de incertidumbre basado en dispersión de escenarios DCF.

    Rango amplio bear-bull = mayor incertidumbre fundamental.

    Args:
        intrinsic_bear: Valor intrínseco escenario pesimista.
        intrinsic_base: Valor intrínseco escenario base.
        intrinsic_bull: Valor intrínseco escenario optimista.

    Returns:
        Score entre 0 y 1.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar DCF dispersion score")


def compute_signal_contradiction(
    knn_prob: float,
    logistic_prob: float,
) -> float:
    """Score de contradicción entre señales kNN y logística.

    Alta contradicción = los modelos no están de acuerdo = más incertidumbre.

    Args:
        knn_prob: P(subida) según kNN.
        logistic_prob: P(subida) según regresión logística.

    Returns:
        Score entre 0 y 1. 0 = acuerdo total, 1 = contradicción total.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar signal contradiction score")


def compute_market_stress(
    macro_data: Dict[str, pd.Series],
) -> float:
    """Score de estrés de mercado actual basado en indicadores macro.

    Usa: VIX, HY spread, IG spread, condiciones financieras Chicago Fed.

    Args:
        macro_data: Output de macro_data.download_all_macro().

    Returns:
        Score entre 0 y 1. 0 = condiciones normales, 1 = estrés extremo.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar market stress score")


def compute_data_quality_penalty(data_flags: List[str]) -> float:
    """Penalización de incertidumbre por datos faltantes o de baja calidad.

    Args:
        data_flags: Lista de flags DATA_GAPS del módulo de valuación.

    Returns:
        Score entre 0 y 0.3 (máximo 30% de incertidumbre extra por datos).

    TODO (Fase 4): Implementar.
    """
    if not data_flags:
        return 0.0
    raise NotImplementedError("Fase 4: implementar data quality penalty")


def compute_uncertainty_score(
    ticker: str,
    returns: Optional[pd.Series] = None,
    knn_returns: Optional[List[float]] = None,
    dcf_scenarios: Optional[Tuple[float, float, float]] = None,
    knn_prob: Optional[float] = None,
    logistic_prob: Optional[float] = None,
    macro_data: Optional[Dict] = None,
    data_flags: Optional[List[str]] = None,
) -> Dict[str, float]:
    """Calcula el score de incertidumbre compuesto para un activo.

    Combina todas las fuentes disponibles con pesos:
      - 30%: Volatilidad histórica
      - 20%: Dispersión kNN
      - 20%: Dispersión DCF
      - 15%: Contradicción señales
      - 10%: Estrés de mercado
      - 5%: Calidad de datos

    Args:
        ticker: Símbolo del activo.
        [Resto de args]: Cada fuente de incertidumbre (todas opcionales).
          Si alguna no está disponible, se usa el promedio de las demás.

    Returns:
        Dict con:
          - 'score': Score total 0-100 (0=certeza, 100=máxima incertidumbre)
          - 'nivel': 'BAJO', 'MODERADO', 'ALTO', 'MUY_ALTO'
          - 'componentes': Dict con score de cada componente
          - 'interpretacion': String explicativo en español

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar uncertainty score")
