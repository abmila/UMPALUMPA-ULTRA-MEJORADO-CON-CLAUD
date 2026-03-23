# -*- coding: utf-8 -*-
"""
src/utils.py — Funciones utilitarias generales

Helpers pequeños y sin dependencias de negocio, reutilizables
por todos los módulos del sistema.

Origen: rescatado y limpiado de ambos scripts originales.
"""

import re
import math
import unicodedata
import logging
from typing import Any, List, Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Normalización de texto
# ─────────────────────────────────────────────

def norm_text(s: str) -> str:
    """Normaliza texto: minúsculas, sin acentos, sin puntuación especial.

    Usado para comparar nombres de cuentas contables de forma robusta.
    Ej: 'Operating Income' → 'operating income'
        'Depreciación & Amortización' → 'depreciacion and amortizacion'

    Args:
        s: Cadena a normalizar.

    Returns:
        Cadena normalizada.
    """
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def sanitize_ticker(sym: str) -> str:
    """Limpia y estandariza un símbolo bursátil.

    Elimina espacios, convierte a mayúsculas y quita el prefijo '$'.
    Ej: ' $aapl ' → 'AAPL'

    Args:
        sym: Símbolo de ticker a limpiar.

    Returns:
        Ticker limpio.
    """
    if not sym:
        return sym
    return str(sym).strip().upper().lstrip("$")


def parse_tickers(raw: str) -> List[str]:
    """Convierte una cadena de tickers separados por coma en lista limpia.

    Args:
        raw: Cadena tipo 'AAPL, MSFT, GOOGL' o 'AAPL MSFT GOOGL'.

    Returns:
        Lista de tickers sanitizados y únicos.
    """
    parts = re.split(r"[,\s]+", raw.strip())
    seen = set()
    result = []
    for t in parts:
        t = sanitize_ticker(t)
        if t and t not in seen:
            seen.add(t)
            result.append(t)
    return result


# ─────────────────────────────────────────────
# Valores seguros / manejo de NaN
# ─────────────────────────────────────────────

def first_non_nan(arr: List[Any], default: float = float("nan")) -> float:
    """Devuelve el primer valor no-NaN de una lista.

    Útil para iterar sobre candidatos fallback de datos financieros.

    Args:
        arr: Lista de valores (puede incluir None y NaN).
        default: Valor a devolver si todos son NaN/None.

    Returns:
        Primer valor válido o default.
    """
    for x in (arr or []):
        if x is not None and not (isinstance(x, float) and math.isnan(x)):
            return float(x)
    return default


def safe_float(val: Any, default: float = float("nan")) -> float:
    """Convierte un valor a float de forma segura.

    Args:
        val: Valor a convertir.
        default: Valor a devolver si la conversión falla.

    Returns:
        Float o default.
    """
    try:
        f = float(val)
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


def pct_string_to_float(s: str, default: float = 0.0) -> float:
    """Convierte string tipo '6%', '0.06' o '6' a float decimal.

    Args:
        s: Cadena representando un porcentaje.
        default: Valor si la conversión falla.

    Returns:
        Float. Ej: '6%' → 0.06, '0.06' → 0.06
    """
    s = s.strip().rstrip("%")
    try:
        v = float(s)
        return v / 100.0 if v > 1.0 else v
    except ValueError:
        return default


# ─────────────────────────────────────────────
# Series de pandas
# ─────────────────────────────────────────────

def last_value(series: pd.Series) -> Optional[float]:
    """Devuelve el último valor no-NaN de una serie.

    Args:
        series: Serie de pandas.

    Returns:
        Último valor válido o None si la serie está vacía.
    """
    s = series.dropna()
    if s.empty:
        return None
    return float(s.iloc[-1])


def pct_change_safe(series: pd.Series, periods: int = 1) -> pd.Series:
    """Calcula cambio porcentual sin propagar NaN al inicio.

    Args:
        series: Serie de precios.
        periods: Número de periodos para el cambio.

    Returns:
        Serie de retornos porcentuales.
    """
    return series.pct_change(periods).fillna(0.0)


def winsorize_1_99(x: pd.Series) -> pd.Series:
    """Winsoriza una serie al percentil 1-99 (elimina outliers extremos).

    Útil para limpiar retornos antes de calcular beta o covarianza.

    Args:
        x: Serie numérica.

    Returns:
        Serie winsorizada.
    """
    lo, hi = x.quantile(0.01), x.quantile(0.99)
    return x.clip(lower=lo, upper=hi)


# ─────────────────────────────────────────────
# Tickers
# ─────────────────────────────────────────────

def is_etf_or_index(sym: str, info: dict) -> bool:
    """Determina si un ticker es un ETF o índice de mercado.

    Usa el campo 'quoteType' de Yahoo Finance.

    Args:
        sym: Símbolo del ticker.
        info: Diccionario info de yf.Ticker.

    Returns:
        True si es ETF o índice.
    """
    qt = str(info.get("quoteType", "")).upper()
    return qt in {"ETF", "INDEX"} or sym.startswith("^")


def fx_pair_ticker(from_ccy: str, to_ccy: str) -> str:
    """Construye el ticker de Yahoo Finance para un par FX.

    Ej: ('USD', 'MXN') → 'USDMXN=X'

    Args:
        from_ccy: Moneda origen.
        to_ccy: Moneda destino.

    Returns:
        Ticker FX de Yahoo Finance.
    """
    return f"{from_ccy}{to_ccy}=X"
