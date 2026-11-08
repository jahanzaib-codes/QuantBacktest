import numpy as np
import pandas as pd
from typing import Dict, Any, List
from config.settings import settings


class PerformanceAnalytics:
    """Computes comprehensive quantitative risk and performance metrics."""

    def __init__(self, risk_free_rate: float = settings.risk_free_rate):
        self.risk_free_rate = risk_free_rate

    def calculate_metrics(
        self,
        equity_curve: pd.Series,
        trades: List[Dict[str, Any]],
        periods_per_year: int = 252
    ) -> Dict[str, Any]:
        """Calculates full hedge-fund tier performance tear-sheet metrics."""
        if len(equity_curve) < 2:
            return {}

        returns = equity_curve.pct_change().dropna()
        n_periods = len(returns)
        years = max(0.1, n_periods / periods_per_year)

        initial = equity_curve.iloc[0]
        final = equity_curve.iloc[-1]
        total_return_pct = ((final - initial) / initial) * 100.0

        # CAGR
        cagr_pct = ((final / initial) ** (1.0 / years) - 1.0) * 100.0

        # Volatility
        daily_std = returns.std()
        ann_volatility_pct = daily_std * np.sqrt(periods_per_year) * 100.0

        # Sharpe Ratio
        rf_daily = (1.0 + self.risk_free_rate) ** (1.0 / periods_per_year) - 1.0
        excess_returns = returns - rf_daily
        sharpe = (excess_returns.mean() / (daily_std + 1e-9)) * np.sqrt(periods_per_year)

        # Sortino Ratio (downside risk only)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 1e-9
        sortino = (excess_returns.mean() / (downside_std + 1e-9)) * np.sqrt(periods_per_year)

        # Drawdown analysis
        cum_max = equity_curve.cummax()
        drawdown_series = (equity_curve - cum_max) / cum_max
        max_drawdown_pct = abs(drawdown_series.min()) * 100.0

        # Calmar Ratio
        calmar = (cagr_pct / (max_drawdown_pct + 1e-9)) if max_drawdown_pct > 0 else 0.0

        # Value at Risk (VaR 95%) and CVaR
        var_95_pct = abs(np.percentile(returns, 5)) * 100.0
        tail_returns = returns[returns <= np.percentile(returns, 5)]
        cvar_95_pct = abs(tail_returns.mean()) * 100.0 if len(tail_returns) > 0 else var_95_pct

        # Trade statistics
        total_trades = len(trades)
        if total_trades > 0:
            winners = [t for t in trades if t["pnl_usd"] > 0]
            losers = [t for t in trades if t["pnl_usd"] <= 0]

            win_rate_pct = (len(winners) / total_trades) * 100.0
            gross_profit = sum(t["pnl_usd"] for t in winners)
            gross_loss = abs(sum(t["pnl_usd"] for t in losers))

            profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 99.99
            avg_win = (gross_profit / len(winners)) if len(winners) > 0 else 0.0
            avg_loss = (gross_loss / len(losers)) if len(losers) > 0 else 0.0
            payoff_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0.0
            expectancy = sum(t["pnl_usd"] for t in trades) / total_trades
            avg_duration = sum(t["duration_bars"] for t in trades) / total_trades
        else:
            win_rate_pct = 0.0
            profit_factor = 0.0
            payoff_ratio = 0.0
            expectancy = 0.0
            avg_duration = 0.0

        return {
            "initial_equity": round(initial, 2),
            "final_equity": round(final, 2),
            "total_return_pct": round(total_return_pct, 2),
            "cagr_pct": round(cagr_pct, 2),
            "annualized_volatility_pct": round(ann_volatility_pct, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "var_95_daily_pct": round(var_95_pct, 2),
            "cvar_95_daily_pct": round(cvar_95_pct, 2),
            "total_trades": total_trades,
            "win_rate_pct": round(win_rate_pct, 2),
            "profit_factor": round(profit_factor, 2),
            "payoff_ratio": round(payoff_ratio, 2),
            "expectancy_usd": round(expectancy, 2),
            "avg_trade_duration_bars": round(avg_duration, 1)
        }


analytics = PerformanceAnalytics()

