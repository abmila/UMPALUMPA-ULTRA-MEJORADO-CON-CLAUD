# -*- coding: utf-8 -*-
"""
src/config_loader.py — Cargador de configuración central

Carga config.yml (o config.example.yml como fallback), valida parámetros
y expone un objeto CFG singleton usado por todos los módulos.

Origen: rescatado y extendido desde umpa_ultra_mejorado_2_0_15_01_2026.py
        (función load_config + CONFIG_DEFAULT, líneas 43-81).

Sin input() — todos los parámetros se leen desde config.yml.
"""

import logging
import os
import pathlib
import warnings
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Intentar importar yaml; si falla, usar fallback
# ─────────────────────────────────────────────
try:
    import yaml
    _HAS_YAML = True
except ImportError:
    yaml = None  # type: ignore
    _HAS_YAML = False
    warnings.warn("pyyaml no está instalado. Usa: pip install pyyaml", stacklevel=2)

# ─────────────────────────────────────────────
# Defaults completos del sistema
# ─────────────────────────────────────────────

CONFIG_DEFAULT: Dict[str, Any] = {
    # ── Tickers ──────────────────────────────────────────────────────────
    "tickers": ["AAPL", "MSFT", "GOOGL", "NVDA", "META", "SPY", "QQQ"],
    "base_currency": "USD",
    "valuation_currency": "USD",

    # ── Portafolio ────────────────────────────────────────────────────────
    "portfolio": {
        "years_history": 5,
        "risk_multiplier": 1.0,
        "budget_min": 10000.0,
        "budget_max": 50000.0,
        "na_threshold": 0.70,
        "lambda_adj": 0.40,
        "fixed_weights": {},
    },

    # ── Horizontes ────────────────────────────────────────────────────────
    "horizons": {
        "short": [5, 10, 15],
        "medium": [30],
        "long": [90, 180, 365],
    },

    # ── Macro ─────────────────────────────────────────────────────────────
    "macro": {
        "focus_years": 5,
        "download_years": 12,
        "knn_neighbors": 150,
        "horizon_bdays": 5,
    },

    # ── DCF ───────────────────────────────────────────────────────────────
    "dcf": {
        "years_projection": 7,
        "fade_method": "linear",
        "g_explicit_bounds": [-0.10, 0.20],
        "term_growth_dev": [0.015, 0.025],
        "term_growth_em": [0.020, 0.035],
    },

    # ── Riesgo / tasas ────────────────────────────────────────────────────
    "risk": {
        "erp_min": 0.035,
        "erp_max": 0.060,
        "erp_fallback": 0.055,
        "usd_rf_fallback": 0.040,
        "country_rates": {
            "MXN": {"rf": 0.090, "erp": 0.070},
            "EUR": {"rf": 0.030, "erp": 0.060},
            "GBP": {"rf": 0.040, "erp": 0.055},
        },
        "etr_caps": {
            "Mexico": 0.30, "México": 0.30, "MX": 0.30,
            "United States": 0.21, "USA": 0.21, "US": 0.21,
            "United Kingdom": 0.25, "UK": 0.25,
            "Germany": 0.30, "DE": 0.30,
            "France": 0.28, "FR": 0.28,
            "Japan": 0.30, "JP": 0.30,
            "Canada": 0.26, "CA": 0.26,
            "_DEFAULT": 0.30,
        },
    },

    # ── Output ────────────────────────────────────────────────────────────
    "output": {
        "excel_filename": "resultado_analisis_financiero.xlsx",
        "output_dir": "outputs",
        "language": "es",
        "include_raw_data": True,
    },

    # ── Datos / caché ─────────────────────────────────────────────────────
    "data": {
        "fred_api_key": "",
        "cache_dir": "outputs/cache",
        "portfolio_memory_file": "outputs/portfolios_memory.json",
        "canonical_tickers": {
            "TSMC": "TSM",
            "BRK.B": "BRK-B",
            "BRK.A": "BRK-A",
        },
    },

    # ── Flags ─────────────────────────────────────────────────────────────
    "flags": {
        "run_valuation": True,
        "run_macro": True,
        "run_portfolio": True,
        "run_news": False,
        "run_sector_signals": True,
        "debug_mode": False,
    },
}


# ─────────────────────────────────────────────
# Cargador principal
# ─────────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    """Fusiona override sobre base recursivamente (sin destruir sub-dicts del base).

    Args:
        base: Diccionario base con defaults.
        override: Diccionario con valores del usuario.

    Returns:
        Diccionario fusionado.
    """
    result = base.copy()
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(path: str = "config.yml") -> dict:
    """Carga el archivo de configuración YAML y lo fusiona con defaults.

    Busca el archivo en este orden:
      1. path exacto (relativo al cwd o absoluto)
      2. config.example.yml en el mismo directorio (solo lectura, sin modificar)
      3. Solo defaults si ninguno existe

    Args:
        path: Ruta al archivo config.yml (default: 'config.yml').

    Returns:
        Diccionario de configuración completo y validado.
    """
    cfg = CONFIG_DEFAULT.copy()

    # Buscar el archivo de configuración
    candidates = [
        pathlib.Path(path),
        pathlib.Path("config.yml"),
        pathlib.Path("config.example.yml"),
    ]
    found_path: Optional[pathlib.Path] = None
    for candidate in candidates:
        if candidate.exists():
            found_path = candidate
            break

    if found_path is None:
        log.warning(
            "No se encontró config.yml. "
            "Copia config.example.yml a config.yml y edítalo. "
            "Usando defaults por ahora."
        )
        return _validate_config(cfg)

    if not _HAS_YAML:
        log.warning("pyyaml no disponible — no se puede leer %s. Usando defaults.", found_path)
        return _validate_config(cfg)

    try:
        text = found_path.read_text(encoding="utf-8")
        user_cfg = yaml.safe_load(text)
        if isinstance(user_cfg, dict):
            cfg = _deep_merge(cfg, user_cfg)
            log.info("Configuración cargada desde: %s", found_path)
        else:
            log.warning("%s está vacío o mal formateado. Usando defaults.", found_path)
    except Exception as exc:
        log.warning("Error leyendo %s: %s — Usando defaults.", found_path, exc)

    return _validate_config(cfg)


def _validate_config(cfg: dict) -> dict:
    """Valida y normaliza tipos del diccionario de configuración.

    Aplica correcciones silenciosas donde es seguro, y emite warnings
    donde hay valores fuera de rango.

    Args:
        cfg: Diccionario de configuración (puede tener valores del usuario).

    Returns:
        Diccionario con tipos corregidos.
    """
    # Tickers: asegurar lista de strings no vacíos
    tickers = cfg.get("tickers", [])
    if isinstance(tickers, str):
        tickers = [t.strip() for t in tickers.split(",") if t.strip()]
    cfg["tickers"] = [str(t).strip().upper() for t in tickers if str(t).strip()]

    # Monedas
    cfg["base_currency"] = str(cfg.get("base_currency", "USD")).upper()
    cfg["valuation_currency"] = str(cfg.get("valuation_currency", "USD")).upper()

    # Portafolio
    port = cfg.get("portfolio", {})
    port["years_history"] = max(2, min(int(port.get("years_history", 5)), 15))
    port["risk_multiplier"] = max(0.1, float(port.get("risk_multiplier", 1.0)))
    port["budget_min"] = max(0.0, float(port.get("budget_min", 10000.0)))
    port["budget_max"] = max(port["budget_min"], float(port.get("budget_max", 50000.0)))
    port["na_threshold"] = max(0.3, min(float(port.get("na_threshold", 0.70)), 1.0))
    port["lambda_adj"] = max(0.0, min(float(port.get("lambda_adj", 0.40)), 1.0))
    if not isinstance(port.get("fixed_weights"), dict):
        port["fixed_weights"] = {}
    cfg["portfolio"] = port

    # DCF
    dcf = cfg.get("dcf", {})
    dcf["years_projection"] = max(3, min(int(dcf.get("years_projection", 7)), 15))
    cfg["dcf"] = dcf

    # Macro
    macro = cfg.get("macro", {})
    macro["download_years"] = max(5, min(int(macro.get("download_years", 12)), 30))
    macro["focus_years"] = max(1, min(int(macro.get("focus_years", 5)), macro["download_years"]))
    macro["knn_neighbors"] = max(10, min(int(macro.get("knn_neighbors", 150)), 500))
    cfg["macro"] = macro

    # Output: asegurar que output_dir existe
    out = cfg.get("output", {})
    out_dir = pathlib.Path(out.get("output_dir", "outputs"))
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    cfg["output"] = out

    return cfg


# ─────────────────────────────────────────────
# Singleton — cargado una vez al importar
# ─────────────────────────────────────────────

CFG: dict = load_config()


# ─────────────────────────────────────────────
# Helpers de acceso
# ─────────────────────────────────────────────

def get_tickers() -> List[str]:
    """Devuelve la lista de tickers configurados (ya canonicalizados).

    Returns:
        Lista de strings con tickers.
    """
    raw = CFG.get("tickers", [])
    canon = CFG.get("data", {}).get("canonical_tickers", {})
    return [canon.get(t, t) for t in raw]


def get_country_rf_erp(currency: str) -> Tuple[float, float]:
    """Devuelve (rf, erp) para una moneda dada, desde config.

    Si la moneda no está en config, usa los fallbacks de USD.

    Args:
        currency: Código de moneda ('USD', 'MXN', 'EUR', ...).

    Returns:
        Tupla (risk_free_rate, equity_risk_premium) como decimales.
    """
    rates = CFG.get("risk", {}).get("country_rates", {})
    if currency == "USD":
        rf_fallback = CFG.get("risk", {}).get("usd_rf_fallback", 0.04)
        erp_fallback = CFG.get("risk", {}).get("erp_fallback", 0.055)
        return rf_fallback, erp_fallback
    if currency in rates:
        r = rates[currency]
        return float(r.get("rf", 0.05)), float(r.get("erp", 0.06))
    log.warning("Moneda %s no encontrada en config.risk.country_rates — usando defaults.", currency)
    return 0.05, 0.065


def get_etr_cap(country: str) -> float:
    """Devuelve el cap de tasa efectiva de impuestos para un país.

    Args:
        country: Nombre o código de país.

    Returns:
        Cap de ETR como decimal. Default 0.30.
    """
    caps = CFG.get("risk", {}).get("etr_caps", {})
    return float(caps.get(country, caps.get("_DEFAULT", 0.30)))


def is_debug() -> bool:
    """Devuelve True si el modo debug está activado en config."""
    return bool(CFG.get("flags", {}).get("debug_mode", False))
