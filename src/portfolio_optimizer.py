# -*- coding: utf-8 -*-
"""
src/portfolio_optimizer.py — Optimización de portafolio

Implementa la construcción del portafolio óptimo:
  - Max Sharpe con cap de varianza (riesgo controlado)
  - Restricciones de pesos fijos por ticker (desde config)
  - Rebalanceo: calcula cantidades enteras dentro de budget
  - Memoria de portafolios anteriores (JSON)

Sin input() — todos los parámetros desde config.yml:
  portfolio.years_history, risk_multiplier, budget_min/max,
  na_threshold, lambda_adj, fixed_weights

Origen: rescatado de umpa_ultra_mejorado_2_0_15_01_2026.py
        (max_sharpe_with_sigma_cap, align_mu_sigma, portfolio DB
         líneas 1011-1038, 1757-1791)

Estado: STUB — implementación completa en Fase 3/4
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


def build_cov_matrix(
    returns: pd.DataFrame,
    ridge_lambda: float = 1e-4,
) -> pd.DataFrame:
    """Construye matriz de covarianza robusta con regularización ridge.

    La regularización evita matrices singulares cuando hay tickers
    con historial corto o muy correlacionados.

    Args:
        returns: DataFrame de retornos periódicos (fechas × tickers).
        ridge_lambda: Parámetro de regularización (default 1e-4).

    Returns:
        DataFrame de covarianza anualizada (N×N).

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar covarianza robusta")


def align_mu_sigma(
    dcf_df: pd.DataFrame,
    cov_ann: pd.DataFrame,
    tickers: List[str],
    lambda_adj: float = 0.40,
    mu_col: str = "MU_ADJ",
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Alinea vector de retornos esperados con la matriz de covarianza.

    El retorno esperado ajustado (MU_ADJ) combina:
      - Señal DCF (upside de valuación)
      - Retorno histórico implícito
      Con peso lambda_adj en la señal DCF.

    Args:
        dcf_df: DataFrame de resultados DCF (debe tener columna mu_col).
        cov_ann: Matriz de covarianza anualizada.
        tickers: Lista de tickers en el mismo orden que cov_ann.
        lambda_adj: Peso de la señal DCF (0-1).
        mu_col: Nombre de la columna de retorno esperado en dcf_df.

    Returns:
        Tupla (mu_array, sigma_matrix, tickers_validos).

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar align_mu_sigma")


def max_sharpe(
    mu: np.ndarray,
    sigma: np.ndarray,
    rf: float,
    sigma_cap: float,
    bounds: Optional[list] = None,
) -> np.ndarray:
    """Optimización Max Sharpe con cap de varianza de portafolio.

    Maximiza: (mu - rf) / sqrt(w' Σ w)
    Sujeto a: w' Σ w ≤ sigma_cap², sum(w) = 1, w ≥ 0

    El sigma_cap se expresa como múltiplo de la volatilidad de SPY:
      sigma_cap = risk_multiplier × vol_SPY

    Args:
        mu: Vector de retornos esperados (N,).
        sigma: Matriz de covarianza (N×N).
        rf: Tasa libre de riesgo.
        sigma_cap: Cap de varianza del portafolio.
        bounds: Lista de (min, max) por activo. None = (0, 1) para todos.

    Returns:
        Array de pesos óptimos (N,).

    TODO (Fase 3): Implementar rescatando max_sharpe_with_sigma_cap.
    """
    raise NotImplementedError("Fase 3: implementar Max Sharpe")


def compute_quantities(
    weights: np.ndarray,
    tickers: List[str],
    prices: Dict[str, float],
    budget_min: float,
    budget_max: float,
    base_currency: str = "USD",
) -> pd.DataFrame:
    """Calcula cantidades enteras de cada activo dado un presupuesto.

    Args:
        weights: Array de pesos del portafolio.
        tickers: Lista de tickers en el mismo orden que weights.
        prices: Dict {ticker: precio_en_moneda_base}.
        budget_min: Inversión mínima.
        budget_max: Inversión máxima.
        base_currency: Moneda base.

    Returns:
        DataFrame con columnas: ticker, peso, precio, cantidad, valor_total, %.

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar cálculo de cantidades")


# ─────────────────────────────────────────────
# Base de datos de portafolios (JSON)
# ─────────────────────────────────────────────

def save_portfolio(
    name: str,
    tickers: List[str],
    weights: Dict[str, float],
    quantities: Dict[str, int],
    base_currency: str,
    db_path: str = "outputs/portfolios_memory.json",
) -> None:
    """Guarda un portafolio en la base de datos JSON local.

    Args:
        name: Nombre del portafolio (ej. 'portafolio_2024_q1').
        tickers: Lista de tickers.
        weights: Dict {ticker: peso}.
        quantities: Dict {ticker: cantidad}.
        base_currency: Moneda base.
        db_path: Ruta al archivo JSON.

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar save_portfolio")


def list_portfolios(
    db_path: str = "outputs/portfolios_memory.json",
) -> pd.DataFrame:
    """Lista todos los portafolios guardados.

    Args:
        db_path: Ruta al archivo JSON.

    Returns:
        DataFrame con metadata de portafolios guardados.

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar list_portfolios")
