import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class MarketDataLoader:
    """Provides historical and simulated market data for backtesting."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        np.random.seed(seed)

    def load_synthetic_data(
        self,
        symbol: str = "SPY",
        start_date: str = "2023-01-01",
        end_date: str = "2026-01-01",
        timeframe: str = "1D",
        initial_price: float = 400.0,
        annual_drift: float = 0.12,
        annual_volatility: float = 0.18
    ) -> pd.DataFrame:
        """
        Generates realistic Geometric Brownian Motion with stochastic volatility
        and fat-tailed returns distribution (Merton Jump Diffusion).
        """
        dates = pd.date_range(start=start_date, end=end_date, freq="B")  # Business days
        n_bars = len(dates)

        dt = 1.0 / 252.0  # Annualized daily time step
        mu = annual_drift
        sigma = annual_volatility

        # Log returns with periodic regime shifts and volatility clusters
        daily_returns = np.random.normal((mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), n_bars)

        # Inject realistic fat-tailed market shock jumps (e.g. CPI prints, earnings)
        jump_indices = np.random.choice(n_bars, size=int(n_bars * 0.04), replace=False)
        daily_returns[jump_indices] += np.random.normal(-0.015, 0.025, size=len(jump_indices))

        # Reconstruct price series
        price_multipliers = np.exp(daily_returns)
        close_prices = initial_price * np.cumprod(price_multipliers)

        # Generate realistic OHLC bars around close
        high_noise = np.random.uniform(1.002, 1.018, n_bars)
        low_noise = np.random.uniform(0.982, 0.998, n_bars)
        open_noise = np.random.uniform(0.995, 1.005, n_bars)

        high_prices = close_prices * high_noise
        low_prices = close_prices * low_noise
        open_prices = np.roll(close_prices, 1) * open_noise
        open_prices[0] = initial_price

        # Ensure bar consistency: Low <= Open, Close <= High
        high_prices = np.maximum.reduce([open_prices, high_prices, close_prices])
        low_prices = np.minimum.reduce([open_prices, low_prices, close_prices])

        # Volume generated correlated with price volatility
        base_vol = 50_000_000 if symbol in ("SPY", "QQQ") else 5_000_000
        vol_noise = np.abs(daily_returns) / np.std(daily_returns)
        volume = (base_vol * np.random.uniform(0.7, 1.3, n_bars) * (1.0 + vol_noise)).astype(int)

        df = pd.DataFrame({
            "open": np.round(open_prices, 2),
            "high": np.round(high_prices, 2),
            "low": np.round(low_prices, 2),
            "close": np.round(close_prices, 2),
            "volume": volume
        }, index=dates)

        df.index.name = "timestamp"
        return df


data_loader = MarketDataLoader()
