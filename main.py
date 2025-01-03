# ARQUIVO MAIN.PY
# Este é o arquivo principal do bot de trading, que executa o bot de trading continuamente.

import os
import time
from bot_trading import executar_bot_trading
from loguru import logger

if not os.path.exists("logs"):
    os.makedirs("logs")

# Configuração do loguru
logger.add("logs/bot.log", level="DEBUG")  # Adicionando o caminho para a pasta logs


# Função principal de execução
def main():
    is_testnet = False  # Testnet ou rede principal (mude conforme necessário)
    threads = []  # Lista para armazenar as threads

    try:  # Adicionar bloco try-except
        while True:
            try:
                # Executar o bot de trading (obter dados, calcular indicadores, identificar entradas)
                executar_bot_trading(is_testnet)

            except Exception as e:
                logger.error(
                    f"Erro ao processar o bot de trading: {e}"
                )  # Usando logger do loguru

            # Aguardar antes de realizar a próxima execução (intervalo de 2 minutos)
            time.sleep(120)

    except KeyboardInterrupt:  # Capturar o KeyboardInterrupt
        print("Interrompendo o programa...")
        for thread in threads:  # Finalizar as threads
            thread.join()


if __name__ == "__main__":
    main()
