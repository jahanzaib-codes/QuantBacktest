import numpy as np
from typing import Dict, Any, List


class MonteCarloSimulator:
    """
    Monte Carlo trade resampling engine to evaluate risk of ruin,
    expected drawdown bands, and parameter stability.
    """

    def __init__(self, n_simulations: int = 1000, initial_capital: float = 100000.0, seed: int = 42):
        self.n_simulations = n_simulations
        self.initial_capital = initial_capital
        self.seed = seed
        np.random.seed(seed)

    def run(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not trades:
            return {
                "error": "No trades provided for Monte Carlo simulation",
                "max_drawdown_95th_pct": 0.0,
                "ruin_probability_20pct": 0.0
            }

        pnl_pcts = np.array([t["pnl_pct"] / 100.0 for t in trades])
        n_trades = len(pnl_pcts)

        final_equities = np.zeros(self.n_simulations)
        max_drawdowns = np.zeros(self.n_simulations)

        ruin_20pct_count = 0
        ruin_30pct_count = 0
        ruin_50pct_count = 0

        for s in range(self.n_simulations):
            # Resample trade returns with replacement
            simulated_returns = np.random.choice(pnl_pcts, size=n_trades, replace=True)

            # Cumulative equity curve
            equity_curve = self.initial_capital * np.cumprod(1.0 + simulated_returns)
            final_equities[s] = equity_curve[-1]

            # Drawdown calculation
            peaks = np.maximum.accumulate(equity_curve)
            drawdowns = (equity_curve - peaks) / peaks
            mdd = abs(np.min(drawdowns)) * 100.0
            max_drawdowns[s] = mdd

            if mdd >= 20.0:
                ruin_20pct_count += 1
            if mdd >= 30.0:
                ruin_30pct_count += 1
            if mdd >= 50.0:
                ruin_50pct_count += 1

        # Calculate percentile distributions
        return {
            "simulations_count": self.n_simulations,
            "sample_trades_count": n_trades,
            "median_final_equity": round(float(np.percentile(final_equities, 50)), 2),
            "worst_case_5th_pct_equity": round(float(np.percentile(final_equities, 5)), 2),
            "best_case_95th_pct_equity": round(float(np.percentile(final_equities, 95)), 2),
            "median_max_drawdown_pct": round(float(np.percentile(max_drawdowns, 50)), 2),
            "max_drawdown_95th_pct": round(float(np.percentile(max_drawdowns, 95)), 2),
            "ruin_probability_20pct": round((ruin_20pct_count / self.n_simulations) * 100.0, 2),
            "ruin_probability_30pct": round((ruin_30pct_count / self.n_simulations) * 100.0, 2),
            "ruin_probability_50pct": round((ruin_50pct_count / self.n_simulations) * 100.0, 2)
        }
