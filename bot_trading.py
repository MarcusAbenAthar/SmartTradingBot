import numpy as np
import pandas as pd
import os
import asyncio
import websockets
import json
from utils import (
    calculate_adx,
    calculate_stochastic,
    define_quantidade_tps,
    identify_entries,
    calculate_volatility,
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_vwap,
    calculate_tp_sl,
)
from send_telegram import enviar_mensagem_formatada
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURAÇÕES (estes valores podem ser ajustados no arquivo .env) ---
VOLATILITY_THRESHOLDS = [
    float(x) for x in os.getenv("VOLATILITY_THRESHOLDS", "0.5,1.0,2.0").split(",")
]
SMA_PERIODS = [int(x) for x in os.getenv("SMA_PERIODS", "50,30,20,10").split(",")]
EMA_PERIODS = [int(x) for x in os.getenv("EMA_PERIODS", "20,15,12,5").split(",")]
LEVERAGE_THRESHOLDS = [
    int(x) for x in os.getenv("LEVERAGE_THRESHOLDS", "7,5,3").split(",")
]
DEFAULT_LEVERAGE = os.getenv("DEFAULT_LEVERAGE", "3x")
LEVERAGE_MULTIPLIERS = [os.getenv("LEVERAGE_MULTIPLIERS", "20x,10x,5x").split(",")]
SL_DISTANCE_MULTIPLIERS = [
    float(x) for x in os.getenv("SL_DISTANCE_MULTIPLIERS", "0.02,0.01,0.005").split(",")
]
ADX_TREND_THRESHOLD = int(os.getenv("ADX_TREND_THRESHOLD", "25"))
ADX_MODERATE_TREND_THRESHOLD = int(os.getenv("ADX_MODERATE_TREND_THRESHOLD", "20"))
RSI_OVERBOUGHT_THRESHOLD = int(os.getenv("RSI_OVERBOUGHT_THRESHOLD", "60"))
RSI_OVERSOLD_THRESHOLD = int(os.getenv("RSI_OVERSOLD_THRESHOLD", "40"))
RSI_NEUTRAL_UPPER_THRESHOLD = int(os.getenv("RSI_NEUTRAL_UPPER_THRESHOLD", "50"))
RSI_NEUTRAL_LOWER_THRESHOLD = int(os.getenv("RSI_NEUTRAL_LOWER_THRESHOLD", "50"))
STOCHASTIC_OVERBOUGHT_THRESHOLD = int(
    os.getenv("STOCHASTIC_OVERBOUGHT_THRESHOLD", "80")
)
STOCHASTIC_OVERSOLD_THRESHOLD = int(os.getenv("STOCHASTIC_OVERSOLD_THRESHOLD", "20"))
# -----------------------------------------------------------------------

# Configuração de logging
logger.add(
    "logs/bot_trading.log", rotation="1 day", level="DEBUG"
)  # Adicionando rotação diária

# Criar a pasta mãe se ela não existir
pasta_mae = "dados_velas"
if not os.path.exists(pasta_mae):
    os.makedirs(pasta_mae)

# Dicionário para armazenar as últimas N velas de cada par
velas_historico = {}
N = 200  # Armazenar as últimas 200 velas (ajuste conforme necessário)

# Lista de sinais ativos
active_signals = []


async def handle_message(exchange, message):
    """
    Processa as mensagens de trade recebidas via WebSocket.
    """
    global velas_historico

    logger.debug(f"Mensagem recebida: {message}")

    try:
        data = json.loads(message)  # Converte a mensagem JSON em um dicionário Python

        # Verifica se a mensagem é um dicionário
        if not isinstance(data, dict):
            logger.warning(
                f"Mensagem inválida recebida (não é um dicionário): {message}"
            )
            return

        # Bybit envia ping, precisamos responder com pong
        if data.get("op") == "ping":
            await exchange.ws.send(
                json.dumps({"op": "pong", "req_id": data.get("req_id")})
            )
            logger.debug("Respondeu ao ping com pong")
            return

        # Verifica se a mensagem é um trade e se contém os dados necessários
        if "topic" not in data or not data["topic"].startswith("trade"):
            logger.warning(f"Mensagem não é do tipo trade: {message}")
            return

        for trade in data["data"]:
            symbol = trade["s"]

            # Adaptação para a estrutura de mensagem da Bybit
            vela = {
                "open": float(trade["p"]),
                "high": float(trade["p"]),
                "low": float(trade["p"]),
                "close": float(trade["p"]),
                "volume": float(trade["v"]),
                "time_period": trade["T"],
            }

            # 1. Carregar os dados do CSV se o arquivo existir
            arquivo_csv = os.path.join(pasta_mae, symbol, f"dados_velas_{symbol}.csv")
            if os.path.exists(arquivo_csv):
                try:
                    df_velas = pd.read_csv(arquivo_csv)
                    velas_csv = df_velas.to_dict("records")
                    velas_historico[symbol] = velas_csv
                except Exception as e:
                    logger.error(f"Erro ao ler dados do CSV para {symbol}: {e}")

            # 2. Armazenar a nova vela no dicionário velas_historico
            velas_historico[symbol] = velas_historico.get(symbol, []) + [vela]
            velas_historico[symbol] = velas_historico[symbol][-N:]

            # 3. Calcular os indicadores para o símbolo
            prices = np.array(
                [float(vela["close"]) for vela in velas_historico[symbol]]
            )
            volumes = np.array(
                [float(vela["volume"]) for vela in velas_historico[symbol]]
            )

            # Carregar configurações dinâmicas
            volatility_thresholds = VOLATILITY_THRESHOLDS
            sma_periods = SMA_PERIODS
            ema_periods = EMA_PERIODS
            leverage_thresholds = LEVERAGE_THRESHOLDS
            default_leverage = DEFAULT_LEVERAGE
            leverage_multipliers = LEVERAGE_MULTIPLIERS
            sl_distance_multipliers = SL_DISTANCE_MULTIPLIERS
            adx_trend_threshold = ADX_TREND_THRESHOLD
            adx_moderate_trend_threshold = ADX_MODERATE_TREND_THRESHOLD
            rsi_overbought_threshold = RSI_OVERBOUGHT_THRESHOLD
            rsi_oversold_threshold = RSI_OVERSOLD_THRESHOLD
            rsi_neutral_upper_threshold = RSI_NEUTRAL_UPPER_THRESHOLD
            rsi_neutral_lower_threshold = RSI_NEUTRAL_LOWER_THRESHOLD
            stochastic_overbought_threshold = STOCHASTIC_OVERBOUGHT_THRESHOLD
            stochastic_oversold_threshold = STOCHASTIC_OVERSOLD_THRESHOLD

            # Calcular a volatilidade para definir os períodos do SMA e EMA dinamicamente
            volatility = calculate_volatility(prices)

            # Escolher os períodos de SMA e EMA com base na volatilidade
            period_sma_short = sma_periods[
                next(
                    (i for i, v in enumerate(volatility_thresholds) if volatility < v),
                    len(sma_periods) - 1,
                )
            ]
            period_ema_short = ema_periods[
                next(
                    (i for i, v in enumerate(volatility_thresholds) if volatility < v),
                    len(ema_periods) - 1,
                )
            ]

            # Calcular os indicadores técnicos
            sma = calculate_sma(prices, period_sma_short)
            ema = calculate_ema(prices, period_ema_short)
            rsi_values = calculate_rsi(prices, period_sma_short)
            rsi = rsi_values[-1] if rsi_values else 50.0
            macd_line, macd_signal = calculate_macd(prices)
            upper_band, lower_band = calculate_bollinger_bands(
                prices, period=period_sma_short
            )
            vwap = calculate_vwap(prices, volumes, period=period_sma_short)

            # Calcular ADX e Estocástico
            adx = calculate_adx(velas_historico[symbol])
            stochastic_k, stochastic_d = calculate_stochastic(velas_historico[symbol])

            # 4. Verificar as condições de entrada
            num_velas_disponiveis = len(prices)
            NUM_MIN_VELAS = max(20, num_velas_disponiveis // 2)
            result = None
            dados_mensagem = {"simbolo": "N/A"}

            if num_velas_disponiveis >= NUM_MIN_VELAS:
                result = identify_entries(
                    prices=prices,
                    period_sma=period_sma_short,
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
                dados_mensagem = {
                    "simbolo": "N/A",
                    "entrada": 0,
                }  # Inicializador padrão
                # 5. Gerar alertas e enviar para o Telegram (dinâmico)
                dados_mensagem = {"tps": []}

                if (
                    result
                    and result["entry_type"] != "No Signal"
                    and len(result["active_signals"]) > 6
                ):
                    # --- Calcular a alavancagem dinamicamente ---
                    forca_do_sinal = len(result["active_signals"])

                    # Calcular a distância do stop-loss
                    distancia_sl = abs(prices[-1] - result["sl"])

                    alavancagem = default_leverage  # Alavancagem padrão

                    # Escolher o multiplicador de alavancagem com base na força do sinal
                    leverage_multiplier = leverage_multipliers[
                        next(
                            (
                                i
                                for i, v in enumerate(leverage_thresholds)
                                if forca_do_sinal >= v
                            ),
                            len(leverage_multipliers) - 1,
                        )
                    ]

                    # Condições para aumentar a alavancagem (adaptar conforme necessário)
                    if (
                        forca_do_sinal
                        >= leverage_thresholds[0]  # Força do sinal muito alta
                        and volatility < volatility_thresholds[0]  # Volatilidade baixa
                        and distancia_sl
                        > sl_distance_multipliers[0] * prices[-1]  # Stop-loss distante
                        and adx[-1] > adx_trend_threshold  # Tendência forte
                        and (
                            (
                                result["entry_type"] == "BUY/LONG"
                                and rsi > rsi_overbought_threshold
                            )
                            or (
                                result["entry_type"] == "SELL/SHORT"
                                and rsi < rsi_oversold_threshold
                            )
                        )  # RSI confirmando a direção
                        and (
                            (
                                result["entry_type"] == "BUY/LONG"
                                and stochastic_k[-1] > stochastic_d[-1]
                                and stochastic_k[-1] < stochastic_overbought_threshold
                            )
                            or (
                                result["entry_type"] == "SELL/SHORT"
                                and stochastic_k[-1] < stochastic_d[-1]
                                and stochastic_k[-1] > stochastic_oversold_threshold
                            )
                        )  # Estocástico confirmando a direção
                    ):
                        alavancagem = leverage_multiplier

                    elif (
                        forca_do_sinal >= leverage_thresholds[1]  # Força do sinal alta
                        and volatility
                        < volatility_thresholds[1]  # Volatilidade moderada
                        and distancia_sl
                        > sl_distance_multipliers[1]
                        * prices[-1]  # Stop-loss moderadamente distante
                        and adx[-1] > adx_moderate_trend_threshold  # Tendência moderada
                        and (
                            (
                                result["entry_type"] == "BUY/LONG"
                                and rsi > rsi_neutral_upper_threshold
                            )
                            or (
                                result["entry_type"] == "SELL/SHORT"
                                and rsi < rsi_neutral_lower_threshold
                            )
                        )  # RSI neutro ou confirmando a direção
                    ):
                        alavancagem = leverage_multiplier

                    elif (
                        forca_do_sinal
                        >= leverage_thresholds[2]  # Força do sinal moderada
                        and volatility < volatility_thresholds[2]  # Volatilidade alta
                        and distancia_sl
                        > sl_distance_multipliers[2] * prices[-1]  # Stop-loss próximo
                    ):
                        alavancagem = leverage_multiplier

                    # --- Fim da lógica da alavancagem ---

                    # Chamar a função calculate_tp_sl para calcular os níveis de TP e SL
                    tp_sl_levels = calculate_tp_sl(
                        prices,
                        result["entry_type"],
                        volatility,
                        velas_historico[symbol],
                        forca_do_sinal,
                    )
                    result["tps"] = tp_sl_levels["tps"]
                    result["sl"] = tp_sl_levels["sl"]

                    # Enviar a mensagem para o Telegram (apenas quando houver sinal claro)
                    dados_mensagem = {
                        "simbolo": symbol,
                        "entrada": prices[-1],
                        "tipo_entrada": result["entry_type"],
                        "tps": result["tps"],
                        "sl": result["sl"],
                        "motivos": result["active_signals"],
                        "alavancagem": alavancagem,
                    }
                    # Registrar o valor de dados_mensagem no log
                    logger.debug(f"Dados da mensagem: {dados_mensagem}")
                    if result["entry_type"] != "NEUTRO":  # Adicionar esta condição
                        enviar_mensagem_formatada(dados_mensagem)

            # 6. Salvar as velas em um arquivo CSV (depois da análise)
            arquivo_csv = os.path.join(pasta_mae, symbol, f"dados_velas_{symbol}.csv")

            # Criar a pasta do par, se ela não existir
            pasta_par = os.path.join(
                pasta_mae, symbol
            )  # Define o caminho da pasta do par
            if not os.path.exists(pasta_par):
                os.makedirs(pasta_par)

            # Criar a pasta mãe se ela não existir (opcional)
            if not os.path.exists(pasta_mae):
                os.makedirs(pasta_mae)

            if os.path.exists(arquivo_csv):
                df_velas = pd.read_csv(arquivo_csv)
                df_velas = pd.concat(
                    [df_velas, pd.DataFrame([vela])], ignore_index=True
                )
            else:
                df_velas = pd.DataFrame([vela])
            df_velas.to_csv(arquivo_csv, index=False)

    except Exception as e:
        logger.error(f"Erro ao processar mensagem da WebSocket: {e}")
        logger.exception(e)


async def subscribe_to_trades(exchange, symbol, wss_url):
    """
    Assina os trades de um símbolo específico via WebSocket.
    """
    while True:
        try:
            async with websockets.connect(
                wss_url, ping_interval=20, ping_timeout=120
            ) as websocket:
                exchange.ws = websocket
                subscription_message = {"op": "subscribe", "args": [f"trade.{symbol}"]}

                await exchange.ws.send(json.dumps(subscription_message))
                logger.info(
                    f"Inscrito para receber atualizações de trades para {symbol}"
                )

                while True:
                    message = await exchange.ws.recv()
                    await handle_message(exchange, message)

        except Exception as e:
            logger.error(f"Erro na conexão WebSocket para {symbol}: {e}")
            logger.exception(e)
            await asyncio.sleep(5)  # Aguarda um pouco antes de tentar reconectar


# Função principal do bot de trading
async def executar_bot_trading(exchange):
    """
    Conecta à Bybit, obtém os pares de futuros, coleta dados via WebSocket,
    processa sinais e envia mensagens.
    """
    exchange.options["defaultType"] = "future"
    # Usar a ccxt para obter os mercados
    markets = exchange.load_markets()
    pares_futuros = [
        market["id"]
        for market in markets.values()
        if market["swap"] and market["quote"] == "USDT"
    ]

    logger.info(f"Iniciando execução para {len(pares_futuros)} pares de futuros.")

    # Inscrever-se nos streams de dados para cada par
    wss_url = "wss://stream.bybit.com/v5/public/linear"  # URL do WebSocket para Futuros Perpétuos
    tasks = [subscribe_to_trades(exchange, symbol, wss_url) for symbol in pares_futuros]
    await asyncio.gather(*tasks)
