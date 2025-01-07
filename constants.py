# --- CONFIGURAÇÕES (estes valores podem ser ajustados no arquivo .env) ---
import os


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
