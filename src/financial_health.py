# -*- coding: utf-8 -*-
"""
src/financial_health.py — Salud financiera y ratios contables

Calcula métricas de solidez y riesgo financiero:
  - Liquidez: Current Ratio, Quick Ratio (Prueba del Ácido)
  - Apalancamiento: Deuda Total, Deuda Neta, Debt/EBITDA
  - Cobertura: Interest Coverage Ratio
  - Rentabilidad: Márgenes operativo y neto, ROE, ROIC
  - Calidad de flujo: FCF vs Utilidad Neta
  - Flags de fragilidad contable o riesgo visible

Propósito: distinguir empresas sólidas de empresas frágiles ANTES de valuar.
Un DCF atractivo en una empresa frágil no vale lo mismo que en una sólida.

Origen: lógica rescatada de umpa_ultra_mejorado_2_0_15_01_2026.py
        (compute_gross_debt, campos de extract_time_series_v4 — líneas 710-849)

Estado: STUB — implementación completa en Fase 3
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Umbrales de referencia para flags (configurables)
THRESHOLDS = {
    "current_ratio_min": 1.0,       # < 1.0 = riesgo de liquidez
    "quick_ratio_min": 0.8,         # < 0.8 = liquidez ajustada baja
    "debt_ebitda_max": 4.0,         # > 4.0 = apalancamiento alto
    "interest_coverage_min": 2.0,   # < 2.0 = cobertura de intereses débil
    "fcf_ni_ratio_min": 0.7,        # FCF/NI < 0.7 = posible calidad de earnings baja
    "net_margin_min": 0.0,          # < 0 = pérdidas
    "roe_min": 0.05,                # < 5% = retorno bajo sobre capital
}


def compute_ratios(financial_data: dict) -> dict:
    """Calcula todos los ratios de salud financiera.

    Args:
        financial_data: Output de valuation_dcf.extract_financial_data().

    Returns:
        Dict con ratios calculados y flags. Campos no disponibles = np.nan.
        Incluye:
          - current_ratio, quick_ratio
          - gross_debt, net_debt, debt_ebitda
          - interest_coverage
          - op_margin, net_margin, roe, roic
          - fcf_quality (FCF/NI)
          - health_score: 0-100 (score compuesto de salud)
          - flags: lista de advertencias activas

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar cálculo de ratios")


def compute_health_score(ratios: dict) -> float:
    """Score compuesto de salud financiera (0-100, mayor = más sólido).

    Pondera:
      - 25%: Liquidez (current ratio, quick ratio)
      - 35%: Apalancamiento (debt/EBITDA, deuda neta/EBITDA)
      - 20%: Cobertura de intereses
      - 20%: Calidad de flujo (FCF/NI, márgenes)

    Args:
        ratios: Output de compute_ratios().

    Returns:
        Score entre 0 y 100. np.nan si no hay suficientes datos.

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar health score")


def detect_financial_flags(ratios: dict) -> List[str]:
    """Genera lista de flags de riesgo o alertas contables.

    Ejemplos de flags:
      - 'LIQUIDEZ_BAJA: Current Ratio < 1.0'
      - 'APALANCAMIENTO_ALTO: Debt/EBITDA > 4.0'
      - 'COBERTURA_DEBIL: Interest Coverage < 2.0'
      - 'CALIDAD_EARNINGS_BAJA: FCF/NI < 0.70'
      - 'PERDIDAS: Margen Neto negativo'

    Args:
        ratios: Output de compute_ratios().

    Returns:
        Lista de strings con flags activos. Lista vacía si no hay alertas.

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar detección de flags")


def run_health_universe(
    tickers: List[str],
    financial_data_map: Dict[str, dict],
) -> pd.DataFrame:
    """Calcula salud financiera para un universo de tickers.

    Args:
        tickers: Lista de tickers.
        financial_data_map: Dict {ticker: financial_data} de extract_financial_data().

    Returns:
        DataFrame con una fila por ticker y columnas de ratios + score + flags.

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar health para universo")
