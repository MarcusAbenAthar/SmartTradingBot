"""
Arquivo principal para inicializar o bot de trading.
- Estabelece conexão com a API da Bybit.
- Inicia a execução assíncrona do bot de trading.
"""

import os
import asyncio
from bot_trading import executar_bot_trading
import ccxt
from loguru import logger
from config_bybit import connect_bybit
from dotenv import load_dotenv

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env

# Verifica e cria o diretório de logs
if not os.path.exists("logs"):
    os.makedirs("logs")

# Configuração do loguru
logger.add("logs/bot_trading.log", rotation="1 day", level="DEBUG")


# Função principal
async def main():
    # Carregar variáveis do ambiente
    load_dotenv()

    # Conexão à API da Bybit
    exchange = ccxt.bybit(
        {
            "apiKey": os.getenv("BYBIT_API_KEY"),
            "secret": os.getenv("BYBIT_API_SECRET"),
            "enableRateLimit": True,
        }
    )

    try:
        logger.info("Conexão com a Bybit estabelecida com sucesso.")
        await executar_bot_trading(exchange)
    except Exception as e:
        logger.error(f"Erro ao executar o bot de trading: {e}")
    finally:
        await exchange.close()


# Executar o bot
if __name__ == "__main__":
    asyncio.run(main())
