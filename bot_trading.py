# ARQUIVO BOT_TRADING.PY
# Função para executar o bot de trading na Bybit
# Aqui se encontra o código principal do bot de trading, que conecta à Bybit, obtém os pares de futuros, coleta dados via WebSocket, processa sinais.

import time
import numpy as np
import pandas as pd
import os
from config_bybit import connect_bybit
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
)
from send_telegram import enviar_mensagem_formatada
import logging
from pybit.unified_trading import WebSocket

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

# Criar a pasta mãe se ela não existir
pasta_mae = "dados_velas"
if not os.path.exists(pasta_mae):
    os.makedirs(pasta_mae)

# Dicionário para armazenar as últimas N velas de cada par
velas_historico = {}
N = 200  # Armazenar as últimas 200 velas (ajuste conforme necessário)

# Lista de sinais ativos
active_signals = []


def websocket_handler(message):
    """
    Processa as mensagens recebidas da WebSocket da Bybit.
    """
    try:
        if message["topic"].startswith("kline.1."):
            symbol = message["topic"].split(".")[2]
            vela = message["data"][0]

            # 1. Carregar os dados do CSV se o arquivo existir
            arquivo_csv = os.path.join(pasta_mae, symbol, f"dados_velas_{symbol}.csv")
            if os.path.exists(arquivo_csv):
                try:
                    df_velas = pd.read_csv(arquivo_csv)
                    velas_csv = df_velas.to_dict("records")
                    velas_historico[symbol] = velas_csv
                except Exception as e:
                    logger.error(f"Erro ao ler dados do CSV para {symbol}: {e}")

            # 2. Armazenar a nova vela no dicionário `velas_historico`
            velas_historico[symbol] = velas_historico.get(symbol, []) + [vela]
            velas_historico[symbol] = velas_historico[symbol][-N:]

            # 3. Calcular os indicadores para o símbolo
            prices = np.array(
                [float(vela["close"]) for vela in velas_historico[symbol]]
            )
            volumes = np.array(
                [float(vela["volume"]) for vela in velas_historico[symbol]]
            )

            # Calcular a volatilidade para definir os períodos do SMA e EMA dinamicamente
            volatility = calculate_volatility(prices)
            if volatility < 0.5:
                period_sma_short = 50  # Volatilidade muito baixa
                period_ema_short = 20
            elif volatility < 1.0:
                period_sma_short = 30  # Volatilidade baixa
                period_ema_short = 15
            elif volatility < 2.0:
                period_sma_short = 20  # Volatilidade moderada
                period_ema_short = 12
            else:
                period_sma_short = 10  # Volatilidade alta
                period_ema_short = 5

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
                    period_ema=period_ema_short,
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

                # Garantindo que symbol está definido
                symbol = message["topic"].split(".")[2]

                # Calcular a distância do stop-loss
                distancia_sl = abs(prices[-1] - result["sl"])

                alavancagem = "3x"  # Alavancagem padrão

                # Condições para aumentar a alavancagem (adaptar conforme necessário)
                if (
                    forca_do_sinal >= 7  # Força do sinal muito alta
                    and volatility < 0.5  # Volatilidade baixa
                    and distancia_sl > 0.02 * prices[-1]  # Stop-loss distante
                    and adx[-1] > 25  # Tendência forte
                    and (
                        (result["entry_type"] == "BUY/LONG" and rsi > 60)
                        or (result["entry_type"] == "SELL/SHORT" and rsi < 40)
                    )  # RSI confirmando a direção
                    and (
                        (
                            result["entry_type"] == "BUY/LONG"
                            and stochastic_k[-1] > stochastic_d[-1]
                            and stochastic_k[-1] < 80
                        )
                        or (
                            result["entry_type"] == "SELL/SHORT"
                            and stochastic_k[-1] < stochastic_d[-1]
                            and stochastic_k[-1] > 20
                        )
                    )  # Estocástico confirmando a direção
                ):
                    alavancagem = "20x"

                elif (
                    forca_do_sinal >= 5  # Força do sinal alta
                    and volatility < 1.0  # Volatilidade moderada
                    and distancia_sl
                    > 0.01 * prices[-1]  # Stop-loss moderadamente distante
                    and adx[-1] > 20  # Tendência moderada
                    and (
                        (result["entry_type"] == "BUY/LONG" and rsi > 50)
                        or (result["entry_type"] == "SELL/SHORT" and rsi < 50)
                    )  # RSI neutro ou confirmando a direção
                ):
                    alavancagem = "10x"

                elif (
                    forca_do_sinal >= 3  # Força do sinal moderada
                    and volatility < 2.0  # Volatilidade alta
                    and distancia_sl > 0.005 * prices[-1]  # Stop-loss próximo
                ):
                    alavancagem = "5x"

                # --- Fim da lógica da alavancagem ---

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
                # Registrar o valor de `dados_mensagem` no log
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


# Função para obter todos os pares de mercado futuros
def obter_pares_todos(session, market_type):
    """
    Obtém todos os pares de negociação para o tipo de mercado especificado,
    filtrando por USDT.

    Args:
        session (HTTP): Sessão HTTP da Bybit.
        market_type (str): Tipo de mercado ("future").

    Returns:
        list: Lista de símbolos de pares de negociação.
    """
    # A API da Bybit usa 'linear' para futuros perpétuos USDT
    category = "linear" if market_type == "future" else market_type

    try:
        response = session.get_instruments_info(category=category)
        result = response.json() if hasattr(response, "json") else response

        if result["retCode"] == 0:
            pares = [
                item["symbol"]
                for item in result["result"]["list"]
                if item["symbol"].endswith("USDT")
            ]
            logger.info(
                f"Total de pares {market_type} encontrados (apenas USDT): {len(pares)}"
            )
            return pares
        else:
            logger.error(f"Erro ao obter pares {market_type}: {result['retMsg']}")
            return []
    except Exception as e:
        logger.error(f"Exceção ao obter pares {market_type}: {e}")
        return []


# Função principal do bot de trading
def executar_bot_trading(testnet=True):
    """
    Conecta à Bybit, obtém os pares de futuros, coleta dados via WebSocket,
    processa sinais e envia mensagens.
    """

    # Iniciar a WebSocket
    ws = WebSocket(
        testnet=testnet,
        ping_interval=30,
        channel_type="linear",
    )

    # Obter todos os pares de futuros
    session_future, _ = connect_bybit(testnet=testnet, market_type="future")
    pares_futuros = obter_pares_todos(session_future, "future")

    # Inscrever-se nos streams de dados para cada par
    for par in pares_futuros:
        ws.kline_stream(
            callback=websocket_handler,
            symbol=par,
            interval="1",
        )

    # Manter a conexão WebSocket aberta
    while True:
        time.sleep(1)
