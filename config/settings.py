import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class BacktestSettings(BaseModel):
    """Configuration settings for QuantBacktest engine."""

    initial_capital: float = Field(default_factory=lambda: float(os.getenv("INITIAL_CAPITAL", "100000.0")))
    currency: str = Field(default_factory=lambda: os.getenv("ACCOUNT_CURRENCY", "USD"))
    benchmark: str = Field(default_factory=lambda: os.getenv("DEFAULT_BENCHMARK", "SPY"))

    # Broker & Execution Friction
    commission_per_share: float = Field(default_factory=lambda: float(os.getenv("DEFAULT_COMMISSION_PER_SHARE", "0.005")))
    commission_per_contract: float = Field(default_factory=lambda: float(os.getenv("DEFAULT_COMMISSION_PER_CONTRACT", "0.85")))
    slippage_bps: float = Field(default_factory=lambda: float(os.getenv("SLIPPAGE_BPS", "3.0")))
    margin_req_pct: float = Field(default_factory=lambda: float(os.getenv("MARGIN_REQUIREMENT_PCT", "0.25")))

    # Validation & Optimization
    monte_carlo_runs: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_MONTE_CARLO_RUNS", "1000")))
    wf_in_sample_days: int = Field(default_factory=lambda: int(os.getenv("WALK_FORWARD_IN_SAMPLE_DAYS", "252")))
    wf_out_sample_days: int = Field(default_factory=lambda: int(os.getenv("WALK_FORWARD_OUT_SAMPLE_DAYS", "63")))
    risk_free_rate: float = Field(default_factory=lambda: float(os.getenv("RISK_FREE_RATE_ANNUAL", "0.045")))

    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


settings = BacktestSettings()

