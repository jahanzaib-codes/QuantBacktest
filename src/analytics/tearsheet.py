from typing import Dict, Any


def generate_ascii_tearsheet(strategy_name: str, metrics: Dict[str, Any]) -> str:
    """Generates an institutional ASCII quant research tearsheet."""
    init_eq = metrics.get("initial_equity", 100000.0)
    fin_eq = metrics.get("final_equity", 0.0)
    tot_ret = metrics.get("total_return_pct", 0.0)
    cagr = metrics.get("cagr_pct", 0.0)
    ann_vol = metrics.get("annualized_volatility_pct", 0.0)
    sharpe = metrics.get("sharpe_ratio", 0.0)
    sortino = metrics.get("sortino_ratio", 0.0)
    calmar = metrics.get("calmar_ratio", 0.0)
    mdd = metrics.get("max_drawdown_pct", 0.0)
    trades = metrics.get("total_trades", 0)
    win_rate = metrics.get("win_rate_pct", 0.0)
    pf = metrics.get("profit_factor", 0.0)
    payoff = metrics.get("payoff_ratio", 0.0)
    exp = metrics.get("expectancy_usd", 0.0)
    var95 = metrics.get("var_95_daily_pct", 0.0)
    cvar95 = metrics.get("cvar_95_daily_pct", 0.0)

    tearsheet = f"""
================================================================================
                    QUANTITATIVE RESEARCH TEARSHEET
Strategy: {strategy_name:<30} Benchmark: SPY
================================================================================
PORTFOLIO CAPITAL & RETURNS                RISK & VOLATILITY ANALYTICS
---------------------------------------    -------------------------------------
Initial Capital:        ${init_eq:<12,.2f}  Annualized Volatility: {ann_vol:>10.2f}%
Final Equity:           ${fin_eq:<12,.2f}  Maximum Drawdown (MDD):{mdd:>10.2f}%
Total Net Return:        {tot_ret:>11.2f}%  Daily VaR (95% Conf):  {var95:>10.2f}%
CAGR (Annualized):       {cagr:>11.2f}%  Daily CVaR / Shortfall:{cvar95:>10.2f}%
Sharpe Ratio (Rf=4.5%):  {sharpe:>11.2f}   Calmar Ratio:          {calmar:>11.2f}
Sortino Ratio:           {sortino:>11.2f}

TRADE EXECUTION & MICROSTRUCTURE
--------------------------------------------------------------------------------
Total Completed Trades:  {trades:<10}  Win Rate (%):           {win_rate:.2f}%
Profit Factor:           {pf:<10.2f}  Payoff Ratio (Win/Loss):{payoff:.2f}
Trade Expectancy:       ${exp:<10.2f}  Avg Duration:           {metrics.get('avg_trade_duration_bars', 0)} bars
================================================================================
"""
    return tearsheet.strip()
