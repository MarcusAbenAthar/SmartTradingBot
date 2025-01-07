"""
Arquivo principal para inicializar o bot de trading.
- Estabelece conexão com a API da Bybit.
- Inicia a execução assíncrona do bot de trading.
"""

import asyncio
import os
from loguru import logger
from config_bybit import connect_bybit
from dotenv import load_dotenv
from bot_trading import executar_bot_trading

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do loguru
logger.add("logs/bot_trading.log", rotation="1 day", level="DEBUG")


async def main() -> None:
    """
    Função principal para execução do bot de trading.
    - Configura o ambiente (Testnet ou Produção).
    - Conecta-se à API da Bybit.
    - Inicia a lógica do bot.
    """
    # Obter a configuração de Testnet do arquivo .env
    is_testnet = os.getenv("IS_TESTNET", "false").lower() == "true"
    logger.info(f"Modo de operação: {'Testnet' if is_testnet else 'Produção'}")

    # Valida as variáveis de ambiente
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")
    if not api_key or not api_secret:
        logger.error("Chaves de API não configuradas no arquivo .env")
        return

    # Estabelecer conexão com a Bybit
    try:
        exchange, market_type = connect_bybit(testnet=is_testnet)
        logger.info("Conexão com a Bybit estabelecida com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao conectar com a Bybit: {e}")
        return  # Encerra a execução se a conexão falhar

    # Iniciar a execução do bot de trading
    try:
        logger.info(f"Iniciando o bot de trading para o mercado {market_type}...")
        await executar_bot_trading(exchange)
    except Exception as e:
        logger.exception(f"Erro na execução do bot de trading: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())  # Inicia o loop de eventos asyncio
    except KeyboardInterrupt:
        logger.info("Interrompendo o programa...")
