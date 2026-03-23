# Arquitectura del Sistema Cuantitativo Unificado

**Versión:** 0.1.0
**Fecha:** 2026-03-23
**Estado:** Fase 1 completada

---

## Visión General

El sistema fusiona dos scripts originales (Colab) en una arquitectura modular, profesional y ejecutable que permite:

1. **Análisis macro** del entorno (tasas, inflación, curva de bonos, FX, commodities)
2. **Valuación fundamental** de acciones/ETF (DCF, FCFF, WACC, beta)
3. **Señales de mercado** por horizonte (5d, 10d, 15d, 30d, 3M, 6M, 1Y)
4. **Salud financiera** (ratios, flags de fragilidad)
5. **Portafolio óptimo** (Max Sharpe con restricciones)
6. **Reporting ejecutivo** en Excel profesional en español

---

## Principios de Diseño

| Principio | Implementación |
|-----------|---------------|
| **Sin `input()`** | Todo desde `config.yml` |
| **Sin `!pip` en código** | Solo `requirements.txt` |
| **Modularidad** | Un módulo = una responsabilidad |
| **Trazabilidad** | Cada métrica documenta su fuente |
| **Resiliencia** | Fallos de un ticker no rompen el resto |
| **Configurabilidad** | Un solo archivo para cambiar todo |
| **Bilingüe** | Código en inglés, outputs en español |

---

## Estructura de Archivos

```
UMPALUMPA-ULTRA-MEJORADO-CON-CLAUD/
│
├── main.py                     ← Punto de entrada único
├── config.example.yml          ← Plantilla de configuración (editar y renombrar a config.yml)
├── config.yml                  ← Configuración activa (gitignored)
├── requirements.txt            ← Dependencias Python
├── architecture.md             ← Este archivo
├── CHANGELOG.md                ← Historial de cambios
├── TODO.md                     ← Roadmap y tareas pendientes
│
├── src/                        ← Código modular del sistema
│   ├── __init__.py
│   ├── config_loader.py        ← Carga config.yml + defaults + validación
│   ├── utils.py                ← Helpers: normalización, sanitización, NaN
│   │
│   ├── data_sources.py         ← Descarga cruda de Yahoo Finance y FRED
│   ├── market_data.py          ← Precios, sectores, ETFs (nivel intermedio)
│   ├── macro_data.py           ← Tasas, inflación, curva bonos, FX, commodities
│   ├── news_data.py            ← Noticias y sentimiento (Fase 4)
│   │
│   ├── feature_engineering.py  ← Construcción de features para modelos
│   ├── risk_country_fx.py      ← Risk-free rate, ERP, conversión FX
│   │
│   ├── valuation_dcf.py        ← DCF/FCFF, WACC, beta, escenarios
│   ├── financial_health.py     ← Ratios, liquidez, apalancamiento, flags
│   │
│   ├── sector_model.py         ← kNN + regresión logística por sector/horizonte
│   ├── market_regime.py        ← Clasificación del régimen macro
│   ├── uncertainty_engine.py   ← Score de incertidumbre compuesto
│   ├── scoring_engine.py       ← Score final y ranking de activos
│   │
│   ├── portfolio_optimizer.py  ← Max Sharpe, covarianza, cantidades
│   └── excel_report.py         ← Generador del Excel ejecutivo
│
├── outputs/                    ← Archivos generados (Excel, caché, logs)
│   └── cache/
│
└── tests/
    ├── __init__.py
    └── test_smoke.py           ← Tests de humo básicos
```

---

## Flujo de Datos

```
config.yml
    │
    ▼
config_loader.py ──────────────────────────────────────────┐
    │                                                       │
    ├─→ data_sources.py ──→ market_data.py                 │
    │         │              │                              │
    │         └──→ macro_data.py ──→ feature_engineering.py│
    │                                    │                  │
    │                                    ▼                  │
    │                             sector_model.py           │
    │                             market_regime.py          │
    │                                    │                  │
    ├─→ risk_country_fx.py ──────────────┤                  │
    │         │                          │                  │
    │         ▼                          │                  │
    │   valuation_dcf.py                 │                  │
    │         │                          │                  │
    │         ▼                          │                  │
    │   financial_health.py              │                  │
    │         │                          │                  │
    │         └──────────────────────────┼──────────────────┤
    │                                    ▼                  │
    │                          uncertainty_engine.py        │
    │                                    │                  │
    │                                    ▼                  │
    │                           scoring_engine.py           │
    │                                    │                  │
    ├─→ portfolio_optimizer.py           │                  │
    │         │                          │                  │
    │         └──────────────────────────┼──────────────────┘
    │                                    ▼
    └─────────────────────────→ excel_report.py ──→ outputs/Excel
```

---

## Módulos: Descripción y Responsabilidades

### `config_loader.py`
- **Responsabilidad**: Única fuente de verdad para configuración
- **Origen**: Rescatado de `umpa_ultra_mejorado_2_0_15_01_2026.py` (load_config)
- **Expone**: `CFG` singleton, `get_tickers()`, `get_country_rf_erp()`, `get_etr_cap()`
- **Sin input()**: Todos los parámetros del sistema vienen de aquí

### `data_sources.py`
- **Responsabilidad**: TODA la comunicación con APIs externas (Yahoo, FRED)
- **Origen**: Rescatado de `que_va_a_pasar_en_el_mercado_.py` (líneas 94-276)
- **Diseño**: El resto del sistema NUNCA llama a yfinance o pdr directamente
- **Resiliencia**: Fallbacks por ticker, warnings claros, no rompe en fallo

### `market_data.py`
- **Responsabilidad**: Precios limpios y metadata de activos
- **Usa**: `data_sources.py` para descargas, `config_loader.py` para parámetros

### `macro_data.py`
- **Responsabilidad**: Series macro (tasas, inflación, spreads, FX, commodities)
- **Origen**: Rescatado de `que_va_a_pasar_en_el_mercado_.py` (FRED + Yahoo macro)
- **Catálogo**: `FRED_SERIES` y `YAHOO_MACRO` documentan qué se descarga y de dónde

### `feature_engineering.py`
- **Responsabilidad**: Construir features para modelos ML
- **Origen**: Rescatado de `que_va_a_pasar_en_el_mercado_.py` (yoy_from_level, delta)
- **Output**: DataFrame normalizado de features listo para kNN y logística

### `risk_country_fx.py`
- **Responsabilidad**: Risk-free rate, ERP, conversión FX
- **Origen**: Rescatado de `umpa_ultra_mejorado_2_0_15_01_2026.py` (líneas 129-495)
- **Sin input()**: Para no-USD lee de `config.risk.country_rates`

### `valuation_dcf.py`
- **Responsabilidad**: Valuación fundamental completa
- **Origen**: Rescatado de `umpa_ultra_mejorado_2_0_15_01_2026.py` (líneas 158-996)
- **Métodos**: DCF/FCFF (industriales), DDM (financieros), Proxy (ETFs)
- **Escenarios**: Bear / Base / Bull automáticamente

### `financial_health.py`
- **Responsabilidad**: Ratios y flags de salud financiera
- **Nuevo**: No existía como módulo separado — extraído de la lógica de valuación
- **Health Score**: 0-100, combina liquidez + apalancamiento + cobertura + calidad

### `sector_model.py`
- **Responsabilidad**: Modelos kNN y logística para señales de mercado
- **Origen**: Rescatado de `que_va_a_pasar_en_el_mercado_.py` (líneas 513-640)
- **Expandido**: De solo 5d → a 5d, 10d, 15d, 30d, 3M, 6M, 1Y

### `market_regime.py`
- **Responsabilidad**: Clasificar el régimen macro y sus implicaciones sectoriales
- **Origen**: Rescatado de `que_va_a_pasar_en_el_mercado_.py` (correlaciones, conclusiones)
- **Output**: Régimen en N dimensiones + sectores favorecidos/presionados

### `uncertainty_engine.py`
- **Responsabilidad**: Cuantificar incertidumbre de forma transparente
- **Nuevo**: No existía en los scripts originales
- **Score**: 0-100 compuesto de 6 fuentes distintas

### `portfolio_optimizer.py`
- **Responsabilidad**: Optimización Max Sharpe y cálculo de cantidades
- **Origen**: Rescatado de `umpa_ultra_mejorado_2_0_15_01_2026.py` (líneas 1011-1791)
- **Sin input()**: budget, risk_multiplier, fixed_weights vienen de config

### `scoring_engine.py`
- **Responsabilidad**: Score final compuesto y ranking del universo
- **Nuevo**: Integrador — combina fundamental + mercado + régimen + incertidumbre
- **Output**: Ranking ejecutivo con atractivo, convicción y riesgo por activo

### `excel_report.py`
- **Responsabilidad**: Generar el Excel ejecutivo completo
- **22 hojas**: Desde dashboard ejecutivo hasta datos crudos
- **Idioma**: Español en etiquetas, números y textos explicativos

---

## Mapeo de `input()` Eliminados

Todos los `input()` del sistema original se reemplazan con `config.yml`:

| input() original | Parámetro config.yml |
|-----------------|----------------------|
| Tickers (líneas 1042, 1331) | `tickers:` lista |
| Moneda valuación (1046, 1335) | `valuation_currency:` |
| Años históricos (1048, 1337) | `portfolio.years_history:` |
| Risk multiplier (1049, 1338) | `portfolio.risk_multiplier:` |
| Budget min/max (1050-51, 1339-40) | `portfolio.budget_min/max:` |
| NA threshold (1052, 1341) | `portfolio.na_threshold:` |
| Lambda (1053, 1342) | `portfolio.lambda_adj:` |
| Fixed weights JSON (1057, 1345) | `portfolio.fixed_weights:` |
| ERP para USD (484) | `risk.erp_fallback:` |
| RF/ERP no-USD (490-491) | `risk.country_rates.{CCY}.rf/erp:` |

---

## Fuentes de Datos

| Fuente | Datos | Módulo responsable |
|--------|-------|-------------------|
| Yahoo Finance | Precios, dividendos, estados financieros, FX | `data_sources.py` |
| FRED | Tasas EUA, inflación, condiciones financieras | `data_sources.py` |
| Config.yml | RF/ERP no-USD, parámetros DCF | `config_loader.py` |
| Calculado | Beta, WACC, ERP blended, ratios | Módulos respectivos |

---

## Compatibilidad

| Entorno | Soporte | Instrucciones |
|---------|---------|---------------|
| Python local | ✓ Completo | `pip install -r requirements.txt && python main.py` |
| Google Colab | ✓ Completo | `!pip install -r requirements.txt` luego `!python main.py` |
| Windows | ✓ Con Python 3.8+ | Mismo proceso |
| Mac/Linux | ✓ Nativo | Mismo proceso |

---

## Decisiones de Diseño

### ¿Por qué no un solo archivo grande?
Los scripts originales tenían 717 y 1,894 líneas. Son difíciles de mantener,
imposibles de testear en partes, y cualquier cambio puede romper todo.
La arquitectura modular permite actualizar un módulo sin tocar los demás.

### ¿Por qué `data_sources.py` separado de `market_data.py`?
`data_sources.py` es la **capa de protocolo** (HTTP requests, parseo de respuestas).
`market_data.py` es la **capa de negocio** (qué datos necesita el sistema y cómo limpiarlos).
Cambiar de Yahoo Finance a Bloomberg solo requiere tocar `data_sources.py`.

### ¿Por qué `config.yml` en lugar de `.env`?
`.env` es adecuado para secretos (API keys). `config.yml` es mejor para
parámetros numéricos con estructura jerárquica (portafolio, DCF, horizontes).
El sistema usa ambos: config.yml para parámetros, opcionalmente .env para FRED API key.

### ¿Por qué dos main() en el original y cómo se resuelve?
El archivo original tenía dos funciones `main()` (líneas 1039 y 1328) con lógica
casi idéntica — probablemente por copiar-pegar durante el desarrollo.
En el nuevo sistema hay exactamente un `main.py` que delega a los módulos.
