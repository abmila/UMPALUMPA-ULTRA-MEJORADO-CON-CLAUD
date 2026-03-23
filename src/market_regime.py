# -*- coding: utf-8 -*-
"""
src/market_regime.py — Lectura del régimen macro de mercado

Interpreta el entorno macroeconómico y genera una lectura
estructurada del "régimen" actual:
  - Crecimiento vs Desaceleración
  - Inflación cediendo vs Repuntando
  - Endurecimiento vs Relajación financiera
  - Curva normal vs Invertida
  - Dólar fuerte vs Débil
  - Risk-on vs Risk-off

Además genera:
  - Sectores favorecidos por el régimen actual
  - Sectores presionados por el régimen actual
  - Conclusiones en español para el reporte ejecutivo

Origen: rescatado de que_va_a_pasar_en_el_mercado_.py
        (pretty_corr_list, train_predict_with_explain — líneas 417-575)

Estado: STUB — implementación completa en Fase 4
"""

import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd

log = logging.getLogger(__name__)

# Mapa de régimen → sectores favorecidos/presionados
REGIME_SECTOR_MAP = {
    "growth_risk_on": {
        "favorecidos": ["XLK", "XLY", "XLC"],
        "presionados": ["XLU", "XLP", "XLV"],
    },
    "defensivo_risk_off": {
        "favorecidos": ["XLU", "XLP", "XLV"],
        "presionados": ["XLK", "XLY", "XLC"],
    },
    "inflacion_alta": {
        "favorecidos": ["XLE", "XLB", "XLF"],
        "presionados": ["XLK", "XLRE", "XLU"],
    },
    "tasas_altas_curva_normal": {
        "favorecidos": ["XLF"],
        "presionados": ["XLRE", "XLU"],
    },
    "tasas_bajando": {
        "favorecidos": ["XLRE", "XLU", "XLK"],
        "presionados": ["XLF"],
    },
    "dolar_fuerte": {
        "favorecidos": ["XLF"],
        "presionados": ["XLE", "XLB"],
    },
    "dolar_debil": {
        "favorecidos": ["XLE", "XLB", "XLK"],
        "presionados": [],
    },
}


def classify_regime(macro_data: Dict[str, pd.Series]) -> Dict[str, str]:
    """Clasifica el régimen macro actual en múltiples dimensiones.

    Args:
        macro_data: Output de macro_data.download_all_macro().

    Returns:
        Dict con dimensiones de régimen, ej:
          {
            'crecimiento': 'desaceleracion',
            'inflacion': 'cediendo',
            'politica_monetaria': 'neutral',
            'curva_bonos': 'invertida',
            'dolar': 'fuerte',
            'sentimiento': 'risk_off',
            'resumen': 'Entorno defensivo: desaceleración + curva invertida...'
          }

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar clasificación de régimen")


def get_favored_sectors(regime: Dict[str, str]) -> Tuple[List[str], List[str]]:
    """Devuelve sectores favorecidos y presionados dado el régimen actual.

    Args:
        regime: Output de classify_regime().

    Returns:
        Tupla (sectores_favorecidos, sectores_presionados) — listas de ETF tickers.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar sectores por régimen")


def compute_top_correlations(
    features: pd.DataFrame,
    forward_returns: pd.DataFrame,
    ticker: str,
    horizon: int,
    n: int = 10,
) -> pd.DataFrame:
    """Calcula las N correlaciones más altas/bajas entre features y retornos futuros.

    Args:
        features: DataFrame de features macro.
        forward_returns: DataFrame de retornos futuros.
        ticker: Ticker de interés.
        horizon: Horizonte en días hábiles.
        n: Número de correlaciones a mostrar (top N positivas y negativas).

    Returns:
        DataFrame con columns [feature, correlacion, interpretacion].

    TODO (Fase 4): Implementar rescatando pretty_corr_list.
    """
    raise NotImplementedError("Fase 4: implementar correlaciones")


def generate_executive_summary(
    regime: Dict[str, str],
    favored: List[str],
    pressured: List[str],
    probs: pd.DataFrame,
) -> str:
    """Genera texto de resumen ejecutivo en español para el reporte.

    Args:
        regime: Output de classify_regime().
        favored: Sectores favorecidos.
        pressured: Sectores presionados.
        probs: Probabilidades por activo y horizonte.

    Returns:
        String con resumen legible en español.

    TODO (Fase 4): Implementar.
    """
    raise NotImplementedError("Fase 4: implementar resumen ejecutivo")
