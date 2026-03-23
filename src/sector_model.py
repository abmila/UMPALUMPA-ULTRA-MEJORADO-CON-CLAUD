# -*- coding: utf-8 -*-
"""
src/sector_model.py — Modelos de señales de mercado y sectores

Implementa los modelos basados en machine learning para generar
señales de dirección por activo, sector y mercado general:
  - k-NN: días históricos similares (vecinos más cercanos)
  - Regresión logística: probabilidad de subida por horizonte
  - Señales por sector basadas en régimen macro

Origen: rescatado de que_va_a_pasar_en_el_mercado_.py
        (train_predict_with_explain, bloque kNN — líneas 513-640)

Estado: STUB — implementación completa en Fase 4
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def find_knn_neighbors(
    features_today: pd.Series,
    features_history: pd.DataFrame,
    n_neighbors: int = 150,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Encuentra los N días históricos más similares al día actual.

    Usa distancia euclidiana en el espacio de features normalizadas.
    Los features deben ser los mismos que build_macro_features() produce.

    Args:
        features_today: Vector de features del día actual.
        features_history: DataFrame histórico de features (fechas × features).
        n_neighbors: Número de vecinos a encontrar.

    Returns:
        Tupla (neighbors_df, distances):
          - neighbors_df: Subconjunto del histórico con las N fechas más similares.
          - distances: Serie con la distancia de cada vecino.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar kNN neighbors")


def knn_forward_returns(
    neighbors_df: pd.DataFrame,
    prices: pd.DataFrame,
    tickers: List[str],
    horizons_bdays: List[int],
) -> Dict[str, Dict[int, float]]:
    """Calcula retornos futuros promedio de los vecinos históricos.

    Para cada vecino encontrado por kNN, mira cuánto subió/bajó cada activo
    en los días siguientes. Promedia esos retornos.

    Args:
        neighbors_df: Output de find_knn_neighbors().
        prices: DataFrame histórico de precios.
        tickers: Lista de tickers a analizar.
        horizons_bdays: Lista de horizontes en días hábiles.

    Returns:
        Dict {ticker: {horizonte_dias: prob_subida}} donde prob_subida
        es la fracción de vecinos donde el activo subió.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar kNN forward returns")


def train_logistic_models(
    features: pd.DataFrame,
    forward_returns: pd.DataFrame,
    tickers: List[str],
    horizons_bdays: List[int],
    min_train_samples: int = 900,
) -> dict:
    """Entrena modelos de regresión logística para predecir dirección.

    Un modelo por (ticker, horizonte). Usa pipeline: StandardScaler + LogisticRegression.
    Solo entrena si hay suficientes muestras (min_train_samples).

    Args:
        features: DataFrame de features macro.
        forward_returns: Output de build_forward_returns().
        tickers: Lista de tickers.
        horizons_bdays: Lista de horizontes.
        min_train_samples: Mínimo de observaciones para entrenar.

    Returns:
        Dict {(ticker, horizonte): modelo_entrenado}.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar modelos logísticos")


def predict_probabilities(
    models: dict,
    features_today: pd.Series,
    tickers: List[str],
    horizons_bdays: List[int],
) -> pd.DataFrame:
    """Genera probabilidades de subida para cada activo y horizonte.

    Args:
        models: Output de train_logistic_models().
        features_today: Vector de features del día actual.
        tickers: Lista de tickers.
        horizons_bdays: Lista de horizontes.

    Returns:
        DataFrame con tickers como índice y horizontes como columnas.
        Valores: P(subida) entre 0 y 1. NaN si el modelo no existe.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar predicciones")


def get_sector_signals(
    probs: pd.DataFrame,
    sector_map: Dict[str, str],
) -> pd.DataFrame:
    """Agrega probabilidades de activos individuales a nivel sector.

    Args:
        probs: Output de predict_probabilities().
        sector_map: Dict {ticker: sector_etf} (ej. {'AAPL': 'XLK'}).

    Returns:
        DataFrame con sectores como índice y horizontes como columnas.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar señales sectoriales")
