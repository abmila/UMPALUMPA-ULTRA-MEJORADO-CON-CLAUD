# -*- coding: utf-8 -*-
"""
src/valuation_dcf.py — Motor de valuación DCF/FCFF

Implementa la valuación fundamental por descuento de flujos:
  - Extracción robusta de estados financieros (alias múltiples)
  - FCFF robusto con promedios 3/5 años y TTM
  - Beta semanal 5Y winsorizada con validación R²
  - WACC con pesos de mercado
  - DCF de 2 etapas con fade (linear o H-Model)
  - Escenarios bear/base/bull
  - DDM de 2 etapas para financieros
  - ETF proxy intrinsic
  - Flags de completitud y calidad de datos

Origen: rescatado de umpa_ultra_mejorado_2_0_15_01_2026.py
        (load_alias_builtin, extract_time_series_v4, compute_dcf_industrial,
         compute_financials_models, compute_etf_index_intrinsic, etc.
         líneas 158-996)

Estado: STUB — implementación completa en Fase 3
"""

import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# Resultado DCF con todos los campos importantes
DCF_RESULT_FIELDS = [
    "ticker", "company_name", "sector", "country", "currency",
    "price_local", "price_base",
    "intrinsic_base", "intrinsic_bear", "intrinsic_bull",
    "upside_base", "upside_bear", "upside_bull",
    "wacc", "rf", "erp", "beta", "beta_r2", "beta_n",
    "g_explicit", "g_terminal",
    "fcff0", "roic", "reinvestment_rate",
    "etr", "etr_source",
    "gross_debt", "net_debt", "equity_market_cap",
    "valuation_method",  # 'DCF_INDUSTRIAL', 'DDM', 'ETF_PROXY'
    "data_gaps", "nwc_method", "shares_source",
    "flags", "warnings",
]


def load_alias_builtin() -> dict:
    """Carga el diccionario de alias de cuentas contables.

    Mapea nombres canónicos (ej. 'revenue') a listas de nombres posibles
    en los estados financieros de Yahoo Finance.

    Returns:
        Dict {campo_canonico: [lista_de_nombres_posibles]}.

    Origen: líneas 158-196 de umpa_ultra_mejorado_2_0_15_01_2026.py
    """
    alias = {
        # Estado de resultados
        "revenue":      ["total revenue", "revenue", "revenues",
                         "operating revenue", "net sales", "sales", "turnover"],
        "op_income":    ["operating income", "operating profit", "ebit",
                         "total operating income as reported", "income from operations"],
        "da":           ["depreciation and amortization", "depreciation",
                         "amortization", "depreciation income statement",
                         "depreciation and amortization in income statement",
                         "reconciled depreciation",
                         "depreciation amortization depletion"],
        "tax_exp":      ["income tax expense", "tax provision",
                         "provision for income taxes"],
        "interest_exp": ["interest expense", "interest expense non operating",
                         "net interest expense"],
        "net_income":   ["net income", "net income applicable to common shares",
                         "consolidated net income", "net earnings"],
        "capex":        ["capital expenditure", "capital expenditure reported",
                         "purchase of ppe",
                         "purchase of property plant and equipment",
                         "additions to property plant and equipment"],
        "change_wc_cf": ["change in working capital",
                         "change in other working capital"],
        # Balance general
        "cash_like":    ["cash and cash equivalents", "cash equivalents", "cash",
                         "cash cash equivalents and short term investments"],
        "sti":          ["short term investments", "marketable securities"],
        "ar":           ["accounts receivable", "trade receivables",
                         "net receivables"],
        "inventory":    ["inventory", "inventories"],
        "other_ca":     ["other current assets", "prepaid expenses",
                         "prepaid expenses and other current assets"],
        "ap":           ["accounts payable", "trade payables"],
        "other_cl":     ["other current liabilities", "accrued expenses",
                         "accrued liabilities", "other payables"],
        "cur_debt":     ["current portion of long term debt", "short term debt",
                         "current debt",
                         "current debt and capital lease obligation",
                         "short term borrowings", "notes payable"],
        "lt_debt":      ["long term debt",
                         "long term debt and capital lease obligation",
                         "long term borrowings",
                         "long term capital lease obligation"],
        "total_debt":   ["total debt"],
        "equity_total": ["total stockholder equity",
                         "total shareholders equity"],
        "tot_ca":       ["total current assets", "current assets"],
        "tot_cl":       ["total current liabilities", "current liabilities"],
        "ppe_net":      ["property plant equipment",
                         "property plant and equipment",
                         "net property plant and equipment",
                         "property plant equipment net"],
    }
    return {k: sorted(set(v)) for k, v in alias.items()}


def extract_financial_data(ticker: str, years_hist: int = 6) -> dict:
    """Extrae estados financieros y métricas clave de un ticker.

    Descarga: Income Statement, Balance Sheet, Cash Flow (anual y trimestral).
    Calcula: FCFF0, NWC, D&A, Capex, ETR, deuda, acciones, precio, moneda.

    Args:
        ticker: Símbolo de Yahoo Finance.
        years_hist: Años de historial para promedios (3-6 recomendado).

    Returns:
        Dict con todos los campos financieros extraídos.
        Campos no disponibles tienen valor np.nan con flag DATA_GAPS.

    TODO (Fase 3): Implementar rescatando lógica de extract_time_series_v4.
    """
    raise NotImplementedError("Fase 3: implementar extracción de estados financieros")


def compute_beta(
    ticker: str,
    price_currency: str,
    rf_annual: float,
    years: int = 5,
) -> dict:
    """Calcula beta semanal de 5 años con winsorización y validación.

    Beta robusto: retornos semanales vs benchmark (SPY o ^GSPC),
    winsorización P1-P99, validación de R² mínimo y N mínimo.

    Args:
        ticker: Símbolo.
        price_currency: Moneda del precio (para elegir benchmark).
        rf_annual: Tasa libre de riesgo anualizada.
        years: Años de historial (default 5).

    Returns:
        Dict con: beta, beta_r2, beta_n, alpha, benchmark_used, method.

    TODO (Fase 3): Implementar rescatando beta_weekly_5y_robust.
    """
    raise NotImplementedError("Fase 3: implementar cálculo de beta")


def compute_wacc(
    beta: float,
    rf: float,
    erp: float,
    cost_of_debt: float,
    etr: float,
    equity_value: float,
    debt_value: float,
) -> float:
    """Calcula WACC con pesos de mercado.

    WACC = (E/V)×Re + (D/V)×Rd×(1-T)
    donde Re = rf + beta×erp

    Args:
        beta: Beta del activo.
        rf: Tasa libre de riesgo.
        erp: Prima de riesgo de mercado.
        cost_of_debt: Costo de deuda antes de impuestos.
        etr: Tasa efectiva de impuestos.
        equity_value: Valor de mercado del capital.
        debt_value: Valor de la deuda.

    Returns:
        WACC como decimal.

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar WACC")


def dcf_valuation(
    ticker: str,
    financial_data: dict,
    rf: float,
    erp: float,
    rf_source: str = "calculado",
    erp_source: str = "calculado",
) -> dict:
    """Valuación DCF completa para un ticker.

    Implementa:
      - DCF Industrial (FCFF) para empresas operativas
      - DDM 2 etapas para financieros/aseguradoras
      - Proxy intrínseco para ETFs/índices
      - Escenarios bear (-30% g, +50bps WACC) / base / bull (+30% g, -50bps WACC)

    Args:
        ticker: Símbolo.
        financial_data: Output de extract_financial_data().
        rf: Tasa libre de riesgo.
        erp: Prima de riesgo de mercado.
        rf_source: Descripción de la fuente de rf (para trazabilidad).
        erp_source: Descripción de la fuente de erp.

    Returns:
        Dict con todos los campos de DCF_RESULT_FIELDS.

    TODO (Fase 3): Implementar rescatando compute_dcf_industrial y variantes.
    """
    raise NotImplementedError("Fase 3: implementar valuación DCF completa")


def run_dcf_universe(
    tickers: List[str],
    valuation_currency: str = "USD",
    years_hist: int = 5,
) -> pd.DataFrame:
    """Corre DCF para una lista de tickers y devuelve tabla unificada.

    Args:
        tickers: Lista de tickers a valuar.
        valuation_currency: Moneda base para el análisis.
        years_hist: Años de historial financiero.

    Returns:
        DataFrame con una fila por ticker y columnas de DCF_RESULT_FIELDS.
        Tickers que fallan tienen fila con flags de error, no revientan el flujo.

    TODO (Fase 3): Implementar.
    """
    raise NotImplementedError("Fase 3: implementar DCF para universo")
