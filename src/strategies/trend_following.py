import pandas as pd
import numpy as np
from src.strategies.base import BaseStrategy


class EmaBreakoutStrategy(BaseStrategy):
    """
    Dual EMA Trend Filter + 20-period Donchian Channel Breakout.
    - Long when Fast EMA > Slow EMA and Close breaks above 20-period High.
    - Flat/Exit when Close crosses below Fast EMA.
    """

    def __init__(self, fast_ema: int = 12, slow_ema: int = 26, breakout_period: int = 20):
        super().__init__("EMA_Donchian_Trend", {
            "fast_ema": fast_ema,
            "slow_ema": slow_ema,
            "breakout_period": breakout_period
        })
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.breakout_period = breakout_period

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()

        # Moving averages
        data["ema_fast"] = data["close"].ewm(span=self.fast_ema, adjust=False).mean()
        data["ema_slow"] = data["close"].ewm(span=self.slow_ema, adjust=False).mean()

        # Donchian channel
        data["donchian_high"] = data["high"].rolling(window=self.breakout_period).max().shift(1)
        data["donchian_low"] = data["low"].rolling(window=self.breakout_period).min().shift(1)

        # Logic
        trend_up = data["ema_fast"] > data["ema_slow"]
        breakout_up = data["close"] > data["donchian_high"]
        exit_rule = data["close"] < data["ema_fast"]

        signals = np.zeros(len(data))
        current_pos = 0

        for i in range(len(data)):
            if current_pos == 0:
                if trend_up.iloc[i] and breakout_up.iloc[i]:
                    current_pos = 1
            elif current_pos == 1:
                if exit_rule.iloc[i]:
                    current_pos = 0
            signals[i] = current_pos

        data["signal"] = signals
        data["position_size"] = np.where(signals == 1, 0.95, 0.0)
        return data

