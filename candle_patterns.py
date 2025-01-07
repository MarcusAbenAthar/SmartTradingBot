# Arquivo candle_patterns.py
# Este arquivo contém funções para identificar padrões de candles.
# Padrões atualmente suportados:
# Engolfo de Alta, Engolfo de Baixa, Martelo e Estrela Cadente.

import numpy as np
import talib

# Função para identificar padrões de candles


def identify_candle_patterns(candles):
    """
    Identifica padrões de candles.

    Args:
        candles (list): Lista de candles (OHLCV) no formato da Bybit.

    Returns:
        list: Lista de strings com os padrões de candles identificados.
    """
    patterns = []
    high = np.array([float(candle["high"]) for candle in candles])
    low = np.array([float(candle["low"]) for candle in candles])
    close = np.array([float(candle["close"]) for candle in candles])
    open_ = np.array([float(candle["open"]) for candle in candles])

    # Identificar Engolfo de Alta
    if talib.CDLENGULFING(open_, high, low, close)[-1] > 0:
        patterns.append("Engolfo de Alta")

    # Identificar Engolfo de Baixa
    if talib.CDLENGULFING(open_, high, low, close)[-1] < 0:
        patterns.append("Engolfo de Baixa")

    # Identificar Martelo
    if talib.CDLHAMMER(open_, high, low, close)[-1] > 0:
        patterns.append("Martelo")

    # Identificar Estrela Cadente
    if talib.CDLSHOOTINGSTAR(open_, high, low, close)[-1] < 0:
        patterns.append("Estrela Cadente")

    return patterns
