# -*- coding: utf-8 -*-
"""
main.py — Punto de entrada del Sistema Cuantitativo Unificado

Uso:
    python main.py                    # usa config.yml en el directorio actual
    python main.py --config mi.yml    # usa un archivo de configuración específico
    python main.py --demo             # corre con tickers demo sin necesitar config

Requiere: pip install -r requirements.txt
"""

import argparse
import logging
import pathlib
import sys
import warnings
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# Configurar logging ANTES de importar módulos
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")

# ─────────────────────────────────────────────
# Verificar versión de Python
# ─────────────────────────────────────────────
if sys.version_info < (3, 8):
    print("ERROR: Se requiere Python 3.8 o superior.")
    sys.exit(1)

# ─────────────────────────────────────────────
# Importar módulos del sistema
# ─────────────────────────────────────────────
try:
    from src.config_loader import load_config, get_tickers, CFG
    from src.excel_report import write_stub_excel
except ImportError as exc:
    print(f"ERROR importando módulos: {exc}")
    print("Asegúrate de estar en el directorio raíz del proyecto.")
    print("Instala dependencias: pip install -r requirements.txt")
    sys.exit(1)

# ─────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║      SISTEMA CUANTITATIVO UNIFICADO — v0.3.0 (Fase 3)       ║
║  Análisis Financiero · Valuación · Macro · Portafolio        ║
╚══════════════════════════════════════════════════════════════╝
"""

PHASE_STATUS = {
    "Fase 1 — Esqueleto y arquitectura": "✓ COMPLETADA",
    "Fase 2 — Datos y macro":            "✓ COMPLETADA",
    "Fase 3 — Valuación y salud":        "✓ COMPLETADA",
    "Fase 4 — Modelos y señales":        "○ PENDIENTE",
    "Fase 5 — Excel final y reporting":  "○ PENDIENTE",
}


def print_banner(cfg: dict) -> None:
    """Imprime el banner de inicio con el estado del sistema."""
    print(BANNER)
    print(f"  Fecha y hora:        {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  Moneda base:         {cfg.get('base_currency', 'USD')}")
    print(f"  Moneda valuación:    {cfg.get('valuation_currency', 'USD')}")
    tickers = get_tickers()
    print(f"  Tickers ({len(tickers)}):        {', '.join(tickers[:8])}{'...' if len(tickers) > 8 else ''}")
    print()
    print("  ── Estado de Fases ──────────────────────────────────")
    for fase, estado in PHASE_STATUS.items():
        print(f"  {estado}  {fase}")
    print()

    # Módulos habilitados
    flags = cfg.get("flags", {})
    print("  ── Módulos Habilitados ──────────────────────────────")
    modulos = [
        ("Valuación DCF",       flags.get("run_valuation", True)),
        ("Análisis Macro",      flags.get("run_macro", True)),
        ("Optimización Port.",  flags.get("run_portfolio", True)),
        ("Señales Sectoriales", flags.get("run_sector_signals", True)),
        ("Noticias/Sentimiento",flags.get("run_news", False)),
    ]
    for nombre, activo in modulos:
        icono = "✓" if activo else "✗"
        print(f"  {icono} {nombre}")
    print()


def run_phase2_macro(cfg: dict) -> dict:
    """Ejecuta la Fase 2: descarga de datos macro y de mercado.

    Returns:
        Dict con todos los datos descargados.
    """
    from src.config_loader import get_tickers
    from src.market_data import get_prices, get_forward_returns
    from src.macro_data import (
        download_all_macro, build_macro_df, compute_derived_macro,
        build_yield_curve, get_yield_curve_today, get_macro_summary,
    )
    from src.feature_engineering import (
        build_macro_features, build_forward_returns,
        get_state_features, get_model_features,
    )
    from src.risk_country_fx import get_rf_erp

    import pandas as pd

    tickers = get_tickers()
    macro_cfg = cfg.get("macro", {})
    download_years = macro_cfg.get("download_years", 12)
    focus_years = macro_cfg.get("focus_years", 5)
    horizons = cfg.get("horizons", {})
    all_horizons = horizons.get("short", [5]) + horizons.get("medium", [30]) + horizons.get("long", [90, 180, 365])
    val_ccy = cfg.get("valuation_currency", "USD")

    end = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(years=download_years)
    focus_start = end - pd.DateOffset(years=focus_years)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    print("=" * 64)
    print("  FASE 2: Descarga de datos macro y de mercado")
    print("=" * 64)
    print(f"  Periodo descarga:    {start_str} → {end_str}")
    print(f"  Periodo focus:       {focus_start.strftime('%Y-%m-%d')} → {end_str}")
    print(f"  Horizontes:          {all_horizons}")
    print()

    # ── 1) Descargar precios de tickers ────────────────────────
    print("  [1/5] Descargando precios de tickers...")
    ticker_prices, tickers_ok, tickers_failed = get_prices(
        tickers, years=download_years, min_points=50,
    )
    print(f"         ✓ {len(tickers_ok)}/{len(tickers)} tickers descargados")
    if tickers_failed:
        print(f"         ! Fallidos: {', '.join(tickers_failed)}")
    print()

    # ── 2) Descargar datos macro (FRED + Yahoo) ───────────────
    print("  [2/5] Descargando datos macro (FRED + Yahoo)...")
    fred_api_key = cfg.get("data", {}).get("fred_api_key", "")
    macro_result = download_all_macro(start_str, end_str, fred_api_key)

    fred_ok = len(macro_result["fred_chosen"]) - len(macro_result["fred_missing"])
    fred_total = len(macro_result["fred_chosen"])
    yahoo_ok = len(macro_result["yahoo_chosen"]) - len(macro_result["yahoo_missing"])
    yahoo_total = len(macro_result["yahoo_chosen"])
    sect_ok = len(macro_result["sector_chosen"]) - len(macro_result["sector_missing"])
    sect_total = len(macro_result["sector_chosen"])

    print(f"         ✓ FRED:     {fred_ok}/{fred_total} series")
    print(f"         ✓ Yahoo:    {yahoo_ok}/{yahoo_total} series macro")
    print(f"         ✓ Sectores: {sect_ok}/{sect_total} ETFs")

    if macro_result["fred_missing"]:
        print(f"         ! FRED faltantes: {', '.join(macro_result['fred_missing'][:10])}")
    if macro_result["yahoo_missing"]:
        print(f"         ! Yahoo faltantes: {', '.join(macro_result['yahoo_missing'])}")
    print()

    # ── 3) Construir macro unificado y derivadas ──────────────
    print("  [3/5] Construyendo features macro...")
    business_days = ticker_prices.index if len(ticker_prices) > 0 else pd.bdate_range(start_str, end_str)
    macro_df = build_macro_df(macro_result, business_days)
    macro_df = compute_derived_macro(macro_df)
    print(f"         ✓ Macro unificado: {macro_df.shape[1]} columnas, {macro_df.shape[0]} filas")

    features = build_macro_features(macro_df, focus_start=focus_start.strftime("%Y-%m-%d"))
    state_feats = get_state_features(features)
    model_feats = get_model_features(features)
    print(f"         ✓ Features: {features.shape[1]} totales, {len(state_feats)} de estado, {len(model_feats)} para modelo")
    print()

    # ── 4) Curva de bonos y resumen macro ─────────────────────
    print("  [4/5] Generando resumen macro...")
    yield_curve = get_yield_curve_today(macro_df)
    macro_summary = get_macro_summary(macro_df)

    print("         Curva de bonos UST actual:")
    for plazo, tasa in yield_curve.items():
        print(f"           {plazo}: {tasa:.3f}%")

    # Indicadores clave
    key_display = [
        ("EFFR", "Tasa Fed Funds"),
        ("UST_10Y", "UST 10Y"),
        ("YC_10Y_2Y", "Curva 10Y-2Y"),
        ("CPI_US_YOY", "Inflación CPI YoY"),
        ("NFCI", "Cond. Financieras"),
        ("HY_SPREAD", "HY Spread"),
        ("VIX", "VIX"),
        ("DXY", "DXY"),
        ("USDMXN", "USD/MXN"),
        ("WTI", "Petróleo WTI"),
        ("GOLD", "Oro"),
        ("MX_3M", "Tasa MX 3M"),
        ("CPI_MX_YOY", "Inflación MX YoY"),
    ]
    print()
    print("         Indicadores macro actuales:")
    for key, label in key_display:
        val = macro_summary.get(key)
        if val is not None:
            print(f"           {label:.<25s} {val:.4f}")
        else:
            print(f"           {label:.<25s} N/A")
    print()

    # ── 5) RF / ERP ───────────────────────────────────────────
    print("  [5/5] Obteniendo tasas de descuento...")
    rf, erp, rf_src, erp_src = get_rf_erp(val_ccy)
    print(f"         ✓ Risk-free ({val_ccy}):  {rf:.4f} ({rf_src})")
    print(f"         ✓ ERP ({val_ccy}):        {erp:.4f} ({erp_src})")
    print()

    # ── Generar Excel con datos macro ─────────────────────────
    output_dir = cfg.get("output", {}).get("output_dir", "outputs")
    excel_name = cfg.get("output", {}).get("excel_filename", "resultado_analisis_financiero.xlsx")
    excel_path = str(pathlib.Path(output_dir) / excel_name)

    print("  Generando Excel con datos macro...")
    _write_phase2_excel(
        excel_path, cfg, macro_df, macro_result, macro_summary,
        yield_curve, features, ticker_prices, tickers_ok, tickers_failed,
        rf, erp, rf_src, erp_src,
    )
    print(f"  ✓ Excel generado: {excel_path}")
    print()

    return {
        "ticker_prices": ticker_prices,
        "tickers_ok": tickers_ok,
        "tickers_failed": tickers_failed,
        "macro_result": macro_result,
        "macro_df": macro_df,
        "features": features,
        "macro_summary": macro_summary,
        "yield_curve": yield_curve,
        "rf": rf, "erp": erp,
        "rf_src": rf_src, "erp_src": erp_src,
    }


def _write_phase2_excel(
    path: str, cfg: dict, macro_df, macro_result, macro_summary,
    yield_curve, features, ticker_prices, tickers_ok, tickers_failed,
    rf, erp, rf_src, erp_src,
) -> None:
    """Genera Excel con los datos de Fase 2."""
    import pandas as pd
    from src.macro_data import build_yield_curve, FRED_CANDIDATES, YAHOO_MACRO

    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        workbook = writer.book

        # Formatos
        title_fmt = workbook.add_format({"bold": True, "font_size": 14, "bg_color": "#1F3864", "font_color": "white"})
        header_fmt = workbook.add_format({"bold": True, "font_size": 11, "bg_color": "#D6E4F0"})
        ok_fmt = workbook.add_format({"bg_color": "#C6EFCE", "font_color": "#276221"})
        warn_fmt = workbook.add_format({"bg_color": "#FFEB9C", "font_color": "#9C6500"})
        na_fmt = workbook.add_format({"bg_color": "#FFC7CE", "font_color": "#9C0006"})

        # ── RESUMEN_MERCADO ──────────────────────────────────
        ws = workbook.add_worksheet("RESUMEN_MERCADO")
        ws.set_column("A:A", 35)
        ws.set_column("B:B", 20)
        ws.set_column("C:C", 25)
        ws.write(0, 0, "RESUMEN DE MERCADO", title_fmt)
        ws.write(0, 1, datetime.now().strftime("%Y-%m-%d %H:%M"), title_fmt)
        ws.write(2, 0, "Indicador", header_fmt)
        ws.write(2, 1, "Valor Actual", header_fmt)

        row = 3
        indicators = [
            ("Tasa Fed Funds (EFFR)", "EFFR"),
            ("UST 3 meses", "UST_3M"),
            ("UST 2 años", "UST_2Y"),
            ("UST 10 años", "UST_10Y"),
            ("Curva 10Y-2Y (spread)", "YC_10Y_2Y"),
            ("Curva 10Y-3M (spread)", "YC_10Y_3M"),
            ("", None),
            ("Inflación CPI EUA (YoY)", "CPI_US_YOY"),
            ("Inflación Core CPI EUA (YoY)", "CORE_CPI_US_YOY"),
            ("Inflación PCE EUA (YoY)", "PCE_YOY"),
            ("Inflación Core PCE EUA (YoY)", "CORE_PCE_YOY"),
            ("Breakeven inflación 5Y", "BE_5Y"),
            ("Breakeven inflación 10Y", "BE_10Y"),
            ("", None),
            ("Desempleo EUA", "UNRATE_US"),
            ("Claims semanales EUA", "ICSA"),
            ("Condiciones financieras (NFCI)", "NFCI"),
            ("Spread High Yield (OAS)", "HY_SPREAD"),
            ("Spread Baa - UST 10Y", "BAA_10Y_SPREAD"),
            ("VIX", "VIX"),
            ("", None),
            ("DXY (Fortaleza USD)", "DXY"),
            ("USD/MXN", "USDMXN"),
            ("Petróleo WTI", "WTI"),
            ("Oro (GLD)", "GOLD"),
            ("Plata (SLV)", "SILVER"),
            ("", None),
            ("Inflación México (YoY)", "CPI_MX_YOY"),
            ("Tasa México 3M", "MX_3M"),
            ("Bono México 10Y", "MX_10Y"),
            ("Curva México 10Y-3M", "MX_YC_10Y_3M"),
        ]

        for label, key in indicators:
            if key is None:
                row += 1
                continue
            val = macro_summary.get(key)
            ws.write(row, 0, label)
            if val is not None:
                ws.write(row, 1, round(val, 4), ok_fmt)
            else:
                ws.write(row, 1, "N/A", na_fmt)
            row += 1

        # RF / ERP
        row += 2
        ws.write(row, 0, "PARÁMETROS DE DESCUENTO", header_fmt)
        row += 1
        ws.write(row, 0, f"Risk-free ({cfg.get('valuation_currency', 'USD')})")
        ws.write(row, 1, round(rf, 4))
        ws.write(row, 2, rf_src)
        row += 1
        ws.write(row, 0, f"ERP ({cfg.get('valuation_currency', 'USD')})")
        ws.write(row, 1, round(erp, 4))
        ws.write(row, 2, erp_src)

        # ── CURVA_BONOS ──────────────────────────────────────
        ws2 = workbook.add_worksheet("CURVA_BONOS")
        ws2.set_column("A:A", 15)
        ws2.set_column("B:B", 15)
        ws2.write(0, 0, "CURVA DE BONOS UST", title_fmt)
        ws2.write(0, 1, "", title_fmt)
        ws2.write(2, 0, "Plazo", header_fmt)
        ws2.write(2, 1, "Tasa (%)", header_fmt)
        for i, (plazo, tasa) in enumerate(yield_curve.items()):
            ws2.write(3 + i, 0, plazo)
            ws2.write(3 + i, 1, round(tasa, 3))

        # Curva histórica
        yield_df = build_yield_curve(macro_df)
        if yield_df is not None and not yield_df.empty:
            yield_df.to_excel(writer, sheet_name="CURVA_BONOS_HIST")

        # ── TASAS_EUA_MX ─────────────────────────────────────
        tasas_cols = [c for c in ["EFFR", "UST_3M", "UST_2Y", "UST_5Y", "UST_10Y", "UST_30Y",
                                   "MX_3M", "MX_10Y", "YC_10Y_2Y", "YC_10Y_3M", "MX_YC_10Y_3M"]
                     if c in macro_df.columns]
        if tasas_cols:
            macro_df[tasas_cols].dropna(how="all").to_excel(writer, sheet_name="TASAS_EUA_MX")

        # ── INFLACION_EUA_MX ─────────────────────────────────
        infl_cols = [c for c in ["CPI_US_YOY", "CORE_CPI_US_YOY", "PCE_YOY", "CORE_PCE_YOY",
                                  "BE_5Y", "BE_10Y", "CPI_MX_YOY"]
                    if c in macro_df.columns]
        if infl_cols:
            macro_df[infl_cols].dropna(how="all").to_excel(writer, sheet_name="INFLACION_EUA_MX")

        # ── COMMODITIES_FX ───────────────────────────────────
        comm_cols = [c for c in ["WTI", "GOLD", "SILVER", "DXY", "USDMXN", "MXNUSD", "VIX"]
                    if c in macro_df.columns]
        if comm_cols:
            macro_df[comm_cols].dropna(how="all").to_excel(writer, sheet_name="COMMODITIES_FX")

        # ── PRECIOS_TICKERS ──────────────────────────────────
        if len(ticker_prices) > 0:
            ticker_prices.to_excel(writer, sheet_name="PRECIOS_TICKERS")

        # ── FEATURES_MACRO ───────────────────────────────────
        feat_sample = features.tail(60)
        if len(feat_sample) > 0:
            feat_sample.to_excel(writer, sheet_name="FEATURES_MACRO_60D")

        # ── MACRO_RAW ────────────────────────────────────────
        if cfg.get("output", {}).get("include_raw_data", True):
            macro_df.to_excel(writer, sheet_name="RAW_DATA_SUMMARY")

        # ── SUPUESTOS_Y_FUENTES ──────────────────────────────
        ws_sup = workbook.add_worksheet("SUPUESTOS_Y_FUENTES")
        ws_sup.set_column("A:A", 30)
        ws_sup.set_column("B:B", 50)
        ws_sup.set_column("C:C", 25)
        ws_sup.write(0, 0, "SUPUESTOS Y FUENTES DE DATOS", title_fmt)
        ws_sup.write(0, 1, "", title_fmt)
        ws_sup.write(0, 2, "", title_fmt)
        ws_sup.write(2, 0, "Serie", header_fmt)
        ws_sup.write(2, 1, "Descripción", header_fmt)
        ws_sup.write(2, 2, "ID/Ticker usado", header_fmt)

        row_s = 3
        ws_sup.write(row_s, 0, "── FRED ──", header_fmt)
        row_s += 1
        for key, (desc, _) in FRED_CANDIDATES.items():
            chosen_id = macro_result["fred_chosen"].get(key)
            fmt = ok_fmt if chosen_id else na_fmt
            ws_sup.write(row_s, 0, key)
            ws_sup.write(row_s, 1, desc)
            ws_sup.write(row_s, 2, chosen_id or "NO DISPONIBLE", fmt)
            row_s += 1

        row_s += 1
        ws_sup.write(row_s, 0, "── Yahoo Finance ──", header_fmt)
        row_s += 1
        for key, (desc, _) in YAHOO_MACRO.items():
            chosen_t = macro_result["yahoo_chosen"].get(key)
            fmt = ok_fmt if chosen_t else na_fmt
            ws_sup.write(row_s, 0, key)
            ws_sup.write(row_s, 1, desc)
            ws_sup.write(row_s, 2, chosen_t or "NO DISPONIBLE", fmt)
            row_s += 1

        row_s += 1
        ws_sup.write(row_s, 0, "── Tickers del usuario ──", header_fmt)
        row_s += 1
        for t in tickers_ok:
            ws_sup.write(row_s, 0, t)
            ws_sup.write(row_s, 2, "OK", ok_fmt)
            row_s += 1
        for t in tickers_failed:
            ws_sup.write(row_s, 0, t)
            ws_sup.write(row_s, 2, "FALLÓ", na_fmt)
            row_s += 1

        # ── WARNINGS_Y_LIMITACIONES ──────────────────────────
        ws_w = workbook.add_worksheet("WARNINGS_Y_LIMITACIONES")
        ws_w.set_column("A:A", 80)
        ws_w.write(0, 0, "WARNINGS Y LIMITACIONES", title_fmt)
        warns = []
        if macro_result["fred_missing"]:
            warns.append(f"Series FRED no disponibles: {', '.join(macro_result['fred_missing'])}")
        if macro_result["yahoo_missing"]:
            warns.append(f"Series Yahoo no disponibles: {', '.join(macro_result['yahoo_missing'])}")
        if macro_result["sector_missing"]:
            warns.append(f"Sectores no disponibles: {', '.join(macro_result['sector_missing'])}")
        if tickers_failed:
            warns.append(f"Tickers sin datos suficientes: {', '.join(tickers_failed)}")
        warns.append("")
        warns.append("LIMITACIONES GENERALES:")
        warns.append("- Los datos macro de FRED tienen frecuencia mensual/semanal; se usan con forward-fill diario.")
        warns.append("- Las series de inflación YoY se calculan aproximando 252 días hábiles = 1 año.")
        warns.append("- Yahoo Finance puede tener datos faltantes o retrasados para algunos activos.")
        warns.append("- Las tasas de México vía FRED son proxies OECD y pueden tener rezago.")
        warns.append(f"- Risk-free ({rf_src}) y ERP ({erp_src}) se usan para valuación en Fases posteriores.")
        warns.append("- Este análisis NO constituye asesoría financiera.")

        for i, w in enumerate(warns):
            ws_w.write(2 + i, 0, w)

    log.info("Excel Fase 2 generado: %s", path)


def run_phase3_valuation(cfg: dict, tickers: Optional[List[str]] = None, rf: Optional[float] = None,
                         erp: Optional[float] = None) -> dict:
    """Ejecuta la Fase 3: Valuación DCF, Salud Financiera y Portafolio.

    Returns:
        Dict con todos los resultados de valuación y salud.
    """
    from src.config_loader import get_tickers
    from src.valuation_dcf import extract_financial_data, run_dcf_universe
    from src.financial_health import run_health_universe
    import yfinance as yf
    import numpy as np
    import pandas as pd

    if tickers is None:
        tickers = get_tickers()

    val_ccy = cfg.get("valuation_currency", "USD")

    if rf is None:
        rf = cfg.get("risk", {}).get("usd_rf_fallback", 0.04)
    if erp is None:
        erp = cfg.get("risk", {}).get("erp_fallback", 0.055)

    print("=" * 64)
    print("  FASE 3: Valuación DCF, Salud Financiera y Portafolio")
    print("=" * 64)
    print(f"  Tickers:             {len(tickers)} ({', '.join(tickers[:8])}{'...' if len(tickers) > 8 else ''})")
    print(f"  Risk-free:           {rf:.4f}")
    print(f"  ERP:                 {erp:.4f}")
    print(f"  Moneda valuación:    {val_ccy}")
    print()

    # ── 1) Extrae datos financieros ────────────────────────────
    print("  [1/5] Extrayendo datos financieros...")
    years_hist = cfg.get("portfolio", {}).get("years_history", 5)
    fin_data_map = {}
    for ticker in tickers:
        try:
            fin_data_map[ticker] = extract_financial_data(ticker, years_hist=years_hist)
        except Exception as e:
            log.warning(f"Error extrayendo {ticker}: {e}")
            fin_data_map[ticker] = {"_no_statements_": True, "ticker": ticker}
    print(f"         ✓ {len(fin_data_map)} tickers procesados")
    print()

    # ── 2) Corre DCF para universo ────────────────────────────
    print("  [2/5] Corriendo DCF para universo...")
    dcf_df = run_dcf_universe(tickers, valuation_currency=val_ccy, years_hist=years_hist, rf=rf, erp=erp)
    valid_valuations = dcf_df[dcf_df["valuation_method"] != "FAILED"]
    print(f"         ✓ {len(valid_valuations)}/{len(dcf_df)} valuaciones completadas")

    if len(valid_valuations) == 0:
        log.error("No hay valuaciones exitosas. Abortando Fase 3.")
        return {"dcf_df": dcf_df}
    print()

    # ── 3) Calcula salud financiera ────────────────────────────
    print("  [3/5] Calculando salud financiera...")
    health_df = run_health_universe(tickers, fin_data_map)
    print(f"         ✓ Salud calculada para {len(health_df)} tickers")

    # Merge DCF + Health
    analysis_df = dcf_df.merge(health_df, on="ticker", how="left")
    print()

    # ── 4) Genera reporte ────────────────────────────────────────
    print("  [4/5] Generando reporte...")
    output_dir = cfg.get("output", {}).get("output_dir", "outputs")
    excel_name = cfg.get("output", {}).get("excel_filename", "resultado_analisis_financiero.xlsx")
    excel_path = str(pathlib.Path(output_dir) / excel_name)

    _write_phase3_excel(excel_path, analysis_df, health_df, pd.DataFrame())
    print(f"  ✓ Excel generado: {excel_path}")
    print()

    # ── 5) Resumen ─────────────────────────────────────────────
    print("  [5/5] Resumen Fase 3")
    avg_upside = dcf_df["upside_base"].mean()
    avg_health = health_df["health_score"].mean()
    print(f"         Upside promedio (base):  {avg_upside:.2%}")
    print(f"         Health score promedio:   {avg_health:.1f}/100")
    print()

    return {
        "dcf_df": dcf_df,
        "health_df": health_df,
        "analysis_df": analysis_df,
        "fin_data_map": fin_data_map,
    }


def _write_phase3_excel(path: str, analysis_df: pd.DataFrame, health_df: pd.DataFrame,
                        quantities_df: pd.DataFrame) -> None:
    """Genera Excel con los datos de Fase 3."""
    import pandas as pd

    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        workbook = writer.book

        # Formatos
        title_fmt = workbook.add_format({"bold": True, "font_size": 14, "bg_color": "#1F3864", "font_color": "white"})
        header_fmt = workbook.add_format({"bold": True, "font_size": 11, "bg_color": "#D6E4F0"})
        number_fmt = workbook.add_format({"num_format": "0.0000"})

        # ── ANALISIS_COMPLETO ────────────────────────────────────
        if not analysis_df.empty:
            analysis_df.to_excel(writer, sheet_name="DCF_SALUD", index=False)

        # ── SALUD_FINANCIERA ─────────────────────────────────────
        if not health_df.empty:
            health_df.to_excel(writer, sheet_name="SALUD_FINANCIERA", index=False)


def main() -> None:
    """Función principal del sistema."""
    parser = argparse.ArgumentParser(
        description="Sistema Cuantitativo Unificado — Análisis Financiero Profesional",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config", type=str, default="config.yml",
        help="Ruta al archivo de configuración (default: config.yml)",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Corre con tickers demo sin necesitar config.yml",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Activa modo debug con logging detallado",
    )
    args = parser.parse_args()

    # Modo debug
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Cargar configuración
    if args.demo:
        log.info("Modo DEMO activado — usando tickers y parámetros de ejemplo")
        cfg = load_config("config.example.yml")
    else:
        cfg = load_config(args.config)

    # Imprimir banner
    print_banner(cfg)

    flags = cfg.get("flags", {})

    # ── FASE 2: Datos y Macro ───────────────────────────────
    if flags.get("run_macro", True):
        results = run_phase2_macro(cfg)
    else:
        log.info("Análisis macro deshabilitado en config (flags.run_macro = false)")
        results = {}

    print("=" * 64)
    print("  Ejecución completada (Fase 2 — Datos y Macro)")
    print()
    print("  Próximos pasos:")
    print("  1. Revisa el Excel generado en outputs/")
    print("  2. Fase 3: Valuación DCF y salud financiera")
    print("  3. Fase 4: Modelos de mercado y señales")
    print("=" * 64)
    print()


if __name__ == "__main__":
    main()
