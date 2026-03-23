# TODO — Roadmap del Sistema Cuantitativo Unificado

**Última actualización:** 2026-03-23

---

## Estado General por Fase

| Fase | Estado | Descripción |
|------|--------|-------------|
| Fase 1 | ✅ COMPLETADA | Auditoría, diseño y esqueleto |
| Fase 2 | 🔲 PENDIENTE | Datos, configuración y capa macro/mercado |
| Fase 3 | 🔲 PENDIENTE | Valuación y salud financiera |
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

## Fase 2 — PENDIENTE 🔲

**Objetivo:** Capa confiable de descarga y limpieza de datos

### Módulos a implementar:

#### `src/data_sources.py`
- [ ] `download_prices_yahoo()` — precios con fallbacks por ticker
- [ ] `download_universe_with_fallbacks()` — universo con alternativas
- [ ] `fred_get_series()` — serie individual de FRED
- [ ] `fred_get_multiple()` — múltiples series con fallbacks
- [ ] `get_fx_spot()` — tipo de cambio spot
- [ ] `get_fx_series()` — serie histórica FX con inversión automática
- [ ] `get_risk_free_usd()` — UST10Y desde FRED → Yahoo → config

#### `src/market_data.py`
- [ ] `get_prices()` — precios limpios, convertidos a moneda base
- [ ] `get_sector_etf_prices()` — 11 ETFs de sector
- [ ] `get_ticker_info()` — metadata: sector, país, industria, moneda
- [ ] `get_returns()` — retornos en frecuencia configurable

#### `src/macro_data.py`
- [ ] `download_all_macro()` — todas las series FRED + Yahoo macro
- [ ] `build_yield_curve()` — estructura temporal de tasas
- [ ] `get_yield_curve_today()` — curva actual puntual
- [ ] `get_spread_2y10y()` — spread 10Y-2Y histórico

#### `src/feature_engineering.py`
- [ ] `yoy_change()` — cambio YoY de niveles (inflación)
- [ ] `rolling_delta()` — cambio en ventana N (momentum de tasas)
- [ ] `build_macro_features()` — DataFrame de features para modelos
- [ ] `build_forward_returns()` — retornos futuros (labels)

#### `src/risk_country_fx.py`
- [ ] `get_risk_free_usd()` — FRED → Yahoo → config fallback
- [ ] `blended_erp_usd()` — ERP de SPY 5/10/30Y
- [ ] `get_rf_erp()` — rf + erp para cualquier moneda (sin input())
- [ ] `fx_spot()` — tipo de cambio spot
- [ ] `get_fx_series()` — historial FX con inversión automática

### Entregables de Fase 2:
- [ ] `main.py --fase2` corre descarga con 3-5 tickers demo
- [ ] Imprime resumen de series descargadas
- [ ] No truena si falta una serie
- [ ] Primera hoja real en Excel: TASAS_EUA_MX
- [ ] Log claro de fuentes de datos

---

## Fase 3 — PENDIENTE 🔲

**Objetivo:** Motor DCF y salud financiera operativos

#### `src/valuation_dcf.py`
- [ ] `extract_financial_data()` — estados financieros robustos
- [ ] `compute_beta()` — beta semanal con winsorización y R²
- [ ] `compute_wacc()` — WACC con pesos de mercado
- [ ] `dcf_valuation()` — DCF completo con escenarios
- [ ] `run_dcf_universe()` — DCF para lista de tickers

#### `src/financial_health.py`
- [ ] `compute_ratios()` — todos los ratios contables
- [ ] `compute_health_score()` — score 0-100
- [ ] `detect_financial_flags()` — flags de riesgo
- [ ] `run_health_universe()` — para lista de tickers

#### `src/portfolio_optimizer.py`
- [ ] `build_cov_matrix()` — covarianza con ridge regularización
- [ ] `align_mu_sigma()` — retornos esperados ajustados
- [ ] `max_sharpe()` — optimización con sigma cap
- [ ] `compute_quantities()` — cantidades enteras por presupuesto
- [ ] `save_portfolio()` / `list_portfolios()` — memoria JSON

### Entregables de Fase 3:
- [ ] DCF para 3 tickers sin romper
- [ ] Tabla de ratios clara por ticker
- [ ] Score preliminar de atractivo fundamental
- [ ] Hojas Excel: DCF_VALUATION, RATIOS_FINANCIEROS, CALIDAD_FINANCIERA
- [ ] Hojas Excel: PORTAFOLIO_OPTIMO, PORTAFOLIO_CANTIDADES

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
