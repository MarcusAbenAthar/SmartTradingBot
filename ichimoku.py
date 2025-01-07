# Arquivo ichimoku.py
# Este arquivo contém uma função para calcular as linhas do Ichimoku Cloud.

import numpy as np
import talib


def calculate_ichimoku(high_prices, low_prices):
    """
    Calcula as linhas do Ichimoku Cloud.

    Args:
      high_prices: Lista de preços máximos das velas.
      low_prices: Lista de preços mínimos das velas.

    Returns:
      Um dicionário com as linhas do Ichimoku Cloud:
        - tenkan_sen: Média móvel de 9 períodos.
        - kijun_sen: Média móvel de 26 períodos.
        - senkou_span_a: Média da Tenkan-sen e Kijun-sen, projetada 26 períodos à frente.
        - senkou_span_b: Média móvel de 52 períodos, projetada 26 períodos à frente.
        - chikou_span: Preço de fechamento atual, projetado 26 períodos para trás.
    """

    # Tenkan-sen (Conversion Line): Média móvel de 9 períodos
    tenkan_sen = talib.SMA(np.array(high_prices + low_prices) / 2, timeperiod=9)

    # Kijun-sen (Base Line): Média móvel de 26 períodos
    kijun_sen = talib.SMA(np.array(high_prices + low_prices) / 2, timeperiod=26)

    # Senkou Span A (Leading Span A): Média da Tenkan-sen e Kijun-sen, projetada 26 períodos à frente
    senkou_span_a = (tenkan_sen + kijun_sen) / 2
    senkou_span_a = np.roll(senkou_span_a, 26)

    # Senkou Span B (Leading Span B): Média móvel de 52 períodos, projetada 26 períodos à frente
    senkou_span_b = talib.SMA(np.array(high_prices + low_prices) / 2, timeperiod=52)
    senkou_span_b = np.roll(senkou_span_b, 26)

    # Chikou Span (Lagging Span): Preço de fechamento atual, projetado 26 períodos para trás
    chikou_span = np.roll(np.array(low_prices), -26)

    return {
        "tenkan_sen": tenkan_sen,
        "kijun_sen": kijun_sen,
        "senkou_span_a": senkou_span_a,
        "senkou_span_b": senkou_span_b,
        "chikou_span": chikou_span,
    }
