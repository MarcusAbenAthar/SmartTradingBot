# ARQUIVO SEND_TELEGRAM.PY
# Função para enviar mensagens formatadas via Telegram

import os
import requests
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente (caso utilize um .env)
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()


# Função para enviar a mensagem via Telegram
def send_telegram_message(mensagem):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        logger.error(
            "Variáveis de ambiente TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID não configuradas."
        )
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensagem,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Lança exceção para erros HTTP
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao enviar mensagem via Telegram: {e}")


def formatar_valor(valor):
    """
    Formata um valor numérico para 4 casas decimais apenas se,
    a partir da 4ª casa, todos os dígitos restantes forem 0.

    Args:
      valor (float): O valor a ser formatado.

    Returns:
      str: O valor formatado como string.
    """
    str_valor = str(valor)  # Converter o valor para string
    if "." in str_valor:  # Verificar se o valor tem casas decimais
        parte_decimal = str_valor.split(".")[1]  # Obter a parte decimal
        if len(parte_decimal) > 4 and parte_decimal[4:] == "0" * (
            len(parte_decimal) - 4
        ):
            return f"{valor:.4f}"  # Formatar com 4 casas decimais
    return str_valor  # Manter o valor original sem formatação


def enviar_mensagem_formatada(dados_mensagem):
    alavancagem = dados_mensagem.get(
        "alavancagem", "N/A"
    )  # Obter a alavancagem da mensagem

    simbolo = dados_mensagem.get("simbolo", "N/A")  # Obter o símbolo da mensagem

    # Validação dos dados_mensagem recebidos
    if not isinstance(dados_mensagem, dict):
        logger.error("Erro: 'dados_mensagem' não é um dicionário!")
        return

    required_keys = [
        "simbolo",
        "entrada",
        "tps",
        "sl",
        "motivos",
        "tipo_entrada",
    ]
    for chave in required_keys:
        if chave not in dados_mensagem:
            logger.error(
                f"Erro: A chave '{chave}' não foi encontrada nos dados_mensagem!"
            )
            return

    if not dados_mensagem["simbolo"]:
        logger.error("Erro: O valor de 'simbolo' está vazio!")
        return

    # Extrair os dados_mensagem do dicionário (com valores padrão caso não existam)
    entrada = dados_mensagem.get("entrada", "N/A")
    sl = dados_mensagem.get("sl", "N/A")
    motivos = dados_mensagem.get("motivos", ["Motivos não fornecidos"])
    tipo_entrada = dados_mensagem.get("tipo_entrada", "Desconhecido")

    # Determinar o emoji com base no tipo de entrada
    tipo_sinal = "🟢" if tipo_entrada == "BUY/LONG" else "🔴"
    # Formatar os Take Profits (TPs) como uma lista de strings
    tps_str = {
        chr(10).join(
            [
                f"🎯 - TP{i+1}: `{formatar_valor(tp)}`"
                for i, tp in enumerate(dados_mensagem["tps"])
            ]
        )
    }

    # Construir a mensagem formatada
    mensagem = f"""
    {tipo_sinal} **Sinal de {tipo_entrada}**

    💱 **Par**: `{simbolo}`
    💰 **Entrada**: `{formatar_valor(entrada)}`
    ⚖️ **Alavancagem Sugerida**: `{alavancagem}`

    {tps_str}\n 

    ⛔️ **Stop Loss (SL)**: `{formatar_valor(sl)}`

    📝 **Motivos da Decisão**:
    \n{chr(10).join([f'      • {motivo.ljust(60)}' for motivo in motivos])}
    """
    logger.info("Mensagem formatada para envio: %s", mensagem)  # Usando o logger
    send_telegram_message(mensagem)  # Enviar a mensagem
