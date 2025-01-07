# ARQUIVO CONFIG_BYBIT.PY
# Este arquivo contém a função `connect_bybit` que conecta à API da Bybit usando ccxt.

import ccxt
import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()  # Carrega as variáveis de ambiente do arquivo .env


def connect_bybit(testnet=False, market_type="future"):
    """
    Conecta-se à API da Bybit usando ccxt.

    Args:
        testnet (bool, optional): Define se a conexão será com a Testnet (True) ou Produção (False). Defaults to False.
        market_type (str, optional): Define o tipo de mercado ("future" para Futuros, "spot" para Spot). Defaults to "future".

    Returns:
        ccxt.bybit: Objeto de exchange da Bybit, conectado à API.
        str: Tipo de mercado selecionado.
    """
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError(
            "As chaves de API da Bybit (API_KEY e API_SECRET) devem ser fornecidas ou configuradas no arquivo .env."
        )

    exchange_class = getattr(ccxt, "bybit")
    exchange = exchange_class(
        {
            "apiKey": api_key,
            "secret": api_secret,
            "testmode": testnet,
            "verbose": False,
            "options": {
                "defaultType": market_type,
            },
        }
    )

    logger.info(
        f"Conectado à Bybit {'Testnet' if testnet else 'Produção'} - Mercado de {'Futuros' if market_type == 'future' else 'Spot'}"
    )
    return exchange, market_type
