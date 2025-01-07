# Arquivo indicatos.py
# Descrição: Este arquivo contém funções para calcular indicadores técnicos.
# Indicadores atualmente suportados:
# SMA, EMA, MACD, RSI, Bandas de Bollinger, Volatilidade, VWAP, ADX e Estocástico.


import numpy as np
import talib

# Função para calcular a média móvel simples (SMA)


def calculate_sma(prices, period):
    if len(prices) < period:
        # Retorna a média de todos os preços disponíveis
        return [sum(prices) / len(prices)] * len(prices) if len(prices) > 0 else []
    sma = [
        sum(prices[i : i + period]) / period for i in range(len(prices) - period + 1)
    ]
    return sma


# Função para calcular a Média Móvel Exponencial (EMA)
def calculate_ema(prices, period):
    if len(prices) < period:
        # Retorna a média de todos os preços disponíveis
        return [sum(prices) / len(prices)] * len(prices) if len(prices) > 0 else []
    ema = [prices[0]]
    k = 2 / (period + 1)
    for i in range(1, len(prices)):
        ema.append(prices[i] * k + ema[i - 1] * (1 - k))
    return ema


# Função para calcular o MACD
def calculate_macd(prices, fast_period=12, slow_period=26, signal_period=9):
    if len(prices) < slow_period:
        return [np.nan] * len(prices), np.nan

    ema_fast = calculate_ema(prices, fast_period)
    ema_slow = calculate_ema(prices, slow_period)

    macd_line = np.subtract(ema_fast, ema_slow)

    # Ajustar o período do sinal se for maior que o comprimento da linha MACD
    adjusted_signal_period = min(signal_period, len(macd_line))
    if adjusted_signal_period > 0:
        signal_line = calculate_ema(macd_line, adjusted_signal_period)[-1]
    else:
        signal_line = np.nan

    return macd_line, signal_line


# Função para calcular o RSI
def calculate_rsi(prices, period):
    if len(prices) < period:
        # Retorna um valor neutro quando não há dados suficientes
        return [50.0] * len(prices) if len(prices) > 0 else []

    gains = []
    losses = []

    for i in range(1, len(prices)):
        delta = prices[i] - prices[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))

    avg_gain = (
        sum(gains[:period]) / period
        if len(gains) >= period
        else sum(gains) / len(gains) if len(gains) > 0 else 0
    )
    avg_loss = (
        sum(losses[:period]) / period
        if len(losses) >= period
        else sum(losses) / len(losses) if len(losses) > 0 else 0
    )

    # Evitar divisão por zero
    if avg_loss == 0:
        if avg_gain == 0:
            return [50.0] * len(
                prices
            )  # Retorna neutro se não houver ganhos nem perdas
        else:
            return [100.0] * len(prices)  # Retorna 100 se houver ganhos e nenhuma perda

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return [rsi] * len(
        prices
    )  # Retorna uma lista com o mesmo valor para manter a consistência


# Função para calcular as Bandas de Bollinger
def calculate_bollinger_bands(prices, period=20, std_dev=2):
    if len(prices) < period:
        # Retorna valores que não afetam a análise quando não há dados suficientes
        return [np.nan] * len(prices), [np.nan] * len(prices)
    sma = calculate_sma(prices, period)
    std = np.std(prices[-period:])
    upper_band = sma[-1] + std * std_dev
    lower_band = sma[-1] - std * std_dev
    return upper_band, lower_band


# Função para calcular a volatilidade
def calculate_volatility(prices):
    return np.std(prices)


def calculate_vwap(prices, volumes, period=20):
    if len(prices) < period or len(volumes) < period:
        # Retorna valores que não afetam a análise quando não há dados suficientes
        return [np.nan] * len(prices)

    vwap_values = []
    for i in range(period - 1, len(prices)):
        pv = [prices[j] * volumes[j] for j in range(i - period + 1, i + 1)]
        soma_volumes = sum(volumes[i - period + 1 : i + 1])
        if soma_volumes != 0:  # Verificar se a soma dos volumes é diferente de zero
            vwap = sum(pv) / soma_volumes
        else:
            vwap = np.nan  # Ou defina outro valor padrão, como 0
        vwap_values.append(vwap)

    return vwap_values


def calculate_adx(candles, period=14):
    """
    Calcula o Average Directional Index (ADX).

    Args:
        candles (list): Lista de candles (OHLCV) no formato da Bybit.
        period (int, optional): Período do ADX. Defaults to 14.

    Returns:
        np.array: Array com os valores do ADX.
    """
    high = np.array([float(candle["high"]) for candle in candles])
    low = np.array([float(candle["low"]) for candle in candles])
    close = np.array([float(candle["close"]) for candle in candles])
    adx = talib.ADX(high, low, close, timeperiod=period)
    return adx


def calculate_stochastic(candles, period=14):
    """
    Calcula o Estocástico.

    Args:
        candles (list): Lista de candles (OHLCV) no formato da Bybit.
        period (int, optional): Período do Estocástico. Defaults to 14.

    Returns:
        tuple: Tupla contendo dois arrays numpy, com os valores do %K e %D.
    """
    high = np.array([float(candle["high"]) for candle in candles])
    low = np.array([float(candle["low"]) for candle in candles])
    close = np.array([float(candle["close"]) for candle in candles])
    slowk, slowd = talib.STOCH(
        high,
        low,
        close,
        fastk_period=period,
        slowk_period=3,
        slowk_matype=0,
        slowd_period=3,
        slowd_matype=0,
    )
    return slowk, slowd
