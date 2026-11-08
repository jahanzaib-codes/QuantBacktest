import pandas as pd
import numpy as np
from src.strategies.base import BaseStrategy


class BollingerRsiMeanReversion(BaseStrategy):
    """
    Statistical Mean Reversion using Bollinger Bands and Relative Strength Index (RSI).
    - Long when Price touches Lower Band and RSI < 30 (Oversold).
    - Exit when Price returns to Middle Band (SMA 20) or RSI > 65.
    """

    def __init__(self, bb_period: int = 20, bb_std: float = 2.0, rsi_period: int = 14):
        super().__init__("Bollinger_RSI_MeanReversion", {
            "bb_period": bb_period,
            "bb_std": bb_std,
            "rsi_period": rsi_period
        })
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_period = rsi_period

    def _calculate_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss.replace(0, np.nan))
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return rsi.fillna(50.0)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()

        # Bollinger Bands
        sma = data["close"].rolling(window=self.bb_period).mean()
        std = data["close"].rolling(window=self.bb_period).std()
        data["bb_mid"] = sma
        data["bb_lower"] = sma - (self.bb_std * std)
        data["bb_upper"] = sma + (self.bb_std * std)

        # RSI
        data["rsi"] = self._calculate_rsi(data["close"], self.rsi_period)

        signals = np.zeros(len(data))
        current_pos = 0

        for i in range(len(data)):
            if pd.isna(data["bb_lower"].iloc[i]):
                continue

            close = data["close"].iloc[i]
            lower = data["bb_lower"].iloc[i]
            mid = data["bb_mid"].iloc[i]
            rsi = data["rsi"].iloc[i]

            if current_pos == 0:
                if close <= lower and rsi <= 35.0:
                    current_pos = 1
            elif current_pos == 1:
                if close >= mid or rsi >= 65.0:
                    current_pos = 0

            signals[i] = current_pos

        data["signal"] = signals
        data["position_size"] = np.where(signals == 1, 0.90, 0.0)
        return data

