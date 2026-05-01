from dataclasses import dataclass, field
from typing import List

@dataclass
class Asset:
    # Single asset in portfolio
    # Example: BTC, NIFTY50, GOLD

    name: str
    allocation_pct: float      # Example: 30 means 30%
    expected_crash_pct: float  # Example: -80 means 80% loss in crash

    def __post_init__(self):
        # allocation must be between 0 and 100
        if not (0 <= self.allocation_pct <= 100):
            raise ValueError(
                f"{self.name}: allocation_pct must be between 0 and 100"
            )

        # crash percentage should be negative or zero
        if self.expected_crash_pct > 0:
            raise ValueError(
                f"{self.name}: expected_crash_pct must be negative or zero"
            )


@dataclass
class Portfolio:
    # Complete portfolio details

    total_value_inr: float
    monthly_expenses_inr: float
    assets: List[Asset] = field(default_factory=list)

    def __post_init__(self):
        # total portfolio value cannot be negative
        if self.total_value_inr < 0:
            raise ValueError("Portfolio value cannot be negative")

        # monthly expenses cannot be negative
        if self.monthly_expenses_inr < 0:
            raise ValueError("Monthly expenses cannot be negative")

        # total asset allocation must be 100%
        total_allocation = sum(asset.allocation_pct for asset in self.assets)

        if self.assets and abs(total_allocation - 100) > 0.01:
            raise ValueError(
                f"Total asset allocation must be 100%, currently {total_allocation:.2f}%"
            )


def portfolio_from_dict(data: dict) -> Portfolio:
    # Convert dictionary into Portfolio object

    assets = []

    for item in data.get("assets", []):
        asset = Asset(
            name=item["name"],
            allocation_pct=item["allocation_pct"],
            expected_crash_pct=item["expected_crash_pct"]
        )
        assets.append(asset)

    portfolio = Portfolio(
        total_value_inr=data["total_value_inr"],
        monthly_expenses_inr=data["monthly_expenses_inr"],
        assets=assets
    )

    return portfolio