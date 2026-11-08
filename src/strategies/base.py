from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any


class BaseStrategy(ABC):
    """Abstract base class for quantitative trading strategies."""

    def __init__(self, name: str, params: Dict[str, Any] = None):
        self.name = name
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Receives OHLCV dataframe and appends:
        - 'signal': 1 (Long), -1 (Short), 0 (Flat)
        - 'position_size': fraction of equity (0.0 to 1.0)
        """
        pass

