import pandas as pd
import numpy as np
from typing import Dict, Any, List
from src.strategies.base import BaseStrategy
from src.engine.event_engine import BacktestEngine
from src.analytics.metrics import analytics


class WalkForwardOptimizer:
    """
    Institutional Walk-Forward Optimization (WFO) engine.
    Tests strategies on strictly out-of-sample forward windows to detect
    curve-fitting and calculate Walk-Forward Efficiency (WFE).
    """

    def __init__(self, in_sample_bars: int = 252, out_sample_bars: int = 63):
        self.in_sample_bars = in_sample_bars
        self.out_sample_bars = out_sample_bars
        self.engine = BacktestEngine()

    def run(self, df: pd.DataFrame, strategy_cls, param_grid: List[Dict[str, Any]]) -> Dict[str, Any]:
        n_bars = len(df)
        step_size = self.out_sample_bars
        windows: List[Dict[str, Any]] = []

        start_idx = 0
        while (start_idx + self.in_sample_bars + self.out_sample_bars) <= n_bars:
            is_start = start_idx
            is_end = start_idx + self.in_sample_bars
            oos_start = is_end
            oos_end = oos_start + self.out_sample_bars

            df_is = df.iloc[is_start:is_end]
            df_oos = df.iloc[oos_start:oos_end]

            # 1. In-sample optimization pass: find parameter set with highest Sharpe
            best_sharpe = -999.0
            best_params = param_grid[0] if param_grid else {}

            for p in param_grid:
                strat = strategy_cls(**p)
                sig_is = strat.generate_signals(df_is)
                res_is = self.engine.run(sig_is)
                met_is = analytics.calculate_metrics(res_is["equity_curve"], res_is["trades"])
                sh = met_is.get("sharpe_ratio", -999.0)
                if sh > best_sharpe:
                    best_sharpe = sh
                    best_params = p

            # 2. Out-of-sample forward test with the chosen best parameters
            strat_oos = strategy_cls(**best_params)
            sig_oos = strat_oos.generate_signals(df_oos)
            res_oos = self.engine.run(sig_oos)
            met_oos = analytics.calculate_metrics(res_oos["equity_curve"], res_oos["trades"])

            windows.append({
                "window": len(windows) + 1,
                "is_period": f"{df_is.index[0].strftime('%Y-%m-%d')} to {df_is.index[-1].strftime('%Y-%m-%d')}",
                "oos_period": f"{df_oos.index[0].strftime('%Y-%m-%d')} to {df_oos.index[-1].strftime('%Y-%m-%d')}",
                "best_params": best_params,
                "is_sharpe": best_sharpe,
                "oos_sharpe": met_oos.get("sharpe_ratio", 0.0),
                "is_cagr": met_is.get("cagr_pct", 0.0),
                "oos_cagr": met_oos.get("cagr_pct", 0.0),
                "oos_return_pct": res_oos.get("total_return_pct", 0.0)
            })

            start_idx += step_size

        if not windows:
            return {"error": "Insufficient data for walk-forward windows", "windows": []}

        # Calculate Walk-Forward Efficiency (WFE)
        avg_is_cagr = np.mean([w["is_cagr"] for w in windows])
        avg_oos_cagr = np.mean([w["oos_cagr"] for w in windows])
        wfe = (avg_oos_cagr / (avg_is_cagr + 1e-9)) * 100.0 if avg_is_cagr > 0 else 0.0

        is_robust = wfe >= 60.0

        return {
            "total_windows": len(windows),
            "in_sample_bars": self.in_sample_bars,
            "out_sample_bars": self.out_sample_bars,
            "walk_forward_efficiency_pct": round(wfe, 2),
            "is_statistically_robust": is_robust,
            "avg_in_sample_sharpe": round(np.mean([w["is_sharpe"] for w in windows]), 2),
            "avg_out_of_sample_sharpe": round(np.mean([w["oos_sharpe"] for w in windows]), 2),
            "windows": windows
        }

