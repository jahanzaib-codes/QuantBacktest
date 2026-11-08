#!/usr/bin/env python3
"""
==============================================================================
QuantBacktest CLI — Institutional Quantitative Research & Backtesting Suite
==============================================================================
"""

import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.data.loader import data_loader
from src.engine.event_engine import BacktestEngine
from src.strategies.trend_following import EmaBreakoutStrategy
from src.strategies.mean_reversion import BollingerRsiMeanReversion
from src.analytics.metrics import analytics
from src.analytics.tearsheet import generate_ascii_tearsheet
from src.optimization.walk_forward import WalkForwardOptimizer
from src.optimization.monte_carlo import MonteCarloSimulator

console = Console()


def run_single_strategy(strategy_name: str, symbol: str, start_date: str, end_date: str, run_mc: bool, run_wfo: bool):
    console.print(Panel.fit(
        f"[bold cyan]🧪 QuantBacktest — Strategy Execution: {strategy_name}[/bold cyan]\n"
        f"[dim]Asset: {symbol} | Period: {start_date} to {end_date}[/dim]",
        border_style="cyan"
    ))

    # 1. Load data
    df = data_loader.load_synthetic_data(symbol=symbol, start_date=start_date, end_date=end_date)
    console.print(f"[bold green]✓ Loaded {len(df):,} market bars for {symbol}[/bold green]")

    # 2. Select strategy
    if strategy_name.lower().startswith("trend") or strategy_name.lower().startswith("ema"):
        strategy = EmaBreakoutStrategy(fast_ema=12, slow_ema=26, breakout_period=20)
    else:
        strategy = BollingerRsiMeanReversion(bb_period=20, bb_std=2.0, rsi_period=14)

    # 3. Generate signals and backtest
    df_signals = strategy.generate_signals(df)
    engine = BacktestEngine()
    result = engine.run(df_signals)

    # 4. Metrics & Tearsheet
    metrics = analytics.calculate_metrics(result["equity_curve"], result["trades"])
    tearsheet_text = generate_ascii_tearsheet(strategy.name, metrics)
    console.print(f"\n[bold white]{tearsheet_text}[/bold white]\n")

    # 5. Monte Carlo Resampling
    if run_mc:
        console.print("[bold yellow]🎲 Running 1,000-Iteration Monte Carlo Risk Simulation...[/bold yellow]")
        mc = MonteCarloSimulator(n_simulations=1000)
        mc_res = mc.run(result["trades"])

        mc_table = Table(title="🎲 Monte Carlo Risk & Ruin Profile (1,000 Bootstraps)", header_style="bold magenta")
        mc_table.add_column("Confidence Metric", style="bold cyan")
        mc_table.add_column("Value", justify="right")

        mc_table.add_row("Median Final Equity (50th %)", f"${mc_res['median_final_equity']:,.2f}")
        mc_table.add_row("Worst-Case Equity (5th %)", f"${mc_res['worst_case_5th_pct_equity']:,.2f}")
        mc_table.add_row("Best-Case Equity (95th %)", f"${mc_res['best_case_95th_pct_equity']:,.2f}")
        mc_table.add_row("Median Max Drawdown", f"{mc_res['median_max_drawdown_pct']:.2f}%")
        mc_table.add_row("95th % Max Drawdown (Tail Risk)", f"[bold red]{mc_res['max_drawdown_95th_pct']:.2f}%[/bold red]")
        mc_table.add_row("Probability of 20% Drawdown", f"{mc_res['ruin_probability_20pct']:.2f}%")
        mc_table.add_row("Probability of 30% Drawdown", f"{mc_res['ruin_probability_30pct']:.2f}%")

        console.print(mc_table)

    # 6. Walk-Forward Optimization
    if run_wfo:
        console.print("\n[bold yellow]🔬 Running Out-of-Sample Walk-Forward Optimization (WFO)...[/bold yellow]")
        param_grid = [
            {"fast_ema": 8, "slow_ema": 21, "breakout_period": 15},
            {"fast_ema": 12, "slow_ema": 26, "breakout_period": 20},
            {"fast_ema": 20, "slow_ema": 50, "breakout_period": 30}
        ] if strategy_name.lower().startswith("trend") else [
            {"bb_period": 15, "bb_std": 1.8, "rsi_period": 10},
            {"bb_period": 20, "bb_std": 2.0, "rsi_period": 14},
            {"bb_period": 25, "bb_std": 2.2, "rsi_period": 20}
        ]

        wfo = WalkForwardOptimizer(in_sample_bars=252, out_sample_bars=63)
        strat_cls = EmaBreakoutStrategy if strategy_name.lower().startswith("trend") else BollingerRsiMeanReversion
        wfo_res = wfo.run(df, strat_cls, param_grid)

        if "windows" in wfo_res and wfo_res["windows"]:
            wfo_table = Table(title="🔬 Walk-Forward Out-of-Sample Performance", header_style="bold green")
            wfo_table.add_column("Window", justify="center")
            wfo_table.add_column("Out-of-Sample Period", justify="center")
            wfo_table.add_column("In-Sample Sharpe", justify="right")
            wfo_table.add_column("OOS Sharpe", justify="right")
            wfo_table.add_column("OOS Return %", justify="right")

            for w in wfo_res["windows"]:
                wfo_table.add_row(
                    str(w["window"]),
                    w["oos_period"],
                    f"{w['is_sharpe']:.2f}",
                    f"{w['oos_sharpe']:.2f}",
                    f"{w['oos_return_pct']:+.2f}%"
                )

            console.print(wfo_table)
            wfe = wfo_res["walk_forward_efficiency_pct"]
            status_style = "bold green" if wfo_res["is_statistically_robust"] else "bold yellow"
            console.print(f"[{status_style}]Walk-Forward Efficiency (WFE): {wfe:.1f}% (Robustness: {wfo_res['is_statistically_robust']})[/{status_style}]\n")


def compare_strategies(symbol: str):
    console.print(Panel.fit(
        f"[bold cyan]🏆 QuantBacktest — Strategy Leaderboard Comparison[/bold cyan]\n"
        f"[dim]Asset: {symbol} | Cross-Strategy Benchmarking[/dim]",
        border_style="cyan"
    ))

    df = data_loader.load_synthetic_data(symbol=symbol)
    strategies = [
        EmaBreakoutStrategy(fast_ema=12, slow_ema=26, breakout_period=20),
        BollingerRsiMeanReversion(bb_period=20, bb_std=2.0, rsi_period=14)
    ]

    table = Table(title="📊 Cross-Strategy Quantitative Comparison", header_style="bold magenta")
    table.add_column("Strategy", style="bold cyan")
    table.add_column("Total Return", justify="right")
    table.add_column("CAGR", justify="right")
    table.add_column("Sharpe Ratio", justify="right", style="bold green")
    table.add_column("Sortino", justify="right")
    table.add_column("Max DD", justify="right", style="bold red")
    table.add_column("Win Rate", justify="right")
    table.add_column("Profit Factor", justify="right")
    table.add_column("Trades", justify="right")

    engine = BacktestEngine()
    for s in strategies:
        df_sig = s.generate_signals(df)
        res = engine.run(df_sig)
        m = analytics.calculate_metrics(res["equity_curve"], res["trades"])

        table.add_row(
            s.name,
            f"{m['total_return_pct']:+.2f}%",
            f"{m['cagr_pct']:.2f}%",
            f"{m['sharpe_ratio']:.2f}",
            f"{m['sortino_ratio']:.2f}",
            f"{m['max_drawdown_pct']:.2f}%",
            f"{m['win_rate_pct']:.1f}%",
            f"{m['profit_factor']:.2f}",
            str(m['total_trades'])
        )

    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="QuantBacktest Institutional CLI")
    parser.add_argument("--strategy", type=str, default="trend", choices=["trend", "mean_reversion", "compare"], help="Strategy to test")
    parser.add_argument("--symbol", type=str, default="SPY", help="Ticker symbol")
    parser.add_argument("--start", type=str, default="2023-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2026-01-01", help="End date (YYYY-MM-DD)")
    parser.add_argument("--mc", action="store_true", default=True, help="Run Monte Carlo simulation")
    parser.add_argument("--wfo", action="store_true", default=True, help="Run Walk-Forward Optimization")

    args = parser.parse_args()

    if args.strategy == "compare":
        compare_strategies(args.symbol)
    else:
        run_single_strategy(args.strategy, args.symbol, args.start, args.end, args.mc, args.wfo)


if __name__ == "__main__":
    main()

