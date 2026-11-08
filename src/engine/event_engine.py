import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from config.settings import settings
from src.execution.broker_model import BrokerExecutionModel, broker_model


class BacktestEngine:
    """Institutional event simulation engine tracking portfolio equity and trade blotter."""

    def __init__(
        self,
        initial_capital: float = settings.initial_capital,
        broker: BrokerExecutionModel = broker_model
    ):
        self.initial_capital = initial_capital
        self.broker = broker

    def run(self, df_with_signals: pd.DataFrame, asset_class: str = "EQUITY") -> Dict[str, Any]:
        df = df_with_signals.copy()
        n = len(df)

        equity = np.zeros(n)
        cash = np.zeros(n)
        position = np.zeros(n)
        holdings = np.zeros(n)

        trades: List[Dict[str, Any]] = []

        current_cash = self.initial_capital
        current_shares = 0.0
        entry_price = 0.0
        entry_idx = 0
        entry_date = None

        total_commission = 0.0
        total_slippage = 0.0

        for i in range(n):
            date = df.index[i]
            close = df["close"].iloc[i]
            target_signal = df["signal"].iloc[i]

            # Current state valuation before execution
            current_holdings = current_shares * close
            current_equity = current_cash + current_holdings

            # Long entry trigger
            if current_shares == 0.0 and target_signal == 1:
                alloc = df.get("position_size", pd.Series(1.0, index=df.index)).iloc[i]
                target_capital = current_equity * alloc
                est_shares = target_capital / close

                fill_px, slip, comm = self.broker.calculate_execution(close, est_shares, "BUY", asset_class)
                actual_cost = est_shares * fill_px + comm

                if actual_cost <= current_cash:
                    current_shares = est_shares
                    current_cash -= actual_cost
                    entry_price = fill_px
                    entry_idx = i
                    entry_date = date
                    total_commission += comm
                    total_slippage += slip

            # Long exit trigger
            elif current_shares > 0.0 and target_signal == 0:
                fill_px, slip, comm = self.broker.calculate_execution(close, current_shares, "SELL", asset_class)
                proceeds = (current_shares * fill_px) - comm
                current_cash += proceeds
                total_commission += comm
                total_slippage += slip

                pnl_usd = (fill_px - entry_price) * current_shares - comm
                pnl_pct = ((fill_px - entry_price) / entry_price) * 100.0

                trades.append({
                    "entry_date": entry_date,
                    "exit_date": date,
                    "duration_bars": i - entry_idx,
                    "entry_price": round(entry_price, 2),
                    "exit_price": round(fill_px, 2),
                    "shares": round(current_shares, 2),
                    "pnl_usd": round(pnl_usd, 2),
                    "pnl_pct": round(pnl_pct, 2),
                    "commissions": round(comm, 2),
                    "slippage": round(slip, 2),
                    "is_winner": pnl_usd > 0
                })

                current_shares = 0.0
                entry_price = 0.0

            cash[i] = current_cash
            position[i] = current_shares
            holdings[i] = current_shares * close
            equity[i] = current_cash + holdings[i]

        df["cash"] = cash
        df["position"] = position
        df["holdings"] = holdings
        df["equity"] = equity
        df["returns"] = df["equity"].pct_change().fillna(0.0)

        return {
            "initial_capital": self.initial_capital,
            "final_equity": round(equity[-1], 2),
            "total_return_usd": round(equity[-1] - self.initial_capital, 2),
            "total_return_pct": round(((equity[-1] - self.initial_capital) / self.initial_capital) * 100.0, 2),
            "total_commissions": round(total_commission, 2),
            "total_slippage": round(total_slippage, 2),
            "equity_curve": df["equity"],
            "returns_series": df["returns"],
            "trades": trades,
            "dataframe": df
        }
