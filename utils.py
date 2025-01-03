# ARQUIVO UTILS.PY
# Este arquivo contém funções para calcular indicadores técnicos comuns, como SMA, EMA, RSI, MACD, Bandas de Bollinger, VWAP, etc.
# Também inclui funções para identificar sinais de entrada com base nos indicadores calculados.
# As funções são usadas em bot_trading.py para analisar os dados do mercado e gerar sinais de compra/venda.

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


def define_quantidade_tps(forca_do_sinal, volatility):
    """
    Define a quantidade de TPs a serem usados com base na força do sinal e na volatilidade.

    Args:
        forca_do_sinal (int): A força do sinal, calculada pela quantidade de indicadores.
        volatility (float): A volatilidade do ativo.

    Returns:
        int: A quantidade de TPs a serem usados.
    """
    if forca_do_sinal >= 7 and volatility >= 1.0:
        return 5  # Sinal muito forte e volatilidade alta: usar 5 TPs
    elif forca_do_sinal >= 5 and volatility >= 0.5:
        return 3  # Sinal forte e volatilidade moderada: usar 3 TPs
    elif forca_do_sinal >= 3:
        return 2  # Sinal moderado: usar 2 TPs
    else:
        return 1  # Sinal fraco ou volatilidade muito baixa: usar 1 TP


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

    # Adicionar outros padrões de candles aqui...

    return patterns


def define_quantidade_tps(forca_do_sinal, volatility, current_price, tps, sma_long):
    """
    Define a quantidade de TPs a serem usados com base na força do sinal,
    volatilidade, distância do TP e presença de suportes/resistências.

    Args:
        forca_do_sinal (int): A força do sinal.
        volatility (float): A volatilidade do ativo.
        current_price (float): Preço atual do ativo.
        tps (list): Lista de níveis de TP.
        sma_long (float): Média móvel de longo prazo.

    Returns:
        int: A quantidade de TPs a serem usados.
    """
    quantidade_tps = 1  # Quantidade mínima de TPs

    if forca_do_sinal >= 7 and volatility >= 1.0:
        quantidade_tps += 2  # Sinal muito forte e volatilidade alta

    if forca_do_sinal >= 5 and volatility >= 0.5:
        quantidade_tps += 1  # Sinal forte e volatilidade moderada

    # Ajustar a quantidade de TPs com base na distância do TP e suportes/resistências
    if tps:
        distancia_tp1 = abs(tps[0] - current_price)
        if distancia_tp1 > volatility * current_price * 0.05:  # TP1 distante
            quantidade_tps += 1
        if (
            sma_long and abs(tps[0] - sma_long) < distancia_tp1 * 0.5
        ):  # TP1 próximo de suporte/resistência
            quantidade_tps += 1

    return quantidade_tps


# Função para calcular os níveis de TP e SL com base na volatilidade e na média móvel de longo prazo
def calculate_tp_sl(prices, entry_type, volatility, candles, forca_do_sinal):
    """
    Calcula os níveis de TP e SL com base na volatilidade, ATR,
    força do sinal e presença de suportes/resistências.

    Args:
        prices (list): Lista de preços.
        entry_type (str): Tipo de entrada ("BUY/LONG" ou "SELL/SHORT").
        volatility (float): Volatilidade do ativo.
        candles (list): Lista de candles (OHLCV) no formato da Bybit.
        forca_do_sinal (int): Força do sinal.

    Returns:
        dict: Dicionário com os níveis de TP e SL.
    """
    current_price = prices[-1]
    high = np.array([float(candle["high"]) for candle in candles])
    low = np.array([float(candle["low"]) for candle in candles])
    close = np.array([float(candle["close"]) for candle in candles])

    # Calcular o ATR (Average True Range)
    atr = talib.ATR(high, low, close, timeperiod=14)[-1]

    # Calcular a média móvel de 200 períodos para identificar suporte e resistência
    period_sma_long = 200
    sma_long = calculate_sma(prices, period_sma_long)

    # Definir os multiplicadores do ATR para TP e SL com base na volatilidade
    if volatility < 0.5:
        tp_atr_multiplier = 1.5  # Volatilidade muito baixa
        sl_atr_multiplier = 0.5
    elif volatility < 1.0:
        tp_atr_multiplier = 2.0  # Volatilidade baixa
        sl_atr_multiplier = 1.0
    elif volatility < 2.0:
        tp_atr_multiplier = 2.5  # Volatilidade moderada
        sl_atr_multiplier = 1.5
    else:
        tp_atr_multiplier = 3.0  # Volatilidade alta
        sl_atr_multiplier = 2.0

    # Calcular a quantidade de TPs dinamicamente
    quantidade_tps = define_quantidade_tps(
        forca_do_sinal,
        volatility,
        current_price,
        [],
        sma_long[-1] if sma_long else None,
    )

    # Inicializar tps com o preço atual
    tps = [current_price]

    # Calcular os TPs
    for i in range(quantidade_tps):
        if entry_type == "BUY/LONG":
            tp = current_price + atr * tp_atr_multiplier * (i + 1)
        elif entry_type == "SELL/SHORT":
            tp = current_price - atr * tp_atr_multiplier * (i + 1)
        else:
            tp = current_price
        tps.append(tp)

    # Ajustar o TP se houver resistência/suporte próximo
    if entry_type == "BUY/LONG" and sma_long:
        for i in range(len(tps)):
            if tps[i] > sma_long[-1]:
                tps[i] = sma_long[-1]  # Define o TP na resistência
    elif entry_type == "SELL/SHORT" and sma_long:
        for i in range(len(tps)):
            if tps[i] < sma_long[-1]:
                tps[i] = sma_long[-1]  # Define o TP no suporte

    # Calcular o SL
    if entry_type == "BUY/LONG":
        sl = current_price - atr * sl_atr_multiplier
    elif entry_type == "SELL/SHORT":
        sl = current_price + atr * sl_atr_multiplier
    else:
        sl = current_price  # Caso "NEUTRO"

    return {"tps": tps, "sl": sl}


def identify_entries(
    prices,
    period_sma,
    period_ema,
    volumes,
    sma,
    ema,
    rsi,
    macd_line,
    macd_signal,
    upper_band,
    adx,
    stochastic_k,
    stochastic_d,
    lower_band,
    vwap,
    candles,
    rsi_threshold_long=30,
    rsi_threshold_short=70,
    long_term=False,
    active_signals=None,
):
    if active_signals is None:
        active_signals = []
    try:
        if len(prices) < period_sma:
            raise ValueError(
                "Número de preços insuficiente para calcular os indicadores."
            )

        current_price = prices[-1]

        # --- Sinais dos Indicadores ---
        try:  # Adicionar um try-except aninhado aqui
            signal_sma = current_price > sma[-1]
            signal_ema = current_price > ema[-1]
            signal_macd = macd_line[-1] > macd_signal
            signal_bollinger_lower = current_price < lower_band
            signal_bollinger_upper = current_price > upper_band
            signal_rsi_long = rsi < rsi_threshold_long
            signal_rsi_short = rsi > rsi_threshold_short
            signal_vwap = current_price > vwap[-1]
            signal_adx = adx[-1] > 25
            signal_stochastic_buy = (
                stochastic_k[-1] > stochastic_d[-1] and stochastic_k[-1] < 80
            )
            signal_stochastic_sell = (
                stochastic_k[-1] < stochastic_d[-1] and stochastic_k[-1] > 20
            )

            # Calcular a média do volume dos últimos 'period_sma' períodos
            media_volume = np.mean(volumes[-period_sma:])

            # Contagem de quantos sinais de compra ou venda estão ativos, considerando o volume para confirmar a força do sinal
            buy_signals_count = 0
            sell_signals_count = 0

            # --- SMA ---
            if signal_sma and volumes[-1] > media_volume:
                buy_signals_count += 2
            elif signal_sma:
                buy_signals_count += 1

            if not signal_sma and volumes[-1] > media_volume:
                sell_signals_count += 2
            elif not signal_sma:
                sell_signals_count += 1

            # --- EMA ---
            if signal_ema and volumes[-1] > media_volume:
                buy_signals_count += 2
            elif signal_ema:
                buy_signals_count += 1

            if not signal_ema and volumes[-1] > media_volume:
                sell_signals_count += 2
            elif not signal_ema:
                sell_signals_count += 1

            # --- MACD ---
            if signal_macd and volumes[-1] > media_volume:
                buy_signals_count += 2
            elif signal_macd:
                buy_signals_count += 1

            if not signal_macd and volumes[-1] > media_volume:
                sell_signals_count += 2
            elif not signal_macd:
                sell_signals_count += 1

            # --- Bollinger ---
            if signal_bollinger_lower and volumes[-1] > media_volume:
                buy_signals_count += 2
            elif signal_bollinger_lower:
                buy_signals_count += 1

            if signal_bollinger_upper and volumes[-1] > media_volume:
                sell_signals_count += 2
            elif signal_bollinger_upper:
                sell_signals_count += 1

            # --- VWAP ---
            if signal_vwap and volumes[-1] > media_volume:
                buy_signals_count += 2
            elif signal_vwap:
                buy_signals_count += 1

            if not signal_vwap and volumes[-1] > media_volume:
                sell_signals_count += 2
            elif not signal_vwap:
                sell_signals_count += 1

            # --- ADX ---
            if signal_adx and volumes[-1] > media_volume:
                buy_signals_count += 2
            elif signal_adx:
                buy_signals_count += 1

            if not signal_adx and volumes[-1] > media_volume:
                sell_signals_count += 2
            elif not signal_adx:
                sell_signals_count += 1

            # --- Estocástico ---
            if signal_stochastic_buy and volumes[-1] > media_volume:
                buy_signals_count += 2
            elif signal_stochastic_buy:
                buy_signals_count += 1

            if signal_stochastic_sell and volumes[-1] > media_volume:
                sell_signals_count += 2
            elif signal_stochastic_sell:
                sell_signals_count += 1

            # Inicializa entry_type como "No Signal"
            entry_type = "No Signal"

            # Calcula a volatilidade
            volatility = calculate_volatility(prices)

            # --- active_signals ---
            active_signals = []
            if signal_sma:
                active_signals.append(f"SMA: Preço cruzou a SMA de baixo para cima.")
            if signal_ema:
                active_signals.append(f"EMA: Preço cruzou a EMA de baixo para cima.")
            if signal_macd:
                active_signals.append("MACD: MACD cruzou o sinal de baixo para cima.")
            if signal_bollinger_lower:
                active_signals.append(
                    "Bollinger: Preço rompeu a banda inferior de Bollinger."
                )
            if signal_bollinger_upper:
                active_signals.append(
                    "Bollinger: Preço rompeu a banda superior de Bollinger."
                )
            if signal_vwap:
                active_signals.append("VWAP: Preço está acima do VWAP.")
            if signal_adx:
                active_signals.append("ADX: Sinal forte")
            if signal_stochastic_buy:
                active_signals.append("Estocástico: Cruzamento de compra")
            if signal_stochastic_sell:
                active_signals.append("Estocástico: Cruzamento de venda")

            # Calcular a força do sinal
            forca_do_sinal = buy_signals_count + sell_signals_count

            # --- Lógica de decisão para compra/venda ---
            if buy_signals_count > 5 and (
                signal_rsi_long or long_term
            ):  # Usar RSI para long_term
                entry_type = "BUY/LONG"
                tp_sl_levels = calculate_tp_sl(
                    prices, entry_type, volatility, candles, forca_do_sinal
                )

            elif sell_signals_count > 5 and (
                signal_rsi_short or long_term
            ):  # Usar RSI para long_term
                entry_type = "SELL/SHORT"
                tp_sl_levels = calculate_tp_sl(
                    prices, entry_type, volatility, candles, forca_do_sinal
                )

            else:
                entry_type = "NEUTRO"
                tp_sl_levels = {
                    "tps": [
                        current_price
                    ],  # Retornar uma lista com o preço atual para tps
                    "sl": current_price,
                }

            # Adicionar mensagem padrão se não houver sinais
            if not active_signals:
                active_signals.append("Nenhum sinal detectado.")

            return {  # Retornar o dicionário final aqui
                "entry_type": entry_type,
                "tps": tp_sl_levels[
                    "tps"
                ],  # Corrigido: usar "tps" em vez de "tp1", "tp2", "tp3"
                "sl": tp_sl_levels["sl"],
                "active_signals": active_signals,
            }

        except Exception as inner_e:  # Capturar exceções internas
            print(f"Erro interno ao identificar entradas: {inner_e}")
            return {
                "entry_type": "NEUTRO",
                "tps": [],
                "sl": None,
                "active_signals": [f"Erro interno ao identificar entradas: {inner_e}"],
            }

    except Exception as e:  # Capturar exceções gerais
        print(f"Error identifying entries: {e}")
        return {
            "entry_type": "ERRO",
            "tps": [],
            "sl": None,
            "active_signals": [f"Erro ao identificar entradas: {e}"],
        }
