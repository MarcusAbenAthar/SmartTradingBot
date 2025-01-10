import logging
import time
from threading import Thread
from collections import defaultdict
import websocket
import json
from indicators import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_volatility,
    calculate_vwap,
    calculate_adx,
    calculate_stochastic,
    verificar_condicoes_entrada,
)
from telegram_alerts import enviar_mensagem_formatada

# Configuração de logs
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class WebSocketManager:
    def __init__(self, api_url, symbols, timeframe):
        self.api_url = api_url
        self.symbols = symbols
        self.timeframe = timeframe
        self.ws = None
        self.is_running = False
        self.threads = []
        self.data = defaultdict(list)
        self.NUM_MIN_VELAS = 20  # Número mínimo de velas para análise

    def connect(self):
        def _on_message(ws, message):
            self.on_message(ws, message)

        def _on_error(ws, error):
            logger.error(f"WebSocket Error: {error}")
            self.reconnect()

        def _on_close(ws, close_status_code, close_msg):
            logger.warning("WebSocket Closed")
            self.reconnect()

        def _on_open(ws):
            logger.info("WebSocket Connection Opened")
            self.subscribe()

        while True:
            try:
                self.ws = websocket.WebSocketApp(
                    self.api_url,
                    on_message=_on_message,
                    on_error=_on_error,
                    on_close=_on_close,
                )
                self.ws.on_open = _on_open
                self.ws.run_forever()
            except Exception as e:
                logger.error(f"Erro ao conectar ao WebSocket: {e}")
                time.sleep(5)

    def subscribe(self):
        for symbol in self.symbols:
            params = {
                "op": "subscribe",
                "args": [f"candle.{self.timeframe}.{symbol}"],
            }
            self.ws.send(json.dumps(params))
            logger.info(f"Inscrito no par: {symbol}")

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if "topic" in data and "candle" in data["topic"]:
                symbol = data["topic"].split(".")[-1]
                for candle in data["data"]:
                    self.data[symbol].append(candle)
                    if len(self.data[symbol]) > self.NUM_MIN_VELAS:
                        self.data[symbol].pop(0)
                self.process_data(symbol)
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")

    def process_data(self, symbol):
        try:
            velas_historico = self.data[symbol]
            if len(velas_historico) < self.NUM_MIN_VELAS:
                return

            prices = [float(c["close"]) for c in velas_historico]
            volumes = [float(c["volume"]) for c in velas_historico]

            sma = calculate_sma(prices)
            ema = calculate_ema(prices)
            rsi = calculate_rsi(prices)
            macd_line, macd_signal = calculate_macd(prices)
            upper_band, lower_band = calculate_bollinger_bands(prices)
            vwap = calculate_vwap(prices, volumes)
            adx = calculate_adx(velas_historico)
            stochastic_k, stochastic_d = calculate_stochastic(prices)

            result = verificar_condicoes_entrada(
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

            if result and result["entry_type"] != "No Signal":
                logger.info(f"Sinal encontrado para {symbol}: {result}")
                enviar_mensagem_formatada(
                    symbol,
                    result["entry_type"],
                    result.get("tps", []),
                    result.get("sl", None),
                    result.get("alavancagem", None),
                )
        except Exception as e:
            logger.error(f"Erro ao processar dados para {symbol}: {e}")

    def start(self):
        self.is_running = True
        thread = Thread(target=self.connect)
        thread.start()
        self.threads.append(thread)

    def stop(self):
        self.is_running = False
        if self.ws:
            self.ws.close()
        for thread in self.threads:
            thread.join()


# Configuração
API_URL = "wss://stream.bybit.com/realtime"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
TIMEFRAME = "1m"

if __name__ == "__main__":
    manager = WebSocketManager(API_URL, SYMBOLS, TIMEFRAME)
    manager.start()
