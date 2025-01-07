# Arquivo trading_logic.py
# Este arquivo contém a lógica de negociação para identificar oportunidades de entrada.


from indicators import calculate_sma, calculate_volatility
import numpy as np
import talib


def identify_entries(
    prices,
    period_sma,
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
    ichimoku,
    rsi_threshold_long=30,
    rsi_threshold_short=70,
    long_term=False,
    active_signals=None,
):
    """
    Identifica oportunidades de entrada com base em indicadores técnicos, padrões de candles e Ichimoku Cloud.

    Args:
        prices (list): Lista de preços do ativo.
        period_sma (int): Período da média móvel simples (SMA).
        volumes (list): Lista de volumes do ativo.
        sma (list): Lista de valores da SMA.
        ema (list): Lista de valores da EMA.
        rsi (float): Valor atual do RSI.
        macd_line (list): Lista de valores da linha MACD.
        macd_signal (list): Lista de valores da linha de sinal do MACD.
        upper_band (list): Lista de valores da banda superior do Bollinger Bands.
        adx (list): Lista de valores do ADX.
        stochastic_k (list): Lista de valores do estocástico %K.
        stochastic_d (list): Lista de valores do estocástico %D.
        lower_band (list): Lista de valores da banda inferior do Bollinger Bands.
        vwap (list): Lista de valores do VWAP.
        candles (list): Lista de candles (OHLCV) no formato da Bybit.
        ichimoku (dict): Dicionário com as linhas do Ichimoku Cloud.
        rsi_threshold_long (int, optional): Limiar do RSI para compra (long). Defaults to 30.
        rsi_threshold_short (int, optional): Limiar do RSI para venda (short). Defaults to 70.
        long_term (bool, optional): Indica se a análise é de longo prazo. Defaults to False.
        active_signals (list, optional): Lista de sinais ativos. Defaults to None.

    Returns:
        dict: Um dicionário com o tipo de entrada, os níveis de TP e SL e os sinais ativos.
    """

    if active_signals is None:
        active_signals = []
    try:
        if len(prices) < period_sma:
            raise ValueError(
                "Número de preços insuficiente para calcular os indicadores."
            )

        current_price = prices[-1]

        # --- Sinais dos Indicadores ---
        try:
            signal_sma = current_price > sma[-1]
            signal_ema = current_price > ema[-1]
            signal_macd = macd_line[-1] > macd_signal[-1]
            signal_bollinger_lower = current_price < lower_band[-1]
            signal_bollinger_upper = current_price > upper_band[-1]
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

            # --- Ichimoku Cloud ---
            signal_ichimoku_tenkan_kijun = (
                ichimoku["tenkan_sen"][-1] > ichimoku["kijun_sen"][-1]
            )
            signal_ichimoku_price_above_cloud = (
                current_price > ichimoku["senkou_span_a"][-1]
                and current_price > ichimoku["senkou_span_b"][-1]
            )

            if (
                signal_ichimoku_tenkan_kijun
                and signal_ichimoku_price_above_cloud
                and volumes[-1] > media_volume
            ):
                buy_signals_count += 2
            elif signal_ichimoku_tenkan_kijun and signal_ichimoku_price_above_cloud:
                buy_signals_count += 1

            if (
                not signal_ichimoku_tenkan_kijun
                and not signal_ichimoku_price_above_cloud
                and volumes[-1] > media_volume
            ):
                sell_signals_count += 2
            elif (
                not signal_ichimoku_tenkan_kijun
                and not signal_ichimoku_price_above_cloud
            ):
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
            if (
                signal_ichimoku_tenkan_kijun and signal_ichimoku_price_above_cloud
            ):  # Adicionado: Sinal do Ichimoku Cloud
                active_signals.append(
                    "Ichimoku: Tenkan-sen cruzou acima da Kijun-sen e preço acima da nuvem."
                )

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
        [],  # Lista vazia para tps (será preenchida posteriormente)
        sma_long[-1] if sma_long else None,
    )

    # Calcular os TPs
    tps = []
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
