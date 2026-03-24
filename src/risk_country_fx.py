# -*- coding: utf-8 -*-
"""
src/risk_country_fx.py — Tasas de descuento, ERP y FX

Maneja todo lo relacionado con:
  - Tasa libre de riesgo (USD desde FRED/Yahoo, otras monedas desde config)
  - Equity Risk Premium (ERP blended desde historial SPY o config)
  - Conversión de monedas y normalización (GBp → GBP, etc.)

Sin input() — todo desde config.yml.

Rescatado de umpa_ultra_mejorado_2_0_15_01_2026.py líneas 103-495.
"""

import logging
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from src.config_loader import CFG, get_country_rf_erp
from src.data_sources import (
    get_risk_free_usd,
    get_blended_erp_usd,
    get_fx_spot,
    get_fx_series,
)

log = logging.getLogger(__name__)

# Monedas cotizadas en fracciones
CCY_NORMALIZATION: Dict[str, Tuple[str, float]] = {
    "GBp": ("GBP", 0.01),
    "ZAc": ("ZAR", 0.01),
}


def normalize_price_currency(
    info_currency: str,
    series: Optional[pd.Series] = None,
    last_price: Optional[float] = None,
) -> Tuple[str, Optional[pd.Series], Optional[float]]:
    """Normaliza monedas cotizadas en fracciones (ej. GBp → GBP).

    Args:
        info_currency: Código de moneda de Yahoo Finance.
        series: Serie de precios a normalizar (opcional).
        last_price: Precio individual a normalizar (opcional).

    Returns:
        Tupla (moneda_normalizada, serie_normalizada, precio_normalizado).
    """
    ccy = (info_currency or "").strip()
    if ccy in CCY_NORMALIZATION:
        ccy_new, factor = CCY_NORMALIZATION[ccy]
        if series is not None:
            series = series * factor
        if last_price is not None:
            last_price = last_price * factor
        return ccy_new, series, last_price
    return ccy, series, last_price


def get_rf_erp(currency: str) -> Tuple[float, float, str, str]:
    """Devuelve (rf, erp, rf_source, erp_source) para una moneda dada.

    Para USD: calcula desde datos de mercado (FRED/Yahoo/SPY).
    Para otras monedas: lee de config.risk.country_rates.

    Sin input() — reemplaza get_rf_erp_with_sources() del script original.

    Args:
        currency: Código de moneda ('USD', 'MXN', 'EUR', etc.).

    Returns:
        Tupla (rf, erp, fuente_rf, fuente_erp).
    """
    risk_cfg = CFG.get("risk", {})
    c = currency.upper()

    if c == "USD":
        fallback_rf = float(risk_cfg.get("usd_rf_fallback", 0.04))
        rf, rf_src = get_risk_free_usd(fallback=fallback_rf)

        erp_min = float(risk_cfg.get("erp_min", 0.035))
        erp_max = float(risk_cfg.get("erp_max", 0.060))
        erp_fallback = float(risk_cfg.get("erp_fallback", 0.055))
        erp, erp_src = get_blended_erp_usd(rf, erp_min, erp_max, erp_fallback)
        erp = float(np.clip(erp, erp_min, erp_max))

        return rf, erp, rf_src, erp_src

    # Para cualquier otra moneda: leer de config
    rf_cfg, erp_cfg = get_country_rf_erp(c)
    log.info("RF/ERP para %s desde config: rf=%.4f, erp=%.4f", c, rf_cfg, erp_cfg)
    return rf_cfg, erp_cfg, f"config:{c}", f"config:{c}"


def fx_spot(from_ccy: str, to_ccy: str) -> float:
    """Tipo de cambio spot (delega a data_sources).

    Args:
        from_ccy: Moneda origen.
        to_ccy: Moneda destino.

    Returns:
        Tipo de cambio. 1.0 si misma moneda o error.
    """
    return get_fx_spot(from_ccy, to_ccy)


def fx_series(from_ccy: str, to_ccy: str, start: str) -> pd.Series:
    """Serie histórica de FX (delega a data_sources).

    Args:
        from_ccy: Moneda origen.
        to_ccy: Moneda destino.
        start: 'YYYY-MM-DD'.

    Returns:
        pd.Series con tipo de cambio diario.
    """
    return get_fx_series(from_ccy, to_ccy, start)
