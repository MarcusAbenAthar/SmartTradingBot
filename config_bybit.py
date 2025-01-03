# ARQUIVO CONFIG_BYBIT.PY
# Este arquivo contém a função `connect_bybit` que conecta à API da Bybit usando pybit.

from pybit.unified_trading import HTTP
import os
from dotenv import load_dotenv
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env


def connect_bybit(testnet=False, market_type="future"):
    """
    Conecta-se à API da Bybit usando pybit.

    Args:
        testnet (bool, optional): Define se a conexão será com a Testnet (True) ou Produção (False). Defaults to False.
        market_type (str, optional): Define o tipo de mercado ("future" para Futuros, "spot" para Spot). Defaults to "future".

    Returns:
        HTTP: Objeto de sessão HTTP da Bybit, conectado à API.
        str: Tipo de mercado selecionado.
    """
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError(
            "As chaves de API da Bybit (API_KEY e API_SECRET) devem ser fornecidas ou configuradas no arquivo .env."
        )

    try:
        session = HTTP(
            testnet=testnet,
            api_key=api_key,
            api_secret=api_secret,
        )
        logger.info(
            f"Conectado à Bybit {'Testnet' if testnet else 'Produção'} - Mercado de {'Futuros' if market_type == 'future' else 'Spot'}"
        )
        return session, market_type
    except Exception as e:
        logger.error(f"Erro ao conectar à Bybit: {e}")
        raise
