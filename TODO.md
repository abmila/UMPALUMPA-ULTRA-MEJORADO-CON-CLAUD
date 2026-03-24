# TODO — Roadmap del Sistema Cuantitativo Unificado

**Última actualización:** 2026-03-24

---

## Estado General por Fase

| Fase | Estado | Descripción |
|------|--------|-------------|
| Fase 1 | ✅ COMPLETADA | Auditoría, diseño y esqueleto |
| Fase 2 | ✅ COMPLETADA | Datos, configuración y capa macro/mercado |
| Fase 3 | ✅ COMPLETADA | Valuación DCF, salud financiera, portafolio |
| Fase 4 | 🔲 PENDIENTE | Modelos de mercado, sectores, incertidumbre |
| Fase 5 | 🔲 PENDIENTE | Reporting final, Excel, README, pruebas |

---

## Fase 1 — COMPLETADA ✅

- [x] Leer ambos archivos originales completamente
- [x] Mapear funciones originales → módulos nuevos
- [x] Identificar todos los `input()` → reemplazados en config.yml
- [x] Identificar `!pip` → movidos a requirements.txt
- [x] Crear estructura de carpetas (src/, outputs/, tests/)
- [x] Crear `requirements.txt`
- [x] Crear `config.example.yml` con todos los parámetros
- [x] Crear `src/__init__.py`
- [x] Crear `src/config_loader.py` con lógica real
- [x] Crear `src/utils.py` con helpers rescatados
- [x] Crear stubs documentados para todos los módulos src/
- [x] Crear `main.py` ejecutable mínimo
- [x] Crear `architecture.md`
- [x] Crear `CHANGELOG.md`
- [x] Verificar que main.py corre sin errores
- [x] Commit y push a rama de desarrollo

**Verificación de Fase 1:**
```bash
python main.py          # debe mostrar banner y generar Excel de estado
python main.py --demo   # mismo resultado con tickers de ejemplo
```

---

## Fase 2 — COMPLETADA ✅

**Objetivo:** Capa confiable de descarga y limpieza de datos

### Módulos implementados:

#### `src/data_sources.py`
- [x] `download_prices_yahoo()` — precios con fallbacks por ticker
- [x] `download_universe_with_fallbacks()` — universo con alternativas
- [x] `fred_get_series()` — serie individual de FRED (pdr + HTTP fallback)
- [x] `fred_get_multiple()` — múltiples series con fallbacks
- [x] `get_fx_spot()` — tipo de cambio spot con par inverso
- [x] `get_fx_series()` — serie histórica FX con inversión automática
- [x] `get_risk_free_usd()` — FRED:DGS10 → Yahoo:^TNX → config fallback
- [x] `get_blended_erp_usd()` — ERP de SPY 5/10/30Y CAGR

#### `src/market_data.py`
- [x] `get_prices()` — precios limpios con min_points
- [x] `get_sector_etf_prices()` — 11 ETFs de sector S&P 500
- [x] `get_ticker_info()` — metadata: sector, país, industria, moneda
- [x] `get_returns()` — retornos diarios/semanales/mensuales
- [x] `get_forward_returns()` — retornos futuros multi-horizonte

#### `src/macro_data.py`
- [x] `download_all_macro()` — 30 series FRED + 12 Yahoo + 11 sectores
- [x] `build_macro_df()` — DataFrame unificado con forward-fill
- [x] `compute_derived_macro()` — inflación YoY, curva, spreads, MXNUSD
- [x] `build_yield_curve()` — estructura temporal UST
- [x] `get_yield_curve_today()` — curva actual puntual
- [x] `get_macro_summary()` — última lectura de indicadores clave

#### `src/feature_engineering.py`
- [x] `yoy_change()` — cambio YoY de niveles (252 días)
- [x] `rolling_delta()` — cambio en ventana N (momentum)
- [x] `build_macro_features()` — 35 features con nombres en español + deltas 1m
- [x] `build_forward_returns()` — retornos futuros logarítmicos
- [x] `get_state_features()` — selección para kNN (12 preferidos)
- [x] `get_model_features()` — selección para logística (niveles + deltas)

#### `src/risk_country_fx.py`
- [x] `get_rf_erp()` — rf + erp para cualquier moneda (sin input())
- [x] `normalize_price_currency()` — GBp→GBP, ZAc→ZAR
- [x] `fx_spot()` — tipo de cambio spot
- [x] `fx_series()` — historial FX

### Entregables verificados:
- [x] `python main.py --demo` corre pipeline completo con tickers demo
- [x] Imprime resumen de series descargadas
- [x] No truena si falta una serie (manejo graceful de errores)
- [x] Excel con 10 hojas macro/mercado
- [x] Log claro de fuentes de datos y warnings

---

## Fase 3 — COMPLETADA ✅

**Objetivo:** Motor DCF y salud financiera operativos

#### `src/valuation_dcf.py`
- [x] `load_alias_builtin()` — diccionario de 50+ alias contables
- [x] `extract_financial_data()` — estados financieros robustos con fallbacks
- [x] `compute_beta()` — beta semanal 5Y con winsorización P1-P99 y validación R²/N
- [x] `compute_wacc()` — WACC con pesos de mercado
- [x] `dcf_valuation()` — DCF industrial de 2 etapas + escenarios bear/base/bull
- [x] `run_dcf_universe()` — DCF para lista de tickers

#### `src/financial_health.py`
- [x] `compute_ratios()` — todos los ratios: liquidez, apalancamiento, cobertura, rentabilidad, flujo
- [x] `compute_health_score()` — score 0-100 ponderado
- [x] `detect_financial_flags()` — flags de riesgo (LIQUIDEZ_BAJA, APALANCAMIENTO_ALTO, etc.)
- [x] `run_health_universe()` — para lista de tickers

#### `src/portfolio_optimizer.py`
- [x] `build_cov_matrix()` — covarianza con ridge regularización
- [x] `align_mu_sigma()` — retornos esperados ajustados con lambda_adj
- [x] `max_sharpe()` — optimización con sigma cap (riesgo controlado)
- [x] `compute_quantities()` — cantidades enteras por presupuesto
- [x] `save_portfolio()` / `list_portfolios()` — memoria JSON

#### `main.py`
- [x] `run_phase3_valuation()` — orquesta pipeline completo
- [x] `_write_phase3_excel()` — genera hojas de resultados
- [x] Actualizado a v0.3.0 en banner

### Entregables de Fase 3:
- [x] DCF para múltiples tickers sin romper
- [x] Tabla de ratios clara por ticker
- [x] Score de salud financiera 0-100
- [x] Hojas Excel: DCF_SALUD, SALUD_FINANCIERA
- [x] Flags y warnings en resultados
- [x] Fallbacks robustos en TODAS partes

### Verificación de Fase 3:
```bash
python main.py --demo    # corre Fase 2 y 3 sin errores
# Debe generar Excel con hojas DCF_SALUD y SALUD_FINANCIERA
```

---

## Fase 4 — PENDIENTE 🔲

**Objetivo:** Señales, régimen macro e incertidumbre

#### `src/sector_model.py`
- [ ] `find_knn_neighbors()` — vecinos históricos similares
- [ ] `knn_forward_returns()` — retornos de vecinos
- [ ] `train_logistic_models()` — modelos por (ticker, horizonte)
- [ ] `predict_probabilities()` — P(subida) por activo y horizonte
- [ ] `get_sector_signals()` — señales agregadas por sector

#### `src/market_regime.py`
- [ ] `classify_regime()` — régimen en múltiples dimensiones
- [ ] `get_favored_sectors()` — sectores favorecidos/presionados
- [ ] `compute_top_correlations()` — correlaciones features vs retornos
- [ ] `generate_executive_summary()` — texto en español

#### `src/uncertainty_engine.py`
- [ ] `compute_volatility_score()`
- [ ] `compute_knn_dispersion()`
- [ ] `compute_dcf_dispersion()`
- [ ] `compute_signal_contradiction()`
- [ ] `compute_market_stress()`
- [ ] `compute_data_quality_penalty()`
- [ ] `compute_uncertainty_score()` — compuesto final

#### `src/scoring_engine.py`
- [ ] `compute_fundamental_score()`
- [ ] `compute_market_score()`
- [ ] `compute_regime_fit_score()`
- [ ] `compute_composite_score()`
- [ ] `rank_universe()` — ranking final

#### `src/news_data.py` (si es confiable)
- [ ] `get_ticker_news()` — Yahoo Finance news
- [ ] `get_macro_news()` — Google News RSS
- [ ] `simple_sentiment()` — sentimiento básico con lexicón

### Entregables de Fase 4:
- [ ] Señales por horizonte (5d a 1Y)
- [ ] Score de incertidumbre por activo
- [ ] Lectura de régimen macro
- [ ] Sectores favorecidos y presionados
- [ ] Ranking de activos con score compuesto
- [ ] Hojas Excel: REGIMEN_MACRO, QUE_VA_A_SUBIR, QUE_VA_A_BAJAR, INCERTIDUMBRE, RANKING_ACTIVOS, SECTORES_*

---

## Fase 5 — PENDIENTE 🔲

**Objetivo:** Producto final usable

#### `src/excel_report.py`
- [ ] `create_excel_report()` — las 22 hojas completas
- [ ] Formato ejecutivo: colores, columnas auto-fit, tablas
- [ ] DASHBOARD_EJECUTIVO — resumen en 1 página
- [ ] SUPUESTOS_Y_FUENTES — documentación completa
- [ ] WARNINGS_Y_LIMITACIONES — transparencia del sistema

#### `tests/test_smoke.py`
- [ ] Test: config carga sin errores
- [ ] Test: módulos importan sin errores
- [ ] Test: main.py corre sin excepciones
- [ ] Test: Excel se genera
- [ ] Test: DCF para AAPL produce resultado razonable
- [ ] Test: portfolio con 3 tickers no explota

#### Documentación
- [ ] `README.md` completo con:
  - Instrucciones de instalación local
  - Instrucciones para Google Colab
  - Cómo cambiar tickers
  - Cómo cambiar moneda base
  - Cómo interpretar el Excel
  - Limitaciones conocidas

#### Limpieza final
- [ ] Verificar que requirements.txt está completo y con versiones
- [ ] Proponer archivado de scripts originales (usuario decide)
- [ ] Run completo con universo demo (8-10 tickers)
- [ ] Confirmar que usuario no técnico puede correrlo

---

## Deuda Técnica Conocida

| Ítem | Prioridad | Notas |
|------|-----------|-------|
| La segunda `main()` del script original es duplicado exacto | BAJA | Documentada, no migrar |
| `blended_erp_usd` necesita historial SPY de 30 años | MEDIA | Fallback a config si falla |
| kNN con N=150 puede ser lento con 30+ tickers | MEDIA | Investigar vectorización |
| FRED tiene límites de requests sin API key | BAJA | Documentar y añadir caché |
| Yahoo Finance puede cambiar su API sin previo aviso | ALTA | Abstracción en data_sources.py ayuda |

---

## Ideas Futuras (Post-Fase 5)

- [ ] Soporte para acciones mexicanas (BMV) con Yahoo Finance
- [ ] Dashboard web con Streamlit o Dash
- [ ] Alertas por email cuando una señal cambia
- [ ] Backtesting de las señales históricas
- [ ] Integración con brokers vía API
- [ ] Reporte en PDF además de Excel
