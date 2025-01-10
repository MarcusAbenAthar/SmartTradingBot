import asyncio
from loguru import logger
from dotenv import load_dotenv

# Importar funções dos outros arquivos
from websocket_manager import subscribe_to_trades

load_dotenv()

# --- CONFIGURAÇÕES ---
# (As configurações foram movidas para o arquivo 'constants.py')
# ----------------------


async def executar_bot_trading(exchange):
    """
    Conecta à Bybit, obtém os pares de futuros, coleta dados via WebSocket
    e inicia as tarefas de processamento para cada par.
    """
    try:
        exchange.options["defaultType"] = "future"

        # Obter os mercados da Bybit
        markets = exchange.load_markets()

        # Filtrar os pares de futuros com USDT como quote currency
        # (reduzindo o número de pares)
        pares_futuros = [
            market["id"]
            for market in markets.values()
            if market["swap"]
            and market["quote"] == "USDT"
            and market["base"]
            in [
                "BTC",
                "ETH",
                "XRP",
                "SOL",
            ]  # Exemplo: incluir apenas BTC, ETH, XRP e SOL
        ]

        # pares_futuros = [
        #     market["id"]
        #     for market in markets.values()
        #     if market["swap"] and market["quote"] == "USDT"
        # ]

        logger.info(f"Iniciando execução para {len(pares_futuros)} pares de futuros.")

        # URL do WebSocket para Futuros Perpétuos
        wss_url = "wss://stream.bybit.com/v5/public/linear"

        # Criar e agendar tarefas para cada par de futuros
        tasks = [
            subscribe_to_trades(exchange, symbol, wss_url) for symbol in pares_futuros
        ]
        await asyncio.gather(*tasks)

    except Exception as e:
        logger.error(f"Erro na execução do bot de trading: {e}")
        logger.exception(e)
