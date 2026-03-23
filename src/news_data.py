# -*- coding: utf-8 -*-
"""
src/news_data.py — Noticias y sentimiento de mercado

Capa ligera de noticias/sentimiento para enriquecer el análisis.

ESTADO ACTUAL: STUB — INFRAESTRUCTURA LISTA, PENDIENTE FASE 4

Diseño deliberadamente conservador:
  - Solo fuentes gratuitas y confiables
  - Si la fuente no es confiable, marca baja_confianza=True
  - Sin alucinaciones ni storytelling falso
  - Si no hay datos, devuelve None + warning, no inventa

Fuentes planeadas (Fase 4):
  - Yahoo Finance news (via yfinance)
  - Google News RSS (gratuito, sin API key)
  - FRED release calendar (para eventos macro)

Lo que NO haremos:
  - Scraping agresivo
  - APIs de pago no configuradas por el usuario
  - Análisis de sentimiento sin fuente verificable
  - "Predicciones" basadas en noticias sin score de confianza

Estado: STUB — implementación en Fase 4
"""

import logging
from typing import Dict, List, Optional

import pandas as pd

log = logging.getLogger(__name__)


def get_ticker_news(
    ticker: str,
    n_articles: int = 5,
) -> List[Dict]:
    """Obtiene noticias recientes para un ticker desde Yahoo Finance.

    Args:
        ticker: Símbolo bursátil.
        n_articles: Máximo de artículos a devolver.

    Returns:
        Lista de dicts con campos:
          - title: Título del artículo
          - publisher: Fuente
          - link: URL
          - providerPublishTime: Timestamp
          - baja_confianza: True si la fuente es desconocida
        Lista vacía si no hay noticias o si falla la descarga.

    TODO (Fase 4): Implementar con yf.Ticker.news.
    """
    log.warning("news_data.get_ticker_news: módulo no implementado aún (Fase 4). Devolviendo [].")
    return []


def get_macro_news(n_articles: int = 10) -> List[Dict]:
    """Obtiene noticias macro recientes (Fed, inflación, economía).

    Args:
        n_articles: Máximo de artículos.

    Returns:
        Lista de dicts similar a get_ticker_news().

    TODO (Fase 4): Implementar con Google News RSS.
    """
    log.warning("news_data.get_macro_news: módulo no implementado aún (Fase 4). Devolviendo [].")
    return []


def simple_sentiment(text: str) -> Optional[Dict]:
    """Análisis de sentimiento simple sin modelo externo.

    Usa conteo de palabras positivas/negativas de un lexicón básico.
    No usa LLMs ni APIs externas — solo lexicón hardcodeado.

    Args:
        text: Texto a analizar (título de noticia, párrafo).

    Returns:
        Dict con:
          - sentiment: 'positivo', 'negativo', 'neutral'
          - score: -1.0 a 1.0
          - baja_confianza: True (siempre, dado el método simple)
        None si el texto está vacío.

    TODO (Fase 4): Implementar.
    """
    if not text or not text.strip():
        return None
    log.warning("news_data.simple_sentiment: módulo no implementado aún (Fase 4).")
    return None
