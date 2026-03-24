# -*- coding: utf-8 -*-
"""
src/feature_engineering.py — Ingeniería de features macro y técnicos

Construye features usados como inputs para los modelos de señales
de mercado (kNN, regresión logística, régimen macro).

Rescatado de que_va_a_pasar_en_el_mercado_.py líneas 277-372.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Mapeo: columna macro → nombre legible en español
FEATURE_NICE_NAMES: Dict[str, str] = {
    "EFFR":           "Tasa EUA (EFFR)",
    "UST_2Y":         "Yield EUA 2 años",
    "UST_5Y":         "Yield EUA 5 años",
    "UST_10Y":        "Yield EUA 10 años",
    "UST_3M":         "Yield EUA 3 meses",
    "YC_10Y_2Y":      "Curva EUA 10Y-2Y",
    "YC_10Y_3M":      "Curva EUA 10Y-3M",
    "CPI_US_YOY":     "Inflación EUA (CPI YoY)",
    "CORE_CPI_US_YOY":"Inflación subyacente EUA (Core CPI YoY)",
    "PCE_YOY":        "Inflación EUA (PCE YoY)",
    "CORE_PCE_YOY":   "Inflación subyacente EUA (Core PCE YoY)",
    "UNRATE_US":      "Desempleo EUA",
    "ICSA":           "Claims semanales EUA",
    "INDPRO_US":      "Producción industrial EUA",
    "RETAIL_US":      "Ventas minoristas EUA",
    "PCE_REAL":       "Consumo real EUA (PCE real)",
    "SENT_US":        "Sentimiento consumidor EUA",
    "ISM_PMI":        "ISM PMI EUA",
    "HOUST":          "Housing starts EUA",
    "PERMIT":         "Building permits EUA",
    "NFCI":           "Condiciones financieras (NFCI)",
    "HY_SPREAD":      "Spread High Yield (OAS)",
    "BAA_10Y_SPREAD": "Spread Baa - 10Y EUA",
    "BE_5Y":          "Breakeven inflación 5Y",
    "BE_10Y":         "Breakeven inflación 10Y",
    "M2":             "M2 EUA",
    "CPI_MX_YOY":     "Inflación México (YoY)",
    "MX_3M":          "Tasa México 3M (proxy)",
    "MX_10Y":         "Bono México 10Y (proxy)",
    "MX_YC_10Y_3M":   "Curva México 10Y-3M (proxy)",
    "DXY":            "Fortaleza del dólar (índice)",
    "USDMXN":         "Tipo de cambio USD/MXN",
    "MXNUSD":         "Fortaleza del peso (MXN/USD)",
    "WTI":            "Petróleo WTI (precio)",
    "VIX":            "Volatilidad implícita (VIX)",
}


def yoy_change(level_series: pd.Series, periods: int = 252) -> pd.Series:
    """Calcula cambio año-contra-año (YoY) de una serie de nivel.

    Para datos diarios, 252 periodos ≈ 1 año de días hábiles.

    Args:
        level_series: Serie en niveles.
        periods: Periodos para el cálculo YoY.

    Returns:
        pd.Series con cambio porcentual YoY (× 100, ej: 3.2 = 3.2%).
    """
    if level_series is None or level_series.dropna().empty:
        return pd.Series(dtype=float)
    return (level_series / level_series.shift(periods) - 1) * 100


def rolling_delta(series: pd.Series, window: int = 21) -> pd.Series:
    """Cambio de una serie en una ventana de N periodos.

    Ej: delta(EFFR, 21) = cambio del Fed Funds en el último mes.

    Args:
        series: Serie numérica.
        window: Ventana en periodos.

    Returns:
        pd.Series con el delta.
    """
    if series is None or series.dropna().empty:
        return pd.Series(dtype=float)
    return series - series.shift(window)


def build_macro_features(
    macro: pd.DataFrame,
    focus_start: Optional[str] = None,
) -> pd.DataFrame:
    """Construye el DataFrame de features macro para los modelos.

    Incluye niveles de indicadores + deltas de 1 mes (21 días hábiles).

    Args:
        macro: DataFrame de series macro (output de macro_data.build_macro_df + compute_derived_macro).
        focus_start: Fecha de inicio del periodo de análisis. None = usar todo.

    Returns:
        DataFrame con features con nombres legibles en español.
    """
    features = pd.DataFrame(index=macro.index)

    # 1) Niveles de indicadores macro
    for col, nice_name in FEATURE_NICE_NAMES.items():
        if col in macro.columns:
            features[nice_name] = macro[col]

    # 2) Cambios 1 mes (momentum macro)
    for col in list(features.columns):
        features[f"Cambio 1m: {col}"] = rolling_delta(features[col], 21)

    features = features.sort_index()

    # 3) Filtrar por periodo de focus
    if focus_start is not None:
        features = features.loc[features.index >= pd.Timestamp(focus_start)]

    log.info("Features construidos: %d columnas, %d filas", features.shape[1], features.shape[0])
    return features


def build_forward_returns(
    prices: pd.DataFrame,
    horizons_bdays: List[int],
    name_map: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Calcula retornos futuros logarítmicos para múltiples horizontes.

    Args:
        prices: DataFrame de precios (fechas × activos).
        horizons_bdays: Horizontes en días hábiles.
        name_map: {ticker: nombre_legible} para columnas.

    Returns:
        DataFrame con columnas tipo 'Forward {H}d: {Nombre}'.
    """
    result = pd.DataFrame(index=prices.index)

    for h in horizons_bdays:
        for col in prices.columns:
            fwd = np.log(prices[col].shift(-h) / prices[col])
            if name_map and col in name_map:
                col_name = f"Forward {h}d: {name_map[col]}"
            else:
                col_name = f"Forward {h}d: {col}"
            result[col_name] = fwd

    return result


def get_state_features(features: pd.DataFrame, min_valid: int = 200) -> List[str]:
    """Selecciona features de estado para kNN (solo niveles, sin deltas).

    Devuelve los features más relevantes que tengan suficientes datos.

    Args:
        features: DataFrame de features.
        min_valid: Mínimo de puntos válidos requeridos.

    Returns:
        Lista de nombres de columnas.
    """
    # Features de estado preferidos (en orden de prioridad)
    preferred = [
        "Tasa EUA (EFFR)",
        "Yield EUA 10 años",
        "Curva EUA 10Y-3M",
        "Inflación EUA (CPI YoY)",
        "Claims semanales EUA",
        "Condiciones financieras (NFCI)",
        "Spread High Yield (OAS)",
        "Breakeven inflación 5Y",
        "Fortaleza del dólar (índice)",
        "Tipo de cambio USD/MXN",
        "Petróleo WTI (precio)",
        "Volatilidad implícita (VIX)",
    ]

    available = [
        c for c in preferred
        if c in features.columns and features[c].dropna().shape[0] >= min_valid
    ]

    log.info("Features de estado seleccionados: %d/%d", len(available), len(preferred))
    return available


def get_model_features(features: pd.DataFrame, min_valid: int = 200) -> List[str]:
    """Selecciona features para el modelo logístico (niveles + deltas relevantes).

    Args:
        features: DataFrame de features.
        min_valid: Mínimo de puntos válidos.

    Returns:
        Lista de nombres de columnas.
    """
    state = get_state_features(features, min_valid)
    model_feats = list(state)

    # Añadir cambios 1m de features relevantes
    relevant_bases = [
        "Tasa EUA", "Yield EUA", "Curva EUA", "Inflación EUA",
        "Claims", "NFCI", "High Yield", "Breakeven",
        "Fortaleza del dólar", "USD/MXN", "Petróleo", "VIX",
    ]

    for col in features.columns:
        if col.startswith("Cambio 1m: ") and features[col].dropna().shape[0] >= min_valid:
            if any(base in col for base in relevant_bases):
                if col not in model_feats:
                    model_feats.append(col)

    return list(dict.fromkeys(model_feats))  # deduplicate preserving order
