from typing import Dict, Any, Tuple
from config.settings import settings


class BrokerExecutionModel:
    """Simulates realistic broker market microstructure friction."""

    def __init__(
        self,
        commission_per_share: float = settings.commission_per_share,
        slippage_bps: float = settings.slippage_bps
    ):
        self.commission_per_share = commission_per_share
        self.slippage_bps = slippage_bps

    def calculate_execution(
        self,
        price: float,
        quantity: float,
        action: str,
        asset_class: str = "EQUITY"
    ) -> Tuple[float, float, float]:
        """
        Calculates realistic fill price, slippage drag, and commission costs.
        
        Returns:
            (fill_price: float, slippage_cost_usd: float, commission_cost_usd: float)
        """
        # Calculate slippage in price terms (bps = 1/10,000)
        slippage_factor = self.slippage_bps / 10000.0
        slippage_price_delta = price * slippage_factor

        if action.upper() == "BUY":
            fill_price = round(price + slippage_price_delta, 4)
        else:
            fill_price = round(price - slippage_price_delta, 4)

        slippage_cost = round(slippage_price_delta * quantity, 2)

        # Commission calculation based on asset class
        if asset_class.upper() == "FUTURES":
            commission = round(max(1.50, quantity * settings.commission_per_contract), 2)
        elif asset_class.upper() == "CRYPTO":
            # 5 bps exchange taker fee
            commission = round((price * quantity) * 0.0005, 2)
        else:
            # Equities: $0.005/share, min $1.00
            commission = round(max(1.00, quantity * self.commission_per_share), 2)

        return fill_price, slippage_cost, commission


broker_model = BrokerExecutionModel()

