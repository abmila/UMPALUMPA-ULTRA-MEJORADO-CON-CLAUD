# -*- coding: utf-8 -*-
"""
src/risk_country_fx.py — Tasas de descuento, ERP y FX

Maneja todo lo relacionado con:
  - Tasa libre de riesgo (USD desde FRED/Yahoo, otras monedas desde config)
  - Equity Risk Premium (ERP blended desde historial SPY o config)
  - Conversión de monedas y normalización (GBp → GBP, etc.)
  - Riesgo país

Sin input() — todos los parámetros de monedas no-USD se leen de config.yml
bajo risk.country_rates.

Origen: rescatado de umpa_ultra_mejorado_2_0_15_01_2026.py
        (get_risk_free_usd, blended_erp_usd, get_rf_erp_with_sources,
         normalize_price_currency, get_fx_series, fx_spot — líneas 129-495)

Estado: STUB — implementación completa en Fase 2
"""

import logging
from typing import Dict, Optional, Tuple

import pandas as pd

log = logging.getLogger(__name__)

# Monedas cotizadas en fracciones (penny stocks de GBP, etc.)
CCY_NORMALIZATION: Dict[str, Tuple[str, float]] = {
    "GBp": ("GBP", 0.01),   # peniques → libras
    "ZAc": ("ZAR", 0.01),   # centavos ZAR → rand
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


def get_risk_free_usd() -> Tuple[float, str]:
    """Obtiene la tasa libre de riesgo USD (UST 10Y).

    Intenta en orden: FRED:DGS10 → Yahoo:^TNX → config fallback.

    Returns:
        Tupla (tasa_decimal, fuente_string).

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar risk-free USD")


def blended_erp_usd(rf: float) -> float:
    """Calcula ERP blended de EUA desde retornos históricos de SPY.

    Promedia ERP implícitos a 5, 10 y 30 años. Aplica bounds de config.

    Args:
        rf: Tasa libre de riesgo actual.

    Returns:
        ERP como decimal (ej. 0.052).

    TODO (Fase 2): Implementar.
    """
    raise NotImplementedError("Fase 2: implementar ERP blended USD")


def get_rf_erp(currency: str) -> Tuple[float, float, str, str]:
    """Devuelve (rf, erp, rf_source, erp_source) para una moneda dada.

    Para USD: intenta calcular desde datos de mercado.
    Para otras monedas: lee de config.risk.country_rates (sin input()).

    Args:
        currency: Código de moneda ('USD', 'MXN', 'EUR', etc.).

    Returns:
        Tupla (rf, erp, fuente_rf, fuente_erp).

    TODO (Fase 2): Implementar. Usa config_loader.get_country_rf_erp() para no-USD.
    """
    raise NotImplementedError("Fase 2: implementar get_rf_erp")


def fx_spot(from_ccy: str, to_ccy: str) -> float:
    """Tipo de cambio spot entre dos monedas.

    Args:
        from_ccy: Moneda origen.
        to_ccy: Moneda destino.

    Returns:
        Tipo de cambio. Retorna 1.0 si las monedas son iguales o en caso de error.

    TODO (Fase 2): Implementar con yfinance, fallback a 1.0 con warning.
    """
    if not from_ccy or not to_ccy or from_ccy == to_ccy:
        return 1.0
    raise NotImplementedError("Fase 2: implementar fx_spot")


def get_fx_series(from_ccy: str, to_ccy: str, start: str) -> pd.Series:
    """Serie histórica de tipo de cambio entre dos monedas.

    Intenta el par directo y luego el inverso si el directo falla.

    Args:
        from_ccy: Moneda origen.
        to_ccy: Moneda destino.
        start: Fecha de inicio.

    Returns:
        pd.Series con tipo de cambio diario.
        Devuelve serie de 1.0 si las monedas son iguales o hay error.

    TODO (Fase 2): Implementar.
    """
    if not from_ccy or not to_ccy or from_ccy == to_ccy:
        return pd.Series(dtype=float)
    raise NotImplementedError("Fase 2: implementar fx_series")
