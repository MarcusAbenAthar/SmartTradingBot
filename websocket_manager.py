import asyncio
import json
import os

import numpy as np
import pandas as pd
import websockets
from loguru import logger

from constants import (
    VOLATILITY_THRESHOLDS,
    SMA_PERIODS,
    EMA_PERIODS,
    LEVERAGE_THRESHOLDS,
    DEFAULT_LEVERAGE,
    LEVERAGE_MULTIPLIERS,
    SL_DISTANCE_MULTIPLIERS,
    ADX_TREND_THRESHOLD,
    ADX_MODERATE_TREND_THRESHOLD,
    RSI_OVERBOUGHT_THRESHOLD,
    RSI_OVERSOLD_THRESHOLD,
    RSI_NEUTRAL_UPPER_THRESHOLD,
    RSI_NEUTRAL_LOWER_THRESHOLD,
    STOCHASTIC_OVERBOUGHT_THRESHOLD,
    STOCHASTIC_OVERSOLD_THRESHOLD,
)
from indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_adx,
    calculate_stochastic,
    calculate_vwap,
    calculate_volatility,
)
from candle_patterns import identify_candle_patterns
from trading_logic import identify_entries, calculate_tp_sl
from telegram_alerts import enviar_mensagem_formatada

# Criar a pasta mãe se ela não existir
pasta_mae = "dados_velas"
if not os.path.exists(pasta_mae):
    os.makedirs(pasta_mae)

# Dicionário para armazenar as últimas N velas de cada par
velas_historico = {}
N = 200  # Armazenar as últimas 200 velas


def processar_dados_trade(trade):
    """
    Processa os dados do trade e cria a estrutura da vela.

    Args:
        trade (dict): Dicionário com os dados do trade.

    Returns:
        dict: Dicionário com a estrutura da vela.
    """
    return {
        "open": float(trade["p"]),
        "high": float(trade["p"]),
        "low": float(trade["p"]),
        "close": float(trade["p"]),
        "volume": float(trade["v"]),
        "time_period": trade["T"],
    }


def carregar_dados_csv(arquivo_csv):
    """
    Carrega os dados do arquivo CSV, caso ele exista.

    Args:
        arquivo_csv (str): Caminho para o arquivo CSV.
    """
    global velas_historico
    if os.path.exists(arquivo_csv):
        try:
            df_velas = pd.read_csv(arquivo_csv)
            velas_csv = df_velas.to_dict("records")
            symbol = arquivo_csv.split("_")[-1].split(".")[0]
            velas_historico[symbol] = velas_csv
        except Exception as e:
            logger.error(f"Erro ao ler dados do CSV: {e}")


def calcular_indicadores(velas_historico, symbol):
    """
    Calcula os indicadores técnicos para o símbolo especificado.

    Args:
        velas_historico (dict): Dicionário com o histórico de velas.
        symbol (str): Símbolo do par de moedas.
    """
    prices = np.array([float(candle["close"]) for candle in velas_historico[symbol]])
    volumes = np.array([float(candle["volume"]) for candle in velas_historico[symbol]])

    volatility = calculate_volatility(prices)

    period_sma_short = SMA_PERIODS[
        next(
            (i for i, v in enumerate(VOLATILITY_THRESHOLDS) if volatility < v),
            len(SMA_PERIODS) - 1,
        )
    ]
    period_ema_short = EMA_PERIODS[
        next(
            (i for i, v in enumerate(VOLATILITY_THRESHOLDS) if volatility < v),
            len(EMA_PERIODS) - 1,
        )
    ]

    sma = calculate_sma(prices, period_sma_short)
    ema = calculate_ema(prices, period_ema_short)
    rsi_values = calculate_rsi(prices, period_sma_short)
    rsi = rsi_values[-1] if rsi_values else 50.0
    macd_line, macd_signal = calculate_macd(prices)
    upper_band, lower_band = calculate_bollinger_bands(prices, period=period_sma_short)
    vwap = calculate_vwap(velas_historico[symbol])
    adx = calculate_adx(velas_historico[symbol])
    stochastic_k, stochastic_d = calculate_stochastic(velas_historico[symbol])

    return (
        prices,
        volumes,
        sma,
        ema,
        rsi,
        macd_line,
        macd_signal,
        upper_band,
        lower_band,
        vwap,
        adx,
        stochastic_k,
        stochastic_d,
    )


def calcular_alavancagem_dinamica(
    forca_do_sinal,
    volatility,
    distancia_sl,
    adx,
    rsi,
    stochastic_k,
    stochastic_d,
    entry_type,
    prices,  # Adicionando prices como argumento
):
    """
    Calcula a alavancagem dinamicamente com base nos indicadores e na força do sinal.

    Args:
        forca_do_sinal (int): Força do sinal de entrada.
        volatility (float): Volatilidade do ativo.
        distancia_sl (float): Distância do Stop Loss.
        adx (float): Valor do ADX.
        rsi (float): Valor do RSI.
        stochastic_k (float): Valor do Estocástico %K.
        stochastic_d (float): Valor do Estocástico %D.
        entry_type (str): Tipo de entrada ('BUY/LONG' ou 'SELL/SHORT').
        prices (list): Lista de preços do ativo.

    Returns:
        str: Alavancagem dinâmica calculada.
    """
    alavancagem = DEFAULT_LEVERAGE

    leverage_multiplier = LEVERAGE_MULTIPLIERS[
        next(
            (i for i, v in enumerate(LEVERAGE_THRESHOLDS) if forca_do_sinal >= v),
            len(LEVERAGE_MULTIPLIERS) - 1,
        )
    ]

    # Condições para aumentar a alavancagem
    if (
        forca_do_sinal >= LEVERAGE_THRESHOLDS[0]
        and volatility < VOLATILITY_THRESHOLDS[0]
        and distancia_sl
        > SL_DISTANCE_MULTIPLIERS[0] * prices[-1]  # Corrigido: usando prices[-1]
        and adx[-1] > ADX_TREND_THRESHOLD
        and (
            (entry_type == "BUY/LONG" and rsi > RSI_OVERBOUGHT_THRESHOLD)
            or (entry_type == "SELL/SHORT" and rsi < RSI_OVERSOLD_THRESHOLD)
        )
        and (
            (
                entry_type == "BUY/LONG"
                and stochastic_k[-1] > stochastic_d[-1]
                and stochastic_k[-1] < STOCHASTIC_OVERBOUGHT_THRESHOLD
            )
            or (
                entry_type == "SELL/SHORT"
                and stochastic_k[-1] < stochastic_d[-1]
                and stochastic_k[-1] > STOCHASTIC_OVERSOLD_THRESHOLD
            )
        )
    ):
        alavancagem = leverage_multiplier

    elif (
        forca_do_sinal >= LEVERAGE_THRESHOLDS[1]
        and volatility < VOLATILITY_THRESHOLDS[1]
        and distancia_sl
        > SL_DISTANCE_MULTIPLIERS[1] * prices[-1]  # Corrigido: usando prices[-1]
        and adx[-1] > ADX_MODERATE_TREND_THRESHOLD
        and (
            (entry_type == "BUY/LONG" and rsi > RSI_NEUTRAL_UPPER_THRESHOLD)
            or (entry_type == "SELL/SHORT" and rsi < RSI_NEUTRAL_LOWER_THRESHOLD)
        )
    ):
        alavancagem = leverage_multiplier

    elif (
        forca_do_sinal >= LEVERAGE_THRESHOLDS[2]
        and volatility < VOLATILITY_THRESHOLDS[2]
        and distancia_sl
        > SL_DISTANCE_MULTIPLIERS[2] * prices[-1]  # Corrigido: usando prices[-1]
    ):
        alavancagem = leverage_multiplier

    return alavancagem


def verificar_condicoes_entrada(
    prices,
    volumes,
    sma,
    ema,
    rsi,
    macd_line,
    macd_signal,
    upper_band,
    lower_band,
    vwap,
    adx,
    stochastic_k,
    stochastic_d,
    symbol,
):
    """
    Verifica as condições de entrada e gera alertas.

    Args:
        prices (np.array): Array de preços.
        volumes (np.array): Array de volumes.
        sma (np.array): Array da média móvel simples.
        ema (np.array): Array da média móvel exponencial.
        rsi (float): Valor do RSI.
        macd_line (np.array): Array da linha MACD.
        macd_signal (np.array): Array da linha de sinal do MACD.
        upper_band (np.array): Array da banda superior do Bollinger Bands.
        lower_band (np.array): Array da banda inferior do Bollinger Bands.
        vwap (np.array): Array do VWAP.
        adx (np.array): Array do ADX.
        stochastic_k (np.array): Array do Estocástico %K.
        stochastic_d (np.array): Array do Estocástico %D.
        symbol (str): Símbolo do par de moedas.
    """
    num_velas_disponiveis = len(prices)
    NUM_MIN_VELAS = max(20, num_velas_disponiveis // 2)

    if num_velas_disponiveis >= NUM_MIN_VELAS:
        result = identify_entries(
            prices=prices,
            period_sma=SMA_PERIODS[0],  # Usando o primeiro período de SMA como padrão
            volumes=volumes,
            long_term=False,
            sma=sma,
            candles=velas_historico[symbol],
            ema=ema,
            rsi=rsi,
            macd_line=macd_line,
            macd_signal=macd_signal,
            lower_band=lower_band,
            vwap=vwap,
            upper_band=upper_band,
            adx=adx,
            stochastic_k=stochastic_k,
            stochastic_d=stochastic_d,
            active_signals=[],
        )

        if (
            result
            and result["entry_type"] != "No Signal"
            and len(result["active_signals"]) > 6
        ):
            # Calcular a alavancagem dinamicamente
            forca_do_sinal = len(result["active_signals"])
            distancia_sl = abs(prices[-1] - result["sl"])

            alavancagem = calcular_alavancagem_dinamica(
                forca_do_sinal,
                calculate_volatility(prices),
                distancia_sl,
                adx,
                rsi,
                stochastic_k,
                stochastic_d,
                result["entry_type"],
                prices,
            )

            # Calcular os níveis de TP e SL
            tp_sl_levels = calculate_tp_sl(
                prices,
                result["entry_type"],
                calculate_volatility(prices),
                velas_historico[symbol],
                forca_do_sinal,
            )
            result["tps"] = tp_sl_levels["tps"]
            result["sl"] = tp_sl_levels["sl"]

            # Enviar a mensagem para o Telegram
            dados_mensagem = {
                "simbolo": symbol,
                "entrada": prices[-1],
                "tipo_entrada": result["entry_type"],
                "tps": result["tps"],
                "sl": result["sl"],
                "motivos": result["active_signals"],
                "alavancagem": alavancagem,
            }

            logger.debug(f"Dados da mensagem: {dados_mensagem}")
            if result["entry_type"] != "NEUTRO":
                enviar_mensagem_formatada(dados_mensagem)


def salvar_dados_csv(vela, symbol):
    """
    Salva os dados da vela em um arquivo CSV.

    Args:
        vela (dict): Dicionário com a estrutura da vela.
        symbol (str): Símbolo do par de moedas.
    """
    arquivo_csv = os.path.join(pasta_mae, symbol, f"dados_velas_{symbol}.csv")
    pasta_par = os.path.join(pasta_mae, symbol)

    if not os.path.exists(pasta_par):
        os.makedirs(pasta_par)

    if os.path.exists(arquivo_csv):
        df_velas = pd.read_csv(arquivo_csv)
        df_velas = pd.concat([df_velas, pd.DataFrame([vela])], ignore_index=True)
    else:
        df_velas = pd.DataFrame([vela])
    df_velas.to_csv(arquivo_csv, index=False)


async def handle_message(exchange, message):
    """
    Processa as mensagens de trade recebidas via WebSocket.
    """
    try:
        data = json.loads(message)

        if not isinstance(data, dict):
            logger.warning(
                f"Mensagem inválida recebida (não é um dicionário): {message}"
            )
            return

        # Responder ao ping da Bybit
        if data.get("op") == "ping":
            await exchange.ws.send(
                json.dumps({"op": "pong", "req_id": data.get("req_id")})
            )
            logger.debug("Respondeu ao ping com pong")
            return

        # Verificar se a mensagem é um trade
        if "topic" not in data or not data["topic"].startswith("trade"):
            logger.warning(f"Mensagem não é do tipo trade: {message}")
            return

        for trade in data["data"]:
            symbol = trade["s"]
            vela = processar_dados_trade(trade)

            carregar_dados_csv(
                os.path.join(pasta_mae, symbol, f"dados_velas_{symbol}.csv")
            )

            # Armazenar a nova vela no histórico
            velas_historico[symbol] = velas_historico.get(symbol, []) + [vela]
            velas_historico[symbol] = velas_historico[symbol][-N:]

            (
                prices,
                volumes,
                sma,
                ema,
                rsi,
                macd_line,
                macd_signal,
                upper_band,
                lower_band,
                vwap,
                adx,
                stochastic_k,
                stochastic_d,
            ) = calcular_indicadores(velas_historico, symbol)

            verificar_condicoes_entrada(
                prices,
                volumes,
                sma,
                ema,
                rsi,
                macd_line,
                macd_signal,
                upper_band,
                lower_band,
                vwap,
                adx,
                stochastic_k,
                stochastic_d,
                symbol,
            )

            salvar_dados_csv(vela, symbol)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem da WebSocket: {e}")
        logger.exception(e)


async def subscribe_to_trades(exchange, symbol, wss_url):
    """
    Assina os trades de um símbolo específico via WebSocket e processa as mensagens recebidas.

    Args:
        exchange: Objeto da exchange.
        symbol: Símbolo do par de moedas.
        wss_url: URL da conexão WebSocket.
    """
    while True:
        try:
            async with websockets.connect(
                wss_url, ping_interval=20, ping_timeout=120
            ) as websocket:
                exchange.ws = websocket
                subscription_message = {"op": "subscribe", "args": [f"trade.{symbol}"]}

                await websocket.send(json.dumps(subscription_message))
                logger.info(
                    f"Inscrito para receber atualizações de trades para {symbol}"
                )

                while True:
                    message = await websocket.recv()
                    await handle_message(exchange, message)

        except Exception as e:
            logger.error(f"Erro na conexão WebSocket para {symbol}: {e}")
            logger.exception(e)
            await asyncio.sleep(5)  # Aguarda um pouco antes de tentar reconectar
