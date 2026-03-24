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
        (líneas 158-996)
"""

import logging
import re
import unicodedata
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

from src.config_loader import CFG, get_etr_cap

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
    "valuation_method",
    "data_gaps", "nwc_method", "shares_source",
    "flags", "warnings",
]

# Constantes derivadas de config
YEARS_PROJ = CFG.get("dcf", {}).get("years_projection", 7)
GTERM_DEV = CFG.get("dcf", {}).get("term_growth_dev", [0.015, 0.025])
GTERM_EM = CFG.get("dcf", {}).get("term_growth_em", [0.020, 0.035])
MIN_G_EXPL, MAX_G_EXPL = CFG.get("dcf", {}).get("g_explicit_bounds", [-0.10, 0.20])
ERP_MIN = CFG.get("risk", {}).get("erp_min", 0.035)
ERP_MAX = CFG.get("risk", {}).get("erp_max", 0.060)


def _norm(s: str) -> str:
    """Normaliza string para búsqueda case-insensitive."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _compile_patterns(words: List[str]) -> List:
    """Compila palabras en regex patterns normalizados."""
    pats = []
    for w in words:
        pats.append(w if isinstance(w, re.Pattern) else re.compile(re.escape(_norm(w))))
    return pats


def _match_first_from_patterns(index_iterable, patterns) -> Tuple[Optional[str], Optional[str]]:
    """Busca el primer match en índice normalizado."""
    if index_iterable is None:
        return None, None
    idx_norm = {_norm(i): i for i in index_iterable}
    for pat in patterns:
        for norm_name, original in idx_norm.items():
            if pat.search(norm_name):
                return original, f"regex:{pat.pattern}"
    return None, None


def find_value(df: pd.DataFrame, patterns: List[str], col, prefer_nonzero: bool = False) -> Tuple[float, Optional[str], Optional[str]]:
    """Busca valor en DataFrame por patrones de alias."""
    name, why = _match_first_from_patterns(df.index if df is not None else [], _compile_patterns(patterns))
    if not name:
        return np.nan, None, None
    try:
        val = float(df.loc[name, col])
        if prefer_nonzero and (val == 0 or np.isnan(val)):
            return np.nan, None, None
        return val, name, why
    except Exception:
        return np.nan, None, None


def load_alias_builtin() -> dict:
    """Carga el diccionario de alias de cuentas contables.

    Mapea nombres canónicos (ej. 'revenue') a listas de nombres posibles
    en los estados financieros de Yahoo Finance.

    Returns:
        Dict {campo_canonico: [lista_de_nombres_posibles]}.
    """
    alias = {
        # Estado de resultados
        "revenue": ["total revenue", "revenue", "revenues",
                   "operating revenue", "net sales", "sales", "turnover"],
        "op_income": ["operating income", "operating profit", "ebit",
                     "total operating income as reported", "income from operations"],
        "da": ["depreciation and amortization", "depreciation",
               "amortization", "depreciation income statement",
               "depreciation and amortization in income statement",
               "reconciled depreciation",
               "depreciation amortization depletion"],
        "tax_exp": ["income tax expense", "tax provision",
                   "provision for income taxes"],
        "interest_exp": ["interest expense", "interest expense non operating",
                        "net interest expense"],
        "net_income": ["net income", "net income applicable to common shares",
                      "consolidated net income", "net earnings"],
        "capex": ["capital expenditure", "capital expenditure reported",
                 "purchase of ppe",
                 "purchase of property plant and equipment",
                 "additions to property plant and equipment"],
        "change_wc_cf": ["change in working capital",
                        "change in other working capital"],
        # Balance general
        "cash_like": ["cash and cash equivalents", "cash equivalents", "cash",
                     "cash cash equivalents and short term investments"],
        "sti": ["short term investments", "marketable securities"],
        "cash_restricted": ["restricted cash"],
        "ar": ["accounts receivable", "trade receivables",
              "net receivables"],
        "inventory": ["inventory", "inventories"],
        "other_ca": ["other current assets", "prepaid expenses",
                    "prepaid expenses and other current assets"],
        "ap": ["accounts payable", "trade payables"],
        "other_cl": ["other current liabilities", "accrued expenses",
                    "accrued liabilities", "other payables"],
        "deferred_rev_cur": ["deferred revenue", "deferred income",
                           "contract liabilities current", "unearned revenue"],
        "taxes_payable": ["income taxes payable", "taxes payable",
                         "current income taxes payable"],
        "cur_debt": ["current portion of long term debt", "short term debt",
                    "current debt",
                    "current debt and capital lease obligation",
                    "short term borrowings", "notes payable"],
        "lt_debt": ["long term debt",
                   "long term debt and capital lease obligation",
                   "long term borrowings",
                   "long term capital lease obligation"],
        "lease_lt": ["non current lease liabilities", "long term lease liabilities"],
        "lease_cur": ["current lease liabilities", "lease liabilities current"],
        "total_debt": ["total debt"],
        "equity_total": ["total stockholder equity",
                        "total shareholders equity"],
        "tot_ca": ["total current assets", "current assets"],
        "tot_cl": ["total current liabilities", "current liabilities"],
        "ppe_net": ["property plant equipment",
                   "property plant and equipment",
                   "net property plant and equipment",
                   "property plant equipment net"],
    }
    return {k: sorted(set(v)) for k, v in alias.items()}


def _get_series_from_bs(bal: pd.DataFrame, alias: dict, key: str) -> Tuple[List[float], List]:
    """Extrae serie de valores desde balance sheet."""
    arr = []
    src = []
    if bal is None or bal.empty:
        return arr, src
    for c in bal.columns:
        v, n, why = find_value(bal, alias.get(key, []), c)
        arr.append(v)
        src.append((n, why, "BS"))
    return arr, src


def _compute_operating_nwc_arrays(bal: pd.DataFrame, alias: dict) -> Tuple[List[float], np.ndarray, str]:
    """Calcula NWC operativo (OCA - OCL) desde balance."""
    cash_like, _ = _get_series_from_bs(bal, alias, "cash_like")
    sti, _ = _get_series_from_bs(bal, alias, "sti")
    cash_res, _ = _get_series_from_bs(bal, alias, "cash_restricted")
    ar, _ = _get_series_from_bs(bal, alias, "ar")
    invt, _ = _get_series_from_bs(bal, alias, "inventory")
    other_ca, _ = _get_series_from_bs(bal, alias, "other_ca")
    ap, _ = _get_series_from_bs(bal, alias, "ap")
    other_cl, _ = _get_series_from_bs(bal, alias, "other_cl")
    cur_debt, _ = _get_series_from_bs(bal, alias, "cur_debt")
    lease_cur, _ = _get_series_from_bs(bal, alias, "lease_cur")
    tot_ca, _ = _get_series_from_bs(bal, alias, "tot_ca")
    tot_cl, _ = _get_series_from_bs(bal, alias, "tot_cl")
    defrev, _ = _get_series_from_bs(bal, alias, "deferred_rev_cur")
    taxpay, _ = _get_series_from_bs(bal, alias, "taxes_payable")

    def nz(x):
        return 0.0 if (x is None or (isinstance(x, float) and np.isnan(x))) else float(x)

    N = len(bal.columns) if (bal is not None and not bal.empty) else 0
    if N == 0:
        return [], np.array([]), "NO_BS"

    OCA, OCL = [], []
    used_totals = False
    used_components = False

    for i in range(N):
        ca_t = tot_ca[i] if i < len(tot_ca) else np.nan
        cl_t = tot_cl[i] if i < len(tot_cl) else np.nan

        if not np.isnan(ca_t):
            oca = nz(ca_t) - nz(cash_like[i] if i < len(cash_like) else np.nan) \
                           - nz(sti[i] if i < len(sti) else np.nan) \
                           - nz(cash_res[i] if i < len(cash_res) else np.nan)
            used_totals = True
        else:
            oca = nz(ar[i] if i < len(ar) else np.nan) + nz(invt[i] if i < len(invt) else np.nan) + nz(
                other_ca[i] if i < len(other_ca) else np.nan)
            used_components = True

        if not np.isnan(cl_t):
            ocl = nz(cl_t) - nz(cur_debt[i] if i < len(cur_debt) else np.nan) - nz(lease_cur[i] if i < len(lease_cur) else np.nan)
        else:
            ocl = nz(ap[i] if i < len(ap) else np.nan) + nz(other_cl[i] if i < len(other_cl) else np.nan) \
                + nz(defrev[i] if i < len(defrev) else np.nan) + nz(taxpay[i] if i < len(taxpay) else np.nan)
            used_components = True

        OCA.append(oca)
        OCL.append(ocl)

    NWC = np.array([OCA[i] - OCL[i] for i in range(N)], dtype=float)
    delta = np.array([np.nan] * N, dtype=float)
    for k in range(0, max(0, N - 1)):
        if not np.isnan(NWC[k]) and not np.isnan(NWC[k + 1]):
            delta[k] = NWC[k] - NWC[k + 1]

    src = "BS_total" if used_totals else ("BS_components" if used_components else "BS")
    return list(NWC), delta, src


def _winsorize_1_99(x: pd.Series) -> pd.Series:
    """Winsoriza serie en percentiles 1-99."""
    if x is None or x.empty:
        return x
    lo, hi = np.nanpercentile(x, 1), np.nanpercentile(x, 99)
    return x.clip(lower=lo, upper=hi)


def fx_spot(from_ccy: str, to_ccy: str) -> float:
    """Obtiene tipo de cambio spot."""
    if not from_ccy or not to_ccy or from_ccy == to_ccy:
        return 1.0
    try:
        pair = f"{from_ccy}{to_ccy}=X"
        px = yf.Ticker(pair).history(period="5d", interval="1d")["Close"].dropna()
        return float(px.iloc[-1]) if not px.empty else 1.0
    except Exception:
        return 1.0


def first_non_nan(arr: List, default=np.nan):
    """Devuelve primer valor no-nan en lista."""
    for x in (arr or []):
        if x is not None and not (isinstance(x, float) and np.isnan(x)):
            return float(x)
    return default


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
    """
    tk = yf.Ticker(ticker)
    alias = load_alias_builtin()

    # Extrae estados anuales
    inc = tk.financials.iloc[:, :years_hist] if tk.financials is not None else pd.DataFrame()
    bal = tk.balance_sheet.iloc[:, :years_hist] if tk.balance_sheet is not None else pd.DataFrame()
    cf = tk.cashflow.iloc[:, :years_hist] if tk.cashflow is not None else pd.DataFrame()

    if inc.empty and bal.empty and cf.empty:
        return {"_no_statements_": True, "ticker": ticker}

    cols = list(inc.columns if not inc.empty else (cf.columns if not cf.empty else bal.columns))

    # Income Statement
    revenue, ebit, tax_exp, da_is, int_exp, net_income = [], [], [], [], [], []
    for c in cols:
        v, _, _ = find_value(inc, alias["revenue"], c)
        revenue.append(v)
        v, _, _ = find_value(inc, alias["op_income"], c)
        ebit.append(v)
        v, _, _ = find_value(inc, alias["tax_exp"], c)
        tax_exp.append(v)
        v, _, _ = find_value(inc, alias["da"], c)
        da_is.append(v)
        v, _, _ = find_value(inc, alias["interest_exp"], c)
        int_exp.append(v)
        v, _, _ = find_value(inc, alias["net_income"], c)
        net_income.append(v)

    # Cash Flow
    dep_cf, capex, chg_wc = [], [], []
    for c in (cf.columns if not cf.empty else cols):
        v, _, _ = find_value(cf, alias["da"], c)
        dep_cf.append(v)
        v, _, _ = find_value(cf, alias["capex"], c)
        capex.append(v)
        v, _, _ = find_value(cf, alias["change_wc_cf"], c)
        chg_wc.append(v)

    # NWC con fallback a trimestral
    NWC, delta_nwc, nwc_src = _compute_operating_nwc_arrays(bal, alias)

    if (len(delta_nwc) == 0) or (np.isnan(delta_nwc[0]) if len(delta_nwc) > 0 else True):
        try:
            qbal = tk.quarterly_balance_sheet
            if qbal is not None and not qbal.empty and len(qbal.columns) >= 5:
                _NWC_q, _delta_q, _src_q = _compute_operating_nwc_arrays(qbal, alias)
                if len(_NWC_q) >= 5 and not np.isnan(_NWC_q[0]) and not np.isnan(_NWC_q[4]):
                    arr = [np.nan] * (len(bal.columns) if not bal.empty else 1)
                    arr[0] = float(_NWC_q[0] - _NWC_q[4])
                    delta_nwc = np.array(arr, dtype=float)
                    nwc_src = "Quarterly_TTM"
        except Exception:
            pass

    # Fallback ΔNWC desde CF
    if (len(delta_nwc) == 0) or (np.isnan(delta_nwc[0]) if len(delta_nwc) > 0 else True):
        if len(chg_wc) > 0 and not np.isnan(chg_wc[0]):
            delta_nwc = np.array([-x if not np.isnan(x) else np.nan for x in chg_wc], dtype=float)
            nwc_src = "CF_fallback"

    # D&A: priorizar CF, luego IS, asegurar positivo
    da = []
    for i in range(max(len(da_is), len(dep_cf))):
        v_cf = dep_cf[i] if i < len(dep_cf) else np.nan
        v_is = da_is[i] if i < len(da_is) else np.nan
        v = v_cf if not np.isnan(v_cf) else (v_is if not np.isnan(v_is) else np.nan)
        if not np.isnan(v):
            v = abs(float(v))
        da.append(v)

    # Capex como salida de caja
    capex = [abs(v) if not np.isnan(v) else np.nan for v in capex]

    # Series de balance
    def _get_bal_series(key):
        arr = []
        for c in (bal.columns if not bal.empty else cols):
            v, _, _ = find_value(bal, alias[key], c)
            arr.append(v)
        return arr

    cur_debt = _get_bal_series("cur_debt")
    lt_debt = _get_bal_series("lt_debt")
    lease_lt = _get_bal_series("lease_lt")
    lease_cur = _get_bal_series("lease_cur")
    total_debt = _get_bal_series("total_debt")
    cash_like = _get_bal_series("cash_like")
    cash_res = _get_bal_series("cash_restricted")
    sti = _get_bal_series("sti")
    equity_tot = _get_bal_series("equity_total")
    ppe_net = _get_bal_series("ppe_net")

    def nz(x):
        return 0.0 if (x is None or (isinstance(x, float) and np.isnan(x))) else float(x)

    N = len(bal.columns) if not bal.empty else len(cols)
    debt_series = []
    for i in range(N):
        td = total_debt[i] if i < len(total_debt) and not np.isnan(total_debt[i]) else np.nan
        if np.isnan(td):
            td = nz(cur_debt[i]) + nz(lt_debt[i]) + nz(lease_lt[i]) + nz(lease_cur[i])
        debt_series.append(td)

    # Cash: diferencia para financieros vs operativos
    info_tk = tk.info or {}
    sector_l = (info_tk.get("sector") or "").lower()
    ind_l = (info_tk.get("industry") or "").lower()
    financial_like = any(s in ind_l for s in ["bank", "insurance", "capital markets", "reit"]) \
                    or any(s in sector_l for s in ["banks", "insurance", "reit"])

    if financial_like:
        cash_series = [nz(cash_like[i]) + nz(cash_res[i]) for i in range(N)]
    else:
        cash_series = [nz(cash_like[i]) + nz(cash_res[i]) + nz(sti[i]) for i in range(N)]

    eq_series = [nz(equity_tot[i]) for i in range(N)]
    ppe_series = [nz(ppe_net[i]) for i in range(N)]

    return {
        "ticker": ticker,
        "years": cols,
        "revenue": revenue, "ebit": ebit, "tax_exp": tax_exp, "interest_exp": int_exp,
        "da": da, "capex": capex, "delta_nwc": list(delta_nwc if isinstance(delta_nwc, np.ndarray) else []),
        "net_income": net_income,
        "cash_last": first_non_nan(cash_series),
        "debt_total_last": first_non_nan(debt_series),
        "debt_total_prev": debt_series[1] if len(debt_series) > 1 else np.nan,
        "equity_last": first_non_nan(eq_series),
        "ppe_last": first_non_nan(ppe_series),
        "nwc_source": nwc_src,
        "inc": inc.copy(), "bal": bal.copy(), "cf": cf.copy(),
        "debt_series": debt_series, "cash_series": cash_series
    }


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
    """
    bench = ("SPY" if (price_currency or "USD").upper() in ("USD", "") else
             "^MXX" if (price_currency or "").upper() == "MXN" else
             "^STOXX50E" if (price_currency or "").upper() == "EUR" else
             "^FTSE" if (price_currency or "").upper() == "GBP" else
             "^N225" if (price_currency or "").upper() == "JPY" else "^ACWI")

    start = (datetime.today() - timedelta(days=years * 365 + 10)).strftime("%Y-%m-%d")

    try:
        data = yf.download([ticker, bench], start=start, interval="1wk", auto_adjust=True, progress=False)

        if isinstance(data.columns, pd.MultiIndex):
            r = data["Close"][ticker].pct_change(fill_method=None).dropna()
            m = data["Close"][bench].pct_change(fill_method=None).dropna()
        else:
            r = data[ticker].pct_change(fill_method=None).dropna()
            m = data[bench].pct_change(fill_method=None).dropna()

        com = r.index.intersection(m.index)
        r, m = r.loc[com], m.loc[com]

        if len(r) < 60:
            return {"beta_calc": 1.0, "R2": 0.0, "N": len(r), "beta_info": np.nan,
                    "beta_used": 1.0, "beta_source": f"default_beta len={len(r)}", "bench": bench}

        r = _winsorize_1_99(r)
        m = _winsorize_1_99(m)

        rf_w = (rf_annual / 52.0)
        ex_r = r - rf_w
        ex_m = m - rf_w

        cov = np.cov(ex_r, ex_m)[0, 1]
        var = np.var(ex_m)
        beta_calc = float(cov / var) if var > 0 else 1.0
        corr = np.corrcoef(ex_r, ex_m)[0, 1] if var > 0 else 0.0
        R2 = float(corr ** 2) if np.isfinite(corr) else 0.0
        N = int(len(ex_r))

        info = yf.Ticker(ticker).info or {}
        beta_info = float(info.get("beta")) if info.get("beta") is not None else np.nan

        # Regla determinística
        if (N >= 120 and R2 >= 0.10) and np.isfinite(beta_calc):
            beta_used, src = beta_calc, "CALC"
        elif np.isfinite(beta_info):
            beta_used, src = beta_info, "INFO"
        else:
            beta_used, src = 1.0, "SECTOR_FALLBACK"

        return {"beta_calc": beta_calc, "R2": R2, "N": N, "beta_info": beta_info,
                "beta_used": beta_used, "beta_source": src, "bench": bench}

    except Exception as e:
        return {"beta_calc": 1.0, "R2": 0.0, "N": 0, "beta_info": np.nan,
                "beta_used": 1.0, "beta_source": f"fallback:{e}", "bench": bench}


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
    """
    Re = float(rf + beta * erp)
    Rd_eff = float(cost_of_debt * (1.0 - etr))
    V = float(equity_value + debt_value)

    if V > 0:
        wE = equity_value / V
        wD = debt_value / V
        wacc = wE * Re + wD * Rd_eff
    else:
        wacc = Re

    return float(wacc)


def _compute_annual_etr(tax_series: List[float], ebit_series: List[float],
                       int_series: List[float], country: str) -> Tuple[float, float, str]:
    """Calcula ETR anual mediana con cap por país."""
    cap = get_etr_cap(country)
    etrs = []

    for tax, ebit, inte in zip(tax_series, ebit_series, int_series):
        try:
            ebt = (0.0 if np.isnan(ebit) else float(ebit)) - (0.0 if np.isnan(inte) else float(inte))
            denom = max(1.0, ebt)
            if not np.isnan(tax) and denom > 0:
                etr_t = float(tax) / float(denom)
                if 0.0 <= etr_t <= 1.0:
                    etrs.append(etr_t)
        except Exception:
            pass

    etrs = [x for x in etrs if np.isfinite(x)]

    if len(etrs) >= 3:
        med3 = float(np.median(etrs[:3]))
        etr_final = float(min(med3, cap))
        return etr_final, med3, "ETR_3Y_MEDIAN"
    elif len(etrs) >= 1:
        med = float(np.median(etrs))
        etr_final = float(min(med, cap))
        return etr_final, med, "ETR_MEDIAN_PARTIAL"
    else:
        return cap, cap, "DEFAULT_COUNTRY"


def _robust_fcff0(fields: dict, etr_final: float) -> Tuple[float, dict]:
    """Calcula FCFF0 = NOPAT0 + D&A_avg - Capex_avg - ΔNWC_avg."""
    ebit = fields.get("ebit", []) or []
    da_arr = fields.get("da", []) or []
    capex = fields.get("capex", []) or []
    dNWC = fields.get("delta_nwc", []) or []

    def _clean_numeric(a):
        return [float(x) for x in a if x is not None and np.isfinite(x)]

    da_c = _clean_numeric(da_arr)
    cap_c = _clean_numeric(capex)
    dnwc_c = _clean_numeric(dNWC)

    method = "ANNUAL_3Y_MEAN"

    def _avg_last(a, n):
        return float(np.mean(a[:n])) if len(a) >= n else (float(np.mean(a)) if len(a) >= 1 else np.nan)

    if len(da_c) >= 5 and len(cap_c) >= 5 and len(dnwc_c) >= 5:
        DA_avg = _avg_last(da_c, 5)
        CAPEX_avg = _avg_last(cap_c, 5)
        DNWC_avg = _avg_last(dnwc_c, 5)
        method = "ANNUAL_5Y_MEAN"
    elif len(da_c) >= 3 and len(cap_c) >= 3 and len(dnwc_c) >= 3:
        DA_avg = _avg_last(da_c, 3)
        CAPEX_avg = _avg_last(cap_c, 3)
        DNWC_avg = _avg_last(dnwc_c, 3)
        method = "ANNUAL_3Y_MEAN"
    else:
        DA_avg = _avg_last(da_c, 1)
        CAPEX_avg = _avg_last(cap_c, 1)
        DNWC_avg = _avg_last(dnwc_c, 1)
        method = "TTM_4Q"

    ebit0 = first_non_nan(ebit, np.nan)
    if np.isnan(ebit0):
        return np.nan, {"DATA_GAPS": True, "why": "missing EBIT", "ΔNWC_METHOD": method}

    NOPAT0 = float(ebit0) * (1 - float(etr_final))
    for_check = [DA_avg, CAPEX_avg, DNWC_avg]
    if any([np.isnan(x) for x in for_check]):
        return np.nan, {"DATA_GAPS": True, "why": "missing DA/Capex/ΔNWC", "ΔNWC_METHOD": method}

    FCFF0 = float(NOPAT0 + DA_avg - CAPEX_avg - DNWC_avg)
    meta = {"DELTA_NWC_AVG": DNWC_avg, "CAPEX_AVG": CAPEX_avg, "DA_AVG": DA_avg,
            "NOPAT0": NOPAT0, "ΔNWC_METHOD": method, "DATA_GAPS": False}
    return FCFF0, meta


def _compute_roic_and_gexp(ebit0, tax_r, ppe_last, operating_nwc_last, reinvestment):
    """Calcula ROIC y g_explicit."""
    CIO0 = float(max(1e-6, (0.0 if np.isnan(ppe_last) else ppe_last) +
                     (0.0 if np.isnan(operating_nwc_last) else operating_nwc_last)))
    NOPAT0 = float(ebit0) * (1 - float(tax_r))
    ROIC0 = float(NOPAT0 / CIO0) if CIO0 > 0 else np.nan
    b0 = max(0.0, float(reinvestment) / max(1e-6, NOPAT0)) if NOPAT0 > 0 else 0.0
    g_exp = float(np.clip(b0 * (ROIC0 if not np.isnan(ROIC0) else 0.1), MIN_G_EXPL, MAX_G_EXPL))
    return NOPAT0, ROIC0, b0, g_exp, CIO0


def _project_fcff_with_fade(fcff0: float, g_exp: float, g_term: float, h: int,
                            method: str = "linear") -> List[float]:
    """Proyecta FCFF con fade lineal."""
    gs = [g_exp - (g_exp - g_term) * (t / h) for t in range(1, h + 1)]
    fcffs = []
    last = fcff0
    for g in gs:
        last = last * (1 + g)
        fcffs.append(last)
    return fcffs


def _safe_price_and_shares(tk: yf.Ticker, price_ccy_hint: str) -> Tuple[float, float, str, str, str]:
    """Obtiene precio y shares con validación."""
    info = tk.info or {}

    px = None
    if hasattr(tk, "fast_info") and tk.fast_info.get("lastPrice") is not None:
        px = float(tk.fast_info["lastPrice"])
    else:
        rawp = info.get("currentPrice") or info.get("previousClose")
        if rawp is not None:
            px = float(rawp)

    if px is None or (isinstance(px, float) and np.isnan(px)):
        try:
            h = tk.history(period="5d")["Close"].dropna()
            if len(h) > 0:
                px = float(h.iloc[-1])
        except Exception:
            pass

    price_ccy = (info.get("currency") or price_ccy_hint or "USD").upper()

    # Shares
    sh = None
    if "sharesOutstanding" in info and info["sharesOutstanding"] is not None:
        sh = float(info["sharesOutstanding"])
    elif "sharesShort" in info and "shortRatio" in info:
        try:
            sr = float(info.get("shortRatio", 1.0))
            ss = float(info.get("sharesShort", 0))
            sh = ss / max(0.01, sr) if sr > 0 else None
        except Exception:
            pass

    if sh is None or np.isnan(sh):
        if px and px > 0 and "marketCap" in info and info["marketCap"] is not None:
            sh = float(info["marketCap"]) / px
            shares_source = "MKTCAP/PX"
            curr_check = "REQUIRED"
        else:
            return np.nan, np.nan, price_ccy, "N/A", "MISSING"
    else:
        shares_source = "INFO"
        curr_check = "OK"

    return float(px) if px else np.nan, float(sh) if sh else np.nan, price_ccy, shares_source, curr_check


def dcf_valuation(
    ticker: str,
    financial_data: dict,
    rf: float,
    erp: float,
    rf_source: str = "calculado",
    erp_source: str = "calculado",
) -> dict:
    """Valuación DCF completa para un ticker.

    Implementa DCF Industrial, escenarios bear/base/bull.

    Args:
        ticker: Símbolo.
        financial_data: Output de extract_financial_data().
        rf: Tasa libre de riesgo.
        erp: Prima de riesgo de mercado.
        rf_source: Descripción de la fuente de rf.
        erp_source: Descripción de la fuente de erp.

    Returns:
        Dict con todos los campos de DCF_RESULT_FIELDS.
    """
    tk = yf.Ticker(ticker)
    info = tk.info or {}

    if financial_data.get("_no_statements_"):
        return {
            "ticker": ticker,
            "company_name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "country": info.get("country", ""),
            "currency": "USD",
            "price_local": np.nan,
            "price_base": np.nan,
            "intrinsic_base": np.nan,
            "intrinsic_bear": np.nan,
            "intrinsic_bull": np.nan,
            "upside_base": np.nan,
            "upside_bear": np.nan,
            "upside_bull": np.nan,
            "wacc": np.nan,
            "rf": rf,
            "erp": erp,
            "beta": np.nan,
            "beta_r2": np.nan,
            "beta_n": np.nan,
            "g_explicit": np.nan,
            "g_terminal": np.nan,
            "fcff0": np.nan,
            "roic": np.nan,
            "reinvestment_rate": np.nan,
            "etr": np.nan,
            "etr_source": "N/A",
            "gross_debt": np.nan,
            "net_debt": np.nan,
            "equity_market_cap": np.nan,
            "valuation_method": "FAILED",
            "data_gaps": "NO_STATEMENTS",
            "nwc_method": "N/A",
            "shares_source": "N/A",
            "flags": ["NO_STATEMENTS"],
            "warnings": ["No hay estados financieros disponibles"],
        }

    fin_ccy = (info.get("financialCurrency") or "USD").upper()
    country = (info.get("country") or "").strip() or "_DEFAULT"

    # Precio y acciones
    px, sh, price_ccy, shares_source, curr_check = _safe_price_and_shares(tk, "USD")

    if np.isnan(px) or np.isnan(sh) or sh <= 0:
        return {
            "ticker": ticker,
            "company_name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "country": country,
            "currency": price_ccy,
            "price_local": np.nan,
            "price_base": np.nan,
            "intrinsic_base": np.nan,
            "intrinsic_bear": np.nan,
            "intrinsic_bull": np.nan,
            "upside_base": np.nan,
            "upside_bear": np.nan,
            "upside_bull": np.nan,
            "wacc": np.nan,
            "rf": rf,
            "erp": erp,
            "beta": np.nan,
            "beta_r2": np.nan,
            "beta_n": np.nan,
            "g_explicit": np.nan,
            "g_terminal": np.nan,
            "fcff0": np.nan,
            "roic": np.nan,
            "reinvestment_rate": np.nan,
            "etr": np.nan,
            "etr_source": "N/A",
            "gross_debt": np.nan,
            "net_debt": np.nan,
            "equity_market_cap": np.nan,
            "valuation_method": "FAILED",
            "data_gaps": "NO_PRICE_OR_SHARES",
            "nwc_method": "N/A",
            "shares_source": shares_source,
            "flags": ["NO_PRICE_OR_SHARES"],
            "warnings": ["No hay precio o shares disponibles"],
        }

    # ETR
    etr_final, etr_med, etr_source = _compute_annual_etr(
        financial_data.get("tax_exp", []),
        financial_data.get("ebit", []),
        financial_data.get("interest_exp", []),
        country
    )

    # FCFF0
    FCFF0_fin, fcff_meta = _robust_fcff0(financial_data, etr_final)
    spot = fx_spot(fin_ccy, "USD")
    FCFF0_val = FCFF0_fin * spot if np.isfinite(FCFF0_fin) else np.nan

    if np.isnan(FCFF0_val):
        return {
            "ticker": ticker,
            "company_name": info.get("longName", ""),
            "sector": info.get("sector", ""),
            "country": country,
            "currency": price_ccy,
            "price_local": px,
            "price_base": px,
            "intrinsic_base": np.nan,
            "intrinsic_bear": np.nan,
            "intrinsic_bull": np.nan,
            "upside_base": np.nan,
            "upside_bear": np.nan,
            "upside_bull": np.nan,
            "wacc": np.nan,
            "rf": rf,
            "erp": erp,
            "beta": np.nan,
            "beta_r2": np.nan,
            "beta_n": np.nan,
            "g_explicit": np.nan,
            "g_terminal": np.nan,
            "fcff0": np.nan,
            "roic": np.nan,
            "reinvestment_rate": np.nan,
            "etr": etr_final,
            "etr_source": etr_source,
            "gross_debt": np.nan,
            "net_debt": np.nan,
            "equity_market_cap": px * sh,
            "valuation_method": "FAILED",
            "data_gaps": "NO_FCFF0",
            "nwc_method": fcff_meta.get("ΔNWC_METHOD", "N/A"),
            "shares_source": shares_source,
            "flags": ["NO_FCFF0"],
            "warnings": ["No hay FCFF disponible"],
        }

    # Beta
    beta_pack = compute_beta(ticker, price_ccy, rf)
    beta_used = float(beta_pack["beta_used"])

    # Re y g_term
    Re = float(rf + beta_used * erp)
    cc = "USD"
    g_lo, g_hi = GTERM_DEV[0], GTERM_DEV[1]
    g_term = min(g_hi, Re - 0.01) if Re > 0.01 else g_lo

    # g_exp via ROIC
    ebit0 = first_non_nan(financial_data.get("ebit", []), np.nan)
    operating_nwc_last = np.nan
    try:
        bal = financial_data.get("bal", pd.DataFrame())
        if bal is not None and not bal.empty:
            alias = load_alias_builtin()
            NWC, _, _ = _compute_operating_nwc_arrays(bal, alias)
            if len(NWC) > 0 and not np.isnan(NWC[0]):
                operating_nwc_last = float(NWC[0])
    except Exception:
        pass

    capex0 = first_non_nan(financial_data.get("capex", []), 0.0)
    da0 = first_non_nan(financial_data.get("da", []), 0.0)
    dNWC0 = first_non_nan(financial_data.get("delta_nwc", []), 0.0)
    reinv_fin = (0.0 if np.isnan(capex0) else capex0) - (0.0 if np.isnan(da0) else da0) + \
                (0.0 if np.isnan(dNWC0) else dNWC0)

    _, ROIC0, b0, g_exp_raw, CIO0 = _compute_roic_and_gexp(
        ebit0, etr_final, financial_data.get("ppe_last", np.nan), operating_nwc_last, reinv_fin
    )
    g_exp = float(np.clip(g_exp_raw, MIN_G_EXPL, MAX_G_EXPL))

    # Proyección
    fcffs = _project_fcff_with_fade(FCFF0_val, g_exp, g_term, YEARS_PROJ, method="linear")

    # Estructura de capital
    px_val = px
    E_mkt = max(px_val * sh, 0.0)

    def _compute_gross_debt(fields_dict):
        debt_last = fields_dict.get("debt_total_last", np.nan)
        return 0.0 if np.isnan(debt_last) else float(debt_last)

    D_gross = _compute_gross_debt(financial_data) * spot
    Cash_c = (0.0 if np.isnan(financial_data.get("cash_last", np.nan)) else
              float(financial_data.get("cash_last"))) * spot

    # Rd
    debt_last = financial_data.get("debt_total_last", np.nan)
    debt_prev = financial_data.get("debt_total_prev", np.nan)
    int0 = first_non_nan(financial_data.get("interest_exp", []), np.nan)

    if np.isnan(int0) or (np.isnan(debt_last) and np.isnan(debt_prev)) or \
       (max(1e-6, (0.0 if np.isnan(debt_last) else debt_last) +
            (0.0 if np.isnan(debt_prev) else debt_prev)) <= 0):
        Rd = max(rf, 0.05)
    else:
        avg_debt = 0.5 * ((0.0 if np.isnan(debt_last) else float(debt_last)) +
                         (0.0 if np.isnan(debt_prev) else float(debt_prev)))
        Rd = float(np.clip(abs(float(int0)) / max(1e-6, avg_debt), rf, 0.25))

    Rd_eff = Rd * (1.0 - etr_final)

    # WACC
    V = float(E_mkt + D_gross)
    if V > 0:
        wE = E_mkt / V
        wD = D_gross / V
        WACC = wE * Re + wD * Rd_eff
    else:
        WACC = Re

    # Validación g_term < WACC
    if WACC <= g_term + 1e-4:
        g_term = max(min(g_term, WACC - 0.01), -0.20)

    # Valuación: PV explícitos + TV Gordon
    PV = sum(fc / ((1 + WACC) ** i) for i, fc in enumerate(fcffs, 1))
    TV = fcffs[-1] * (1 + g_term) / (WACC - g_term)
    EV = PV + TV / ((1 + WACC) ** YEARS_PROJ)

    # Equity
    net_debt = D_gross - Cash_c
    equity_value = EV - net_debt
    intrinsic_val_ps = equity_value / sh
    intrinsic_px_price_ccy = intrinsic_val_ps

    # Escenarios
    g_exp_bear = g_exp * 0.70
    g_term_bear = g_term * 0.90
    WACC_bear = WACC + 0.005
    fcffs_bear = _project_fcff_with_fade(FCFF0_val, g_exp_bear, g_term_bear, YEARS_PROJ, method="linear")
    PV_bear = sum(fc / ((1 + WACC_bear) ** i) for i, fc in enumerate(fcffs_bear, 1))
    TV_bear = fcffs_bear[-1] * (1 + g_term_bear) / (WACC_bear - g_term_bear) if (WACC_bear - g_term_bear) > 1e-4 else 0
    EV_bear = PV_bear + TV_bear / ((1 + WACC_bear) ** YEARS_PROJ)
    equity_value_bear = EV_bear - net_debt
    intrinsic_px_bear = equity_value_bear / sh

    g_exp_bull = g_exp * 1.30
    g_term_bull = g_term * 1.10
    WACC_bull = WACC - 0.005
    fcffs_bull = _project_fcff_with_fade(FCFF0_val, g_exp_bull, g_term_bull, YEARS_PROJ, method="linear")
    PV_bull = sum(fc / ((1 + WACC_bull) ** i) for i, fc in enumerate(fcffs_bull, 1))
    TV_bull = fcffs_bull[-1] * (1 + g_term_bull) / (WACC_bull - g_term_bull) if (WACC_bull - g_term_bull) > 1e-4 else 0
    EV_bull = PV_bull + TV_bull / ((1 + WACC_bull) ** YEARS_PROJ)
    equity_value_bull = EV_bull - net_debt
    intrinsic_px_bull = equity_value_bull / sh

    # Upsides
    upside_base = (intrinsic_px_price_ccy - px) / px if px > 0 else np.nan
    upside_bear = (intrinsic_px_bear - px) / px if px > 0 else np.nan
    upside_bull = (intrinsic_px_bull - px) / px if px > 0 else np.nan

    return {
        "ticker": ticker,
        "company_name": info.get("longName", ""),
        "sector": info.get("sector", ""),
        "country": country,
        "currency": price_ccy,
        "price_local": px,
        "price_base": px,
        "intrinsic_base": intrinsic_px_price_ccy,
        "intrinsic_bear": intrinsic_px_bear,
        "intrinsic_bull": intrinsic_px_bull,
        "upside_base": upside_base,
        "upside_bear": upside_bear,
        "upside_bull": upside_bull,
        "wacc": WACC,
        "rf": rf,
        "erp": erp,
        "beta": beta_used,
        "beta_r2": beta_pack["R2"],
        "beta_n": beta_pack["N"],
        "g_explicit": g_exp,
        "g_terminal": g_term,
        "fcff0": FCFF0_val,
        "roic": ROIC0,
        "reinvestment_rate": b0,
        "etr": etr_final,
        "etr_source": etr_source,
        "gross_debt": D_gross,
        "net_debt": net_debt,
        "equity_market_cap": E_mkt,
        "valuation_method": "DCF_INDUSTRIAL",
        "data_gaps": "NONE" if not fcff_meta.get("DATA_GAPS", False) else "YES",
        "nwc_method": fcff_meta.get("ΔNWC_METHOD", "N/A"),
        "shares_source": shares_source,
        "flags": [] if not fcff_meta.get("DATA_GAPS", False) else ["DATA_GAPS"],
        "warnings": [fcff_meta.get("why", "")] if fcff_meta.get("DATA_GAPS", False) else [],
    }


def run_dcf_universe(
    tickers: List[str],
    valuation_currency: str = "USD",
    years_hist: int = 5,
    rf: Optional[float] = None,
    erp: Optional[float] = None,
) -> pd.DataFrame:
    """Corre DCF para una lista de tickers y devuelve tabla unificada.

    Args:
        tickers: Lista de tickers a valuar.
        valuation_currency: Moneda base para el análisis.
        years_hist: Años de historial financiero.
        rf: Tasa libre de riesgo (si None, usa fallback de config).
        erp: Prima de riesgo de mercado (si None, usa fallback de config).

    Returns:
        DataFrame con una fila por ticker y columnas de DCF_RESULT_FIELDS.
    """
    if rf is None:
        rf = CFG.get("risk", {}).get("usd_rf_fallback", 0.04)
    if erp is None:
        erp = CFG.get("risk", {}).get("erp_fallback", 0.055)

    results = []

    for ticker in tickers:
        try:
            log.info(f"DCF para {ticker}...")
            fin_data = extract_financial_data(ticker, years_hist=years_hist)
            dcf_result = dcf_valuation(ticker, fin_data, rf, erp)
            results.append(dcf_result)
        except Exception as e:
            log.error(f"Error en DCF {ticker}: {e}")
            results.append({
                "ticker": ticker,
                "company_name": "",
                "sector": "",
                "country": "",
                "currency": "USD",
                "price_local": np.nan,
                "price_base": np.nan,
                "intrinsic_base": np.nan,
                "intrinsic_bear": np.nan,
                "intrinsic_bull": np.nan,
                "upside_base": np.nan,
                "upside_bear": np.nan,
                "upside_bull": np.nan,
                "wacc": np.nan,
                "rf": rf,
                "erp": erp,
                "beta": np.nan,
                "beta_r2": np.nan,
                "beta_n": np.nan,
                "g_explicit": np.nan,
                "g_terminal": np.nan,
                "fcff0": np.nan,
                "roic": np.nan,
                "reinvestment_rate": np.nan,
                "etr": np.nan,
                "etr_source": "ERROR",
                "gross_debt": np.nan,
                "net_debt": np.nan,
                "equity_market_cap": np.nan,
                "valuation_method": "ERROR",
                "data_gaps": str(e),
                "nwc_method": "N/A",
                "shares_source": "N/A",
                "flags": ["ERROR"],
                "warnings": [str(e)],
            })

    return pd.DataFrame(results)
