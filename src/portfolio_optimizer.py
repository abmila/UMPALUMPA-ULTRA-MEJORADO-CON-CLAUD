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
        (líneas 1011-1038, 1757-1791)
"""

import json
import logging
import pathlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

from src.config_loader import CFG

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
    """
    # Calcula covarianza muestral
    cov = returns.cov().values
    n = cov.shape[0]

    # Añade regularización ridge
    cov_ridge = cov + ridge_lambda * np.eye(n)

    # Asegura PSD (positivo semi-definido)
    try:
        np.linalg.cholesky(cov_ridge)
    except np.linalg.LinAlgError:
        # Si aún no es PSD, añade más regularización
        eigvals = np.linalg.eigvalsh(cov)
        min_eigval = eigvals[0]
        if min_eigval < 0:
            cov_ridge = cov + (-min_eigval + 1e-6) * np.eye(n)

    # Anualiza si es necesario
    # (asumiendo que returns es con frecuencia de trading típica)
    periods_per_year = 252 if "daily" in str(returns.index).lower() else 52 if "weekly" in str(returns.index).lower() else 12
    cov_ann = cov_ridge * periods_per_year

    return pd.DataFrame(cov_ann, index=returns.columns, columns=returns.columns)


def align_mu_sigma(
    dcf_df: pd.DataFrame,
    cov_ann: pd.DataFrame,
    tickers: List[str],
    lambda_adj: float = 0.40,
    mu_col: str = "upside_base",
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
    """
    # Indexa por ticker
    dcf_indexed = dcf_df.set_index("ticker") if "ticker" in dcf_df.columns else dcf_df.copy()

    # Filtra solo tickers con datos válidos en mu_col
    valid_mask = np.isfinite(dcf_indexed[mu_col])
    valid_dcf = dcf_indexed[valid_mask].copy()

    # Encuentra intersección con covarianza
    inter = [t for t in tickers if t in valid_dcf.index and t in cov_ann.index]

    if len(inter) < 2:
        raise RuntimeError(
            f"No hay suficientes tickers comunes entre valuación y covarianza. "
            f"Encontrados: {len(inter)}. Necesarios: >= 2"
        )

    # Extrae datos en el orden de inter
    mu_dcf = valid_dcf.loc[inter, mu_col].values.astype(float)

    # Retorno histórico implícito: media de retornos históricos
    # (si disponible; sino, usar rf + 2% como fallback)
    mu_hist = np.full_like(mu_dcf, 0.06)  # Fallback: 6% anual
    for i, ticker in enumerate(inter):
        try:
            hist = yf.download(ticker, period="1y", interval="1d", progress=False)["Close"]
            if len(hist) > 10:
                ret = hist.pct_change().dropna()
                annual_return = ((1 + ret.mean()) ** 252) - 1
                mu_hist[i] = float(annual_return) if np.isfinite(annual_return) else 0.06
        except Exception:
            pass

    # Combina señales
    mu = lambda_adj * mu_dcf + (1 - lambda_adj) * mu_hist

    # Extrae submatriz de covarianza
    Sigma = cov_ann.loc[inter, inter].values

    # Asegura que Sigma es PSD
    try:
        np.linalg.cholesky(Sigma)
    except np.linalg.LinAlgError:
        Sigma = Sigma + np.eye(Sigma.shape[0]) * 1e-8

    return mu, Sigma, inter


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
    """
    n = len(mu)
    bounds = bounds or [(0.0, 1.0)] * n

    # Restricciones: sum(w) = 1 y varianza cap
    cons = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
    if sigma_cap and sigma_cap > 0:
        cons.append({'type': 'ineq', 'fun': lambda w: sigma_cap**2 - (w @ sigma @ w)})

    # Punto inicial: media ponderada
    w0 = np.array([(low + high) / 2 for (low, high) in bounds], dtype=float)

    # Función objetivo: -Sharpe (negativo para minimizar)
    def neg_sharpe(w):
        ret = float(w @ mu)
        vol = float(np.sqrt(w @ sigma @ w))
        if vol > 1e-8:
            return -((ret - rf) / vol)
        else:
            return 1e9

    # Optimiza
    res = minimize(
        neg_sharpe,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=cons,
        options=dict(maxiter=600, ftol=1e-9)
    )

    # Normaliza resultado
    w = np.clip(res.x if res.success else w0, 0, 1)
    s = w.sum()
    return w / s if s > 0 else np.ones(n) / n


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
    """
    rows = []

    # Intenta usar el presupuesto máximo primero
    budget = budget_max
    total_invested = 0.0

    for ticker, weight in zip(tickers, weights):
        if weight < 1e-6:
            rows.append({
                "ticker": ticker,
                "weight": weight,
                "price": prices.get(ticker, np.nan),
                "quantity": 0,
                "value_total": 0.0,
                "percent_budget": 0.0,
            })
            continue

        try:
            price = float(prices.get(ticker, np.nan))
            if np.isnan(price) or price <= 0:
                log.warning(f"Precio inválido para {ticker}: {price}")
                rows.append({
                    "ticker": ticker,
                    "weight": weight,
                    "price": np.nan,
                    "quantity": 0,
                    "value_total": 0.0,
                    "percent_budget": 0.0,
                })
                continue

            # Cantidad target
            target_value = budget * weight
            quantity = int(np.floor(target_value / price))

            # Asegura al menos 1 share si weight > 0
            if quantity == 0 and weight > 0 and target_value >= price:
                quantity = 1

            value = float(quantity * price)
            total_invested += value

            pct_budget = (value / budget * 100) if budget > 0 else 0.0

            rows.append({
                "ticker": ticker,
                "weight": weight,
                "price": price,
                "quantity": quantity,
                "value_total": value,
                "percent_budget": pct_budget,
            })

        except Exception as e:
            log.error(f"Error calculando cantidades para {ticker}: {e}")
            rows.append({
                "ticker": ticker,
                "weight": weight,
                "price": np.nan,
                "quantity": 0,
                "value_total": 0.0,
                "percent_budget": 0.0,
            })

    # Valida que esté dentro de presupuesto
    if total_invested < budget_min:
        log.warning(f"Inversión total {total_invested} < budget_min {budget_min}")
    if total_invested > budget_max:
        log.warning(f"Inversión total {total_invested} > budget_max {budget_max}")

    df = pd.DataFrame(rows)
    if not df.empty:
        df["total_portfolio_value"] = df["value_total"].sum()

    return df


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
    """
    db_path = pathlib.Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Carga portafolios existentes
    portfolios = {}
    if db_path.exists():
        try:
            portfolios = json.loads(db_path.read_text(encoding="utf-8"))
        except Exception as e:
            log.warning(f"Error leyendo {db_path}: {e}. Se crea nuevo.")

    # Añade nuevo portafolio
    portfolio_data = {
        "name": name,
        "created_at": datetime.now().isoformat(),
        "tickers": tickers,
        "weights": weights,
        "quantities": quantities,
        "base_currency": base_currency,
    }

    portfolios[name] = portfolio_data

    # Guarda
    try:
        db_path.write_text(
            json.dumps(portfolios, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        log.info(f"Portafolio '{name}' guardado en {db_path}")
    except Exception as e:
        log.error(f"Error guardando portafolio: {e}")


def list_portfolios(
    db_path: str = "outputs/portfolios_memory.json",
) -> pd.DataFrame:
    """Lista todos los portafolios guardados.

    Args:
        db_path: Ruta al archivo JSON.

    Returns:
        DataFrame con metadata de portafolios guardados.
    """
    db_path = pathlib.Path(db_path)

    if not db_path.exists():
        log.info(f"No hay portafolios guardados en {db_path}")
        return pd.DataFrame()

    try:
        portfolios = json.loads(db_path.read_text(encoding="utf-8"))

        rows = []
        for name, data in portfolios.items():
            rows.append({
                "portfolio_name": name,
                "created_at": data.get("created_at", ""),
                "num_tickers": len(data.get("tickers", [])),
                "base_currency": data.get("base_currency", "USD"),
                "tickers": ",".join(data.get("tickers", [])),
            })

        return pd.DataFrame(rows)

    except Exception as e:
        log.error(f"Error listando portafolios: {e}")
        return pd.DataFrame()
