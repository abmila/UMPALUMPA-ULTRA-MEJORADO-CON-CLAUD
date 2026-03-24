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
        (líneas 710-849)
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
    """
    ratios = {}

    # ─────────────────────────────────────────────────────
    # Liquidez
    # ─────────────────────────────────────────────────────
    # Current Ratio = Current Assets / Current Liabilities
    # Necesitamos extraer de balance o usar states
    bal = financial_data.get("bal", pd.DataFrame())

    def nz(x):
        """Null to zero."""
        return 0.0 if (x is None or (isinstance(x, float) and np.isnan(x))) else float(x)

    current_ratio = np.nan
    quick_ratio = np.nan

    if bal is not None and not bal.empty and len(bal.columns) > 0:
        # Primera columna = más reciente
        try:
            col = bal.columns[0]
            from src.valuation_dcf import find_value, load_alias_builtin
            alias = load_alias_builtin()

            tot_ca, _, _ = find_value(bal, alias.get("tot_ca", []), col)
            tot_cl, _, _ = find_value(bal, alias.get("tot_cl", []), col)

            if not np.isnan(tot_ca) and not np.isnan(tot_cl) and tot_cl > 0:
                current_ratio = float(tot_ca / tot_cl)

                # Quick Ratio = (CA - Inventory) / CL
                inventory, _, _ = find_value(bal, alias.get("inventory", []), col)
                quick_assets = nz(tot_ca) - nz(inventory)
                if quick_assets > 0:
                    quick_ratio = float(quick_assets / tot_cl)
        except Exception as e:
            log.debug(f"Error calculando liquidez: {e}")

    ratios["current_ratio"] = current_ratio
    ratios["quick_ratio"] = quick_ratio

    # ─────────────────────────────────────────────────────
    # Apalancamiento
    # ─────────────────────────────────────────────────────
    gross_debt = financial_data.get("debt_total_last", np.nan)
    cash_last = financial_data.get("cash_last", np.nan)

    ratios["gross_debt"] = gross_debt if not np.isnan(gross_debt) else np.nan
    ratios["cash"] = cash_last if not np.isnan(cash_last) else np.nan

    net_debt = np.nan
    if not np.isnan(gross_debt) and not np.isnan(cash_last):
        net_debt = float(gross_debt - cash_last)
    elif not np.isnan(gross_debt):
        net_debt = float(gross_debt)

    ratios["net_debt"] = net_debt

    # Debt / EBITDA
    debt_ebitda = np.nan
    ebit0 = None
    ebit_arr = financial_data.get("ebit", [])
    if ebit_arr:
        for x in ebit_arr:
            if x is not None and not np.isnan(x):
                ebit0 = float(x)
                break

    da_arr = financial_data.get("da", [])
    da0 = None
    if da_arr:
        for x in da_arr:
            if x is not None and np.isfinite(x):
                da0 = float(x)
                break

    if ebit0 is not None and da0 is not None and not np.isnan(gross_debt):
        ebitda = ebit0 + da0
        if ebitda > 0:
            debt_ebitda = float(gross_debt / ebitda)

    ratios["debt_ebitda"] = debt_ebitda

    # ─────────────────────────────────────────────────────
    # Cobertura de intereses
    # ─────────────────────────────────────────────────────
    interest_coverage = np.nan
    int_exp_arr = financial_data.get("interest_exp", [])
    int0 = None
    if int_exp_arr:
        for x in int_exp_arr:
            if x is not None and not np.isnan(x):
                int0 = float(x)
                break

    if ebit0 is not None and int0 is not None and int0 > 0:
        interest_coverage = float(ebit0 / int0)

    ratios["interest_coverage"] = interest_coverage

    # ─────────────────────────────────────────────────────
    # Rentabilidad
    # ─────────────────────────────────────────────────────
    # Operating Margin = EBIT / Revenue
    op_margin = np.nan
    revenue_arr = financial_data.get("revenue", [])
    revenue0 = None
    if revenue_arr:
        for x in revenue_arr:
            if x is not None and not np.isnan(x):
                revenue0 = float(x)
                break

    if ebit0 is not None and revenue0 is not None and revenue0 > 0:
        op_margin = float(ebit0 / revenue0)

    ratios["op_margin"] = op_margin

    # Net Margin = NI / Revenue
    net_margin = np.nan
    ni_arr = financial_data.get("net_income", [])
    ni0 = None
    if ni_arr:
        for x in ni_arr:
            if x is not None and not np.isnan(x):
                ni0 = float(x)
                break

    if ni0 is not None and revenue0 is not None and revenue0 > 0:
        net_margin = float(ni0 / revenue0)

    ratios["net_margin"] = net_margin

    # ROE = NI / Equity
    roe = np.nan
    equity_last = financial_data.get("equity_last", np.nan)
    if ni0 is not None and not np.isnan(equity_last) and equity_last > 0:
        roe = float(ni0 / equity_last)

    ratios["roe"] = roe

    # ROIC = NOPAT / Invested Capital
    roic = np.nan
    tax_exp_arr = financial_data.get("tax_exp", [])
    tax0 = None
    if tax_exp_arr:
        for x in tax_exp_arr:
            if x is not None and not np.isnan(x):
                tax0 = float(x)
                break

    if ebit0 is not None and tax0 is not None and revenue0 is not None and revenue0 > 0:
        # ETR aproximada
        etr = float(tax0 / max(1.0, ebit0)) if ebit0 > 0 else 0.21
        NOPAT = ebit0 * (1 - etr)

        # IC ≈ PPE + NWC
        ppe_last = financial_data.get("ppe_last", np.nan)
        # NWC operativo (simple)
        if bal is not None and not bal.empty and len(bal.columns) > 0:
            try:
                from src.valuation_dcf import _compute_operating_nwc_arrays, load_alias_builtin
                alias = load_alias_builtin()
                NWC_arr, _, _ = _compute_operating_nwc_arrays(bal, alias)
                nwc = NWC_arr[0] if len(NWC_arr) > 0 else np.nan
                if not np.isnan(ppe_last) and not np.isnan(nwc):
                    IC = ppe_last + nwc
                    if IC > 1e-6:
                        roic = float(NOPAT / IC)
            except Exception as e:
                log.debug(f"Error calculando ROIC: {e}")

    ratios["roic"] = roic

    # ─────────────────────────────────────────────────────
    # Calidad de flujo
    # ─────────────────────────────────────────────────────
    fcf_quality = np.nan
    capex_arr = financial_data.get("capex", [])
    capex0 = None
    if capex_arr:
        for x in capex_arr:
            if x is not None and np.isfinite(x):
                capex0 = float(x)
                break

    if da0 is not None and capex0 is not None and ni0 is not None and ni0 > 0:
        dNWC_arr = financial_data.get("delta_nwc", [])
        dnwc0 = None
        if dNWC_arr:
            for x in dNWC_arr:
                if x is not None and np.isfinite(x):
                    dnwc0 = float(x)
                    break
        else:
            dnwc0 = 0.0

        # FCF ≈ NI + DA - Capex - ΔNWC
        fcf = ni0 + da0 - capex0 - (0.0 if dnwc0 is None else dnwc0)
        fcf_quality = float(fcf / ni0) if ni0 > 0 else np.nan

    ratios["fcf_quality"] = fcf_quality

    return ratios


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
    """
    scores = {}

    # ─────────────────────────────────────────────────────
    # Liquidez (25%)
    # ─────────────────────────────────────────────────────
    cr = ratios.get("current_ratio", np.nan)
    qr = ratios.get("quick_ratio", np.nan)

    liquidity_scores = []
    if not np.isnan(cr):
        # Current Ratio: 1.0+ es bueno, 0.5 es malo
        cr_score = min(100.0, max(0.0, (cr / 1.5) * 100))
        liquidity_scores.append(cr_score)
    if not np.isnan(qr):
        # Quick Ratio: 0.8+ es bueno, 0.3 es malo
        qr_score = min(100.0, max(0.0, (qr / 1.0) * 100))
        liquidity_scores.append(qr_score)

    liquidity_score = float(np.mean(liquidity_scores)) if liquidity_scores else np.nan

    # ─────────────────────────────────────────────────────
    # Apalancamiento (35%)
    # ─────────────────────────────────────────────────────
    debt_ebitda = ratios.get("debt_ebitda", np.nan)

    leverage_scores = []
    if not np.isnan(debt_ebitda):
        # D/E ratio: 2.0 es normal, 5.0+ es alto
        # Score: 100 en 0, 0 en 6
        le_score = min(100.0, max(0.0, 100 - (debt_ebitda / 6.0) * 100))
        leverage_scores.append(le_score)

    leverage_score = float(np.mean(leverage_scores)) if leverage_scores else np.nan

    # ─────────────────────────────────────────────────────
    # Cobertura (20%)
    # ─────────────────────────────────────────────────────
    ic = ratios.get("interest_coverage", np.nan)

    coverage_scores = []
    if not np.isnan(ic) and ic > 0:
        # Interest Coverage: 2.0 es mínimo, 5.0+ es bueno
        ic_score = min(100.0, max(0.0, (ic / 5.0) * 100))
        coverage_scores.append(ic_score)

    coverage_score = float(np.mean(coverage_scores)) if coverage_scores else np.nan

    # ─────────────────────────────────────────────────────
    # Calidad de flujo (20%)
    # ─────────────────────────────────────────────────────
    fcf_q = ratios.get("fcf_quality", np.nan)
    net_margin = ratios.get("net_margin", np.nan)

    flow_scores = []
    if not np.isnan(fcf_q):
        # FCF/NI: 0.7+ es bueno, 0.3 es malo
        fcf_score = min(100.0, max(0.0, (fcf_q / 0.8) * 100))
        flow_scores.append(fcf_score)
    if not np.isnan(net_margin):
        # Net Margin: 10%+ es bueno, 0% es neutral
        nm_score = min(100.0, max(0.0, (net_margin / 0.10) * 100))
        flow_scores.append(nm_score)

    flow_score = float(np.mean(flow_scores)) if flow_scores else np.nan

    # ─────────────────────────────────────────────────────
    # Ponderación final
    # ─────────────────────────────────────────────────────
    scores["liquidity"] = liquidity_score
    scores["leverage"] = leverage_score
    scores["coverage"] = coverage_score
    scores["flow"] = flow_score

    weighted_components = []
    if not np.isnan(liquidity_score):
        weighted_components.append(liquidity_score * 0.25)
    if not np.isnan(leverage_score):
        weighted_components.append(leverage_score * 0.35)
    if not np.isnan(coverage_score):
        weighted_components.append(coverage_score * 0.20)
    if not np.isnan(flow_score):
        weighted_components.append(flow_score * 0.20)

    if not weighted_components:
        return np.nan

    health_score = float(sum(weighted_components) / (0.25 + 0.35 + 0.20 + 0.20))
    return health_score


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
    """
    flags = []

    # Liquidez
    cr = ratios.get("current_ratio", np.nan)
    if not np.isnan(cr) and cr < THRESHOLDS["current_ratio_min"]:
        flags.append(f"LIQUIDEZ_BAJA: Current Ratio {cr:.2f} < {THRESHOLDS['current_ratio_min']}")

    qr = ratios.get("quick_ratio", np.nan)
    if not np.isnan(qr) and qr < THRESHOLDS["quick_ratio_min"]:
        flags.append(f"LIQUIDEZ_ACIDA_BAJA: Quick Ratio {qr:.2f} < {THRESHOLDS['quick_ratio_min']}")

    # Apalancamiento
    de = ratios.get("debt_ebitda", np.nan)
    if not np.isnan(de) and de > THRESHOLDS["debt_ebitda_max"]:
        flags.append(f"APALANCAMIENTO_ALTO: Debt/EBITDA {de:.2f} > {THRESHOLDS['debt_ebitda_max']}")

    # Cobertura
    ic = ratios.get("interest_coverage", np.nan)
    if not np.isnan(ic) and ic < THRESHOLDS["interest_coverage_min"]:
        flags.append(f"COBERTURA_DEBIL: Interest Coverage {ic:.2f} < {THRESHOLDS['interest_coverage_min']}")

    # Calidad de flujo
    fcf_q = ratios.get("fcf_quality", np.nan)
    if not np.isnan(fcf_q) and fcf_q < THRESHOLDS["fcf_ni_ratio_min"]:
        flags.append(f"CALIDAD_EARNINGS_BAJA: FCF/NI {fcf_q:.2f} < {THRESHOLDS['fcf_ni_ratio_min']}")

    # Márgenes
    nm = ratios.get("net_margin", np.nan)
    if not np.isnan(nm) and nm < THRESHOLDS["net_margin_min"]:
        flags.append(f"PERDIDAS: Margen Neto {nm:.2%} < 0%")

    # ROE
    roe = ratios.get("roe", np.nan)
    if not np.isnan(roe) and roe < THRESHOLDS["roe_min"]:
        flags.append(f"ROE_BAJO: ROE {roe:.2%} < {THRESHOLDS['roe_min']:.2%}")

    return flags


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
    """
    rows = []

    for ticker in tickers:
        fin_data = financial_data_map.get(ticker, {})

        if not fin_data or fin_data.get("_no_statements_"):
            rows.append({
                "ticker": ticker,
                "current_ratio": np.nan,
                "quick_ratio": np.nan,
                "debt_ebitda": np.nan,
                "interest_coverage": np.nan,
                "op_margin": np.nan,
                "net_margin": np.nan,
                "roe": np.nan,
                "roic": np.nan,
                "fcf_quality": np.nan,
                "gross_debt": np.nan,
                "net_debt": np.nan,
                "health_score": np.nan,
                "flags": ["NO_DATA"],
            })
            continue

        try:
            ratios = compute_ratios(fin_data)
            health_score = compute_health_score(ratios)
            flags = detect_financial_flags(ratios)

            rows.append({
                "ticker": ticker,
                "current_ratio": ratios.get("current_ratio", np.nan),
                "quick_ratio": ratios.get("quick_ratio", np.nan),
                "debt_ebitda": ratios.get("debt_ebitda", np.nan),
                "interest_coverage": ratios.get("interest_coverage", np.nan),
                "op_margin": ratios.get("op_margin", np.nan),
                "net_margin": ratios.get("net_margin", np.nan),
                "roe": ratios.get("roe", np.nan),
                "roic": ratios.get("roic", np.nan),
                "fcf_quality": ratios.get("fcf_quality", np.nan),
                "gross_debt": ratios.get("gross_debt", np.nan),
                "net_debt": ratios.get("net_debt", np.nan),
                "health_score": health_score,
                "flags": ";".join(flags) if flags else "",
            })
        except Exception as e:
            log.error(f"Error en salud {ticker}: {e}")
            rows.append({
                "ticker": ticker,
                "current_ratio": np.nan,
                "quick_ratio": np.nan,
                "debt_ebitda": np.nan,
                "interest_coverage": np.nan,
                "op_margin": np.nan,
                "net_margin": np.nan,
                "roe": np.nan,
                "roic": np.nan,
                "fcf_quality": np.nan,
                "gross_debt": np.nan,
                "net_debt": np.nan,
                "health_score": np.nan,
                "flags": f"ERROR: {str(e)}",
            })

    return pd.DataFrame(rows)
