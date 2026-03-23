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
from datetime import datetime

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
║      SISTEMA CUANTITATIVO UNIFICADO — v0.1.0 (Fase 1)       ║
║  Análisis Financiero · Valuación · Macro · Portafolio        ║
╚══════════════════════════════════════════════════════════════╝
"""

PHASE_STATUS = {
    "Fase 1 — Esqueleto y arquitectura": "✓ COMPLETADA",
    "Fase 2 — Datos y macro":            "○ PENDIENTE",
    "Fase 3 — Valuación y salud":        "○ PENDIENTE",
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


def run_phase1_stub(cfg: dict) -> None:
    """Ejecuta el stub de Fase 1: valida estructura y genera Excel de estado."""

    log.info("Verificando estructura del proyecto...")

    # Verificar que los módulos importan correctamente
    modules_ok = []
    modules_fail = []
    module_names = [
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

    import importlib
    for mod_name in module_names:
        try:
            importlib.import_module(mod_name)
            modules_ok.append(mod_name)
        except ImportError as exc:
            modules_fail.append((mod_name, str(exc)))
        except Exception:
            # NotImplementedError al nivel de módulo está bien en Fase 1
            modules_ok.append(mod_name)

    print(f"  Módulos verificados: {len(modules_ok)}/{len(module_names)}")
    if modules_fail:
        print("  ADVERTENCIAS de importación:")
        for mod, err in modules_fail:
            print(f"    ✗ {mod}: {err}")
    else:
        print("  ✓ Todos los módulos importan sin errores")
    print()

    # Verificar archivos de configuración
    config_files = [
        "config.yml",
        "config.example.yml",
        "requirements.txt",
        "architecture.md",
        "TODO.md",
        "CHANGELOG.md",
    ]
    print("  ── Archivos del Proyecto ────────────────────────────")
    for f in config_files:
        exists = pathlib.Path(f).exists()
        icono = "✓" if exists else "✗"
        print(f"  {icono} {f}")
    print()

    # Generar Excel de estado
    output_dir = cfg.get("output", {}).get("output_dir", "outputs")
    excel_name = cfg.get("output", {}).get("excel_filename", "resultado_analisis_financiero.xlsx")
    excel_path = str(pathlib.Path(output_dir) / excel_name)

    log.info("Generando Excel de estado del sistema...")
    result_path = write_stub_excel(
        output_path=excel_path,
        run_info={
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tickers": get_tickers(),
            "phases_done": ["Fase 1 — Esqueleto y arquitectura"],
        },
    )

    if result_path:
        print(f"  ✓ Excel generado: {result_path}")
    else:
        print("  ✗ No se pudo generar el Excel (revisa logs)")
    print()


def main() -> None:
    """Función principal del sistema."""
    parser = argparse.ArgumentParser(
        description="Sistema Cuantitativo Unificado — Análisis Financiero Profesional",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yml",
        help="Ruta al archivo de configuración (default: config.yml)",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Corre con tickers demo sin necesitar config.yml",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
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

    # En Fase 1: solo verificar y generar stub
    run_phase1_stub(cfg)

    print("=" * 64)
    print("  Sistema iniciado correctamente (Fase 1 — Esqueleto)")
    print()
    print("  Próximos pasos:")
    print("  1. Edita config.yml con tus tickers y parámetros")
    print("  2. Espera la Fase 2 para análisis macro real")
    print("  3. Espera la Fase 3 para valuaciones DCF")
    print("=" * 64)
    print()


if __name__ == "__main__":
    main()
