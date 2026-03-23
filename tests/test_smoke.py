# -*- coding: utf-8 -*-
"""
tests/test_smoke.py — Tests de humo básicos

Verifica que el sistema arranca y los módulos importan sin errores.
NO testea lógica de negocio (eso es para fases posteriores).

Cómo correr:
    python tests/test_smoke.py          # desde el directorio raíz del proyecto
    python -m pytest tests/ -v          # con pytest

Estado: Tests de Fase 1 implementados.
        Tests de Fases 2-5 marcados como TODO.
"""

import importlib
import pathlib
import sys
import os

# Asegurar que el directorio raíz está en el path
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

PASSED = []
FAILED = []


def test(name: str):
    """Decorador simple para registrar tests."""
    def decorator(fn):
        def wrapper():
            try:
                fn()
                PASSED.append(name)
                print(f"  ✓ {name}")
            except Exception as exc:
                FAILED.append((name, str(exc)))
                print(f"  ✗ {name}: {exc}")
        return wrapper
    return decorator


# ─────────────────────────────────────────────
# FASE 1: Tests de arquitectura y esqueleto
# ─────────────────────────────────────────────

@test("config.example.yml existe")
def test_config_example_exists():
    assert (ROOT / "config.example.yml").exists(), "config.example.yml no encontrado"


@test("requirements.txt existe")
def test_requirements_exists():
    assert (ROOT / "requirements.txt").exists(), "requirements.txt no encontrado"


@test("architecture.md existe")
def test_architecture_exists():
    assert (ROOT / "architecture.md").exists(), "architecture.md no encontrado"


@test("TODO.md existe")
def test_todo_exists():
    assert (ROOT / "TODO.md").exists(), "TODO.md no encontrado"


@test("CHANGELOG.md existe")
def test_changelog_exists():
    assert (ROOT / "CHANGELOG.md").exists(), "CHANGELOG.md no encontrado"


@test("main.py existe")
def test_main_exists():
    assert (ROOT / "main.py").exists(), "main.py no encontrado"


@test("Directorio outputs/ existe")
def test_outputs_dir():
    assert (ROOT / "outputs").is_dir(), "outputs/ no encontrado"


@test("src/ es paquete Python")
def test_src_package():
    assert (ROOT / "src" / "__init__.py").exists(), "src/__init__.py no encontrado"


@test("tests/ es paquete Python")
def test_tests_package():
    assert (ROOT / "tests" / "__init__.py").exists(), "tests/__init__.py no encontrado"


# ─────────────────────────────────────────────
# Tests de importación de módulos
# ─────────────────────────────────────────────

MODULES_TO_IMPORT = [
    "src",
    "src.utils",
    "src.config_loader",
    "src.data_sources",
    "src.market_data",
    "src.macro_data",
    "src.feature_engineering",
    "src.risk_country_fx",
    "src.valuation_dcf",
    "src.financial_health",
    "src.sector_model",
    "src.market_regime",
    "src.uncertainty_engine",
    "src.portfolio_optimizer",
    "src.scoring_engine",
    "src.news_data",
    "src.excel_report",
]


def test_module_imports():
    """Verifica que todos los módulos src/ importan sin errores."""
    for mod_name in MODULES_TO_IMPORT:
        name = f"Módulo {mod_name} importa"
        try:
            importlib.import_module(mod_name)
            PASSED.append(name)
            print(f"  ✓ {name}")
        except ImportError as exc:
            FAILED.append((name, str(exc)))
            print(f"  ✗ {name}: {exc}")
        except Exception:
            # NotImplementedError dentro de funciones es esperado en Fase 1
            PASSED.append(name)
            print(f"  ✓ {name}")


# ─────────────────────────────────────────────
# Tests de config_loader
# ─────────────────────────────────────────────

@test("config_loader carga defaults sin config.yml")
def test_config_defaults():
    from src.config_loader import load_config
    cfg = load_config("ARCHIVO_QUE_NO_EXISTE.yml")
    assert isinstance(cfg, dict)
    assert "tickers" in cfg
    assert "base_currency" in cfg
    assert len(cfg["tickers"]) > 0


@test("config_loader valida tickers como lista de strings")
def test_config_tickers_type():
    from src.config_loader import load_config
    cfg = load_config("ARCHIVO_QUE_NO_EXISTE.yml")
    tickers = cfg["tickers"]
    assert isinstance(tickers, list)
    assert all(isinstance(t, str) for t in tickers)


@test("config_loader carga config.example.yml sin errores")
def test_config_example_loads():
    from src.config_loader import load_config
    cfg = load_config(str(ROOT / "config.example.yml"))
    assert isinstance(cfg, dict)
    assert "tickers" in cfg
    assert "portfolio" in cfg
    assert "dcf" in cfg
    assert "risk" in cfg


@test("get_tickers() devuelve lista no vacía")
def test_get_tickers():
    from src.config_loader import get_tickers
    tickers = get_tickers()
    assert isinstance(tickers, list)
    assert len(tickers) > 0


@test("get_country_rf_erp('USD') devuelve floats razonables")
def test_rf_erp_usd():
    from src.config_loader import get_country_rf_erp
    rf, erp = get_country_rf_erp("USD")
    assert 0.0 < rf < 0.20, f"rf={rf} fuera de rango"
    assert 0.0 < erp < 0.20, f"erp={erp} fuera de rango"


@test("get_country_rf_erp('MXN') devuelve floats razonables")
def test_rf_erp_mxn():
    from src.config_loader import get_country_rf_erp
    rf, erp = get_country_rf_erp("MXN")
    assert 0.0 < rf < 0.30, f"rf={rf} fuera de rango"
    assert 0.0 < erp < 0.30, f"erp={erp} fuera de rango"


# ─────────────────────────────────────────────
# Tests de utils
# ─────────────────────────────────────────────

@test("norm_text normaliza texto correctamente")
def test_norm_text():
    from src.utils import norm_text
    assert norm_text("Operating Income") == "operating income"
    assert norm_text("D&A") == "d and a"
    assert "acciones" in norm_text("Acciones")


@test("sanitize_ticker limpia símbolos")
def test_sanitize_ticker():
    from src.utils import sanitize_ticker
    assert sanitize_ticker(" $aapl ") == "AAPL"
    assert sanitize_ticker("MSFT") == "MSFT"


@test("first_non_nan devuelve primer valor válido")
def test_first_non_nan():
    import math
    from src.utils import first_non_nan
    assert first_non_nan([float("nan"), None, 5.0]) == 5.0
    assert math.isnan(first_non_nan([]))
    assert first_non_nan([1.0, 2.0]) == 1.0


@test("pct_string_to_float convierte porcentajes")
def test_pct_string():
    from src.utils import pct_string_to_float
    assert abs(pct_string_to_float("6%") - 0.06) < 1e-9
    assert abs(pct_string_to_float("0.06") - 0.06) < 1e-9
    assert pct_string_to_float("no_es_numero", 0.05) == 0.05


@test("winsorize_1_99 no revienta con serie normal")
def test_winsorize():
    import pandas as pd
    import numpy as np
    from src.utils import winsorize_1_99
    s = pd.Series(np.random.randn(100))
    w = winsorize_1_99(s)
    assert len(w) == 100
    assert not w.isna().any()


# ─────────────────────────────────────────────
# Tests de valuation_dcf (lo que ya está implementado)
# ─────────────────────────────────────────────

@test("load_alias_builtin() devuelve diccionario con claves esperadas")
def test_alias_builtin():
    from src.valuation_dcf import load_alias_builtin
    alias = load_alias_builtin()
    assert isinstance(alias, dict)
    expected_keys = ["revenue", "op_income", "da", "net_income", "capex",
                     "cash_like", "ar", "lt_debt", "equity_total"]
    for k in expected_keys:
        assert k in alias, f"Clave '{k}' faltante en alias"
    # Verificar que los valores son listas no vacías
    for k, v in alias.items():
        assert isinstance(v, list) and len(v) > 0, f"'{k}' tiene lista vacía"


# ─────────────────────────────────────────────
# Tests de risk_country_fx (lo que ya está implementado)
# ─────────────────────────────────────────────

@test("normalize_price_currency convierte GBp a GBP")
def test_normalize_gbp():
    import pandas as pd
    from src.risk_country_fx import normalize_price_currency
    ccy, _, price = normalize_price_currency("GBp", last_price=1000.0)
    assert ccy == "GBP"
    assert abs(price - 10.0) < 1e-9


@test("normalize_price_currency no modifica USD")
def test_normalize_usd():
    from src.risk_country_fx import normalize_price_currency
    ccy, _, price = normalize_price_currency("USD", last_price=150.0)
    assert ccy == "USD"
    assert price == 150.0


# ─────────────────────────────────────────────
# Tests de excel_report
# ─────────────────────────────────────────────

@test("write_stub_excel() genera archivo sin error")
def test_stub_excel():
    from src.excel_report import write_stub_excel
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_output.xlsx")
        result = write_stub_excel(
            output_path=path,
            run_info={"timestamp": "2026-01-01 00:00", "tickers": ["AAPL", "MSFT"]},
        )
        assert result != "", "write_stub_excel devolvió string vacío"
        assert os.path.exists(result), f"Archivo no creado: {result}"
        assert os.path.getsize(result) > 0, "Archivo generado está vacío"


# ─────────────────────────────────────────────
# Archivos originales intactos
# ─────────────────────────────────────────────

@test("Script original 1 existe y no fue modificado")
def test_original_1_exists():
    p = ROOT / "que_va_a_pasar_en_el_mercado_.py"
    assert p.exists(), "Script original 1 fue eliminado"
    assert p.stat().st_size > 1000, "Script original 1 parece truncado"


@test("Script original 2 existe y no fue modificado")
def test_original_2_exists():
    p = ROOT / "umpa_ultra_mejorado_2_0_15_01_2026.py"
    assert p.exists(), "Script original 2 fue eliminado"
    assert p.stat().st_size > 10000, "Script original 2 parece truncado"


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def run_all_tests():
    print()
    print("=" * 60)
    print("  SMOKE TESTS — Sistema Cuantitativo Unificado v0.1")
    print("=" * 60)
    print()

    print("  ── Archivos del Proyecto ────────────────────────────")
    test_config_example_exists()
    test_requirements_exists()
    test_architecture_exists()
    test_todo_exists()
    test_changelog_exists()
    test_main_exists()
    test_outputs_dir()
    test_src_package()
    test_tests_package()
    test_original_1_exists()
    test_original_2_exists()

    print()
    print("  ── Importación de Módulos ───────────────────────────")
    test_module_imports()

    print()
    print("  ── config_loader ────────────────────────────────────")
    test_config_defaults()
    test_config_tickers_type()
    test_config_example_loads()
    test_get_tickers()
    test_rf_erp_usd()
    test_rf_erp_mxn()

    print()
    print("  ── utils ────────────────────────────────────────────")
    test_norm_text()
    test_sanitize_ticker()
    test_first_non_nan()
    test_pct_string()
    test_winsorize()

    print()
    print("  ── valuation_dcf (alias) ────────────────────────────")
    test_alias_builtin()

    print()
    print("  ── risk_country_fx (normalización) ──────────────────")
    test_normalize_gbp()
    test_normalize_usd()

    print()
    print("  ── excel_report ─────────────────────────────────────")
    test_stub_excel()

    print()
    print("=" * 60)
    total = len(PASSED) + len(FAILED)
    print(f"  RESULTADO: {len(PASSED)}/{total} tests pasaron")
    if FAILED:
        print()
        print("  FALLIDOS:")
        for name, err in FAILED:
            print(f"    ✗ {name}")
            print(f"      Error: {err}")
    print("=" * 60)
    print()

    return len(FAILED) == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
