# Changelog

Todos los cambios notables de este proyecto se documentan aquí.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/).

---

## [0.2.0] — 2026-03-23 — Fase 2: Datos, Macro y Feature Engineering

### Añadido
- `src/data_sources.py` — Implementación completa: Yahoo Finance (por ticker con fallbacks), FRED (pandas_datareader + HTTP fallback), FX spot/series, risk-free rate (FRED→Yahoo→config), ERP blended (SPY 5/10/30Y)
- `src/market_data.py` — Implementación completa: precios con limpieza, 11 ETFs de sector S&P 500, metadata de tickers, retornos diarios/semanales/mensuales, forward returns multi-horizonte
- `src/macro_data.py` — Implementación completa: 30 series FRED + 12 series Yahoo macro + 11 sectores, build_macro_df() con forward-fill, compute_derived_macro() (inflación YoY, curva de bonos, spreads), curva de rendimientos UST
- `src/feature_engineering.py` — Implementación completa: 35 features macro con nombres en español, YoY changes, rolling deltas, forward returns, selección de features para kNN y logística
- `src/risk_country_fx.py` — Implementación completa: get_rf_erp() sin input() (lee config para monedas no-USD), normalización de monedas, FX spot/series
- `main.py` — Actualizado a v0.2.0: run_phase2_macro() con pipeline completo de 5 pasos, generación de Excel con 10 hojas (RESUMEN_MERCADO, CURVA_BONOS, TASAS, INFLACION, COMMODITIES_FX, PRECIOS_TICKERS, FEATURES_MACRO, RAW_DATA, SUPUESTOS, WARNINGS)

### Rescatado de scripts originales
- `_download_one_ticker()`, `download_universe_yahoo()` → `src/data_sources.py`
- `fred_try_series()`, `download_fred_candidates()` → `src/data_sources.py` (con HTTP fallback añadido)
- `get_risk_free_usd()`, `blended_erp_usd()` → `src/data_sources.py`
- `get_rf_erp_with_sources()` → `src/risk_country_fx.py:get_rf_erp()` (sin input())
- `yoy_from_level()`, `delta()` → `src/feature_engineering.py`
- Catálogos FRED (30 series) y Yahoo macro (12 series) → `src/macro_data.py`
- Curva de bonos y spreads → `src/macro_data.py:compute_derived_macro()`

### Corregido
- pandas_datareader incompatible con pandas actual — añadido fallback HTTP directo a FRED CSV
- Import de pandas_datareader ahora captura TypeError además de ImportError

---

## [0.1.0] — 2026-03-23 — Fase 1: Esqueleto y Arquitectura

### Añadido
- `main.py` — Punto de entrada único con banner, verificación de módulos y generación de Excel de estado
- `config.example.yml` — Plantilla de configuración completa con todos los parámetros del sistema
- `requirements.txt` — Dependencias Python del proyecto
- `architecture.md` — Documentación completa de la arquitectura y decisiones de diseño
- `TODO.md` — Roadmap por fases con tareas detalladas
- `src/__init__.py` — Paquete Python con versión
- `src/config_loader.py` — Cargador de config con merge profundo, validación y singleton CFG
- `src/utils.py` — Helpers: norm_text, sanitize_ticker, parse_tickers, first_non_nan, safe_float, pct_string_to_float, last_value, pct_change_safe, winsorize_1_99, is_etf_or_index, fx_pair_ticker
- `src/data_sources.py` — Stub documentado para descarga Yahoo/FRED
- `src/market_data.py` — Stub con catálogo SECTOR_ETFS
- `src/macro_data.py` — Stub con catálogos FRED_SERIES y YAHOO_MACRO documentados
- `src/feature_engineering.py` — Stub documentado
- `src/risk_country_fx.py` — Stub con CCY_NORMALIZATION (GBp→GBP) ya funcional
- `src/valuation_dcf.py` — Stub con load_alias_builtin() ya implementado (alias contables)
- `src/financial_health.py` — Stub con THRESHOLDS de salud documentados
- `src/sector_model.py` — Stub documentado
- `src/market_regime.py` — Stub con REGIME_SECTOR_MAP documentado
- `src/uncertainty_engine.py` — Stub documentado con 6 fuentes de incertidumbre
- `src/portfolio_optimizer.py` — Stub documentado
- `src/scoring_engine.py` — Stub con SCORE_WEIGHTS documentado
- `src/news_data.py` — Stub conservador (get_ticker_news y get_macro_news devuelven [] con warning)
- `src/excel_report.py` — Stub con write_stub_excel() YA FUNCIONAL (genera Excel de estado)
- `outputs/.gitkeep` — Directorio de salidas inicializado
- `tests/__init__.py` — Paquete de tests

### Rescatado de scripts originales
- Lógica de `load_config()` y `CONFIG_DEFAULT` → `src/config_loader.py`
- Diccionario de alias contables (50+ patrones) → `src/valuation_dcf.py:load_alias_builtin()`
- Normalización de monedas (GBp, ZAc) → `src/risk_country_fx.py`
- Catálogos FRED y Yahoo macro → `src/macro_data.py`
- Catálogo de sector ETFs S&P 500 → `src/market_data.py`
- Utilidades: `_norm`, `sanitize_symbol`, `first_non_nan`, `_winsorize_1_99`, `_parse_tickers`, `pct_string_to_float` → `src/utils.py`

### Eliminado/Refactorizado
- **19 llamadas `input()`** del script original → reemplazadas por `config.yml`
- **`!pip install`** en líneas de código → movido a `requirements.txt`
- **Función `main()` duplicada** (líneas 1039 y 1328 del script original) → un solo `main.py`
- Mezcla de configuración con lógica de negocio → separación limpia en módulos

### Archivos originales preservados
- `que_va_a_pasar_en_el_mercado_.py` — sin modificar
- `umpa_ultra_mejorado_2_0_15_01_2026.py` — sin modificar

---

## [Próximos Releases]

### [0.3.0] — Fase 3: Valuación y Salud (pendiente)
- Implementación completa de `valuation_dcf.py`
- Implementación de `financial_health.py`
- Implementación de `risk_country_fx.py`
- Implementación de `portfolio_optimizer.py`
- Excel con hojas DCF y ratios

### [0.4.0] — Fase 4: Modelos y Señales (pendiente)
- Implementación de `sector_model.py` (kNN + logística)
- Implementación de `market_regime.py`
- Implementación de `uncertainty_engine.py`
- Implementación de `scoring_engine.py`
- Señales por horizonte (5d a 1Y)

### [0.5.0] — Fase 5: Reporting Final (pendiente)
- Excel ejecutivo completo con 22 hojas
- README completo con instrucciones
- Tests de humo
- Documentación de supuestos y fuentes
