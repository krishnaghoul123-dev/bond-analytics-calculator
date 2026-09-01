"""Core fixed-income calculations for a plain-vanilla fixed-rate bond."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Bond:
    face_value: float
    coupon_rate: float
    years_to_maturity: float
    frequency: int = 2

    def __post_init__(self) -> None:
        if self.face_value <= 0:
            raise ValueError("Face value must be positive.")
        if self.coupon_rate < 0:
            raise ValueError("Coupon rate cannot be negative.")
        if self.years_to_maturity <= 0:
            raise ValueError("Years to maturity must be positive.")
        if self.frequency not in (1, 2, 4, 12):
            raise ValueError("Frequency must be 1, 2, 4, or 12.")
        periods = self.years_to_maturity * self.frequency
        if abs(periods - round(periods)) > 1e-9:
            raise ValueError("Maturity must contain a whole number of coupon periods.")

    @property
    def periods(self) -> int:
        return round(self.years_to_maturity * self.frequency)

    @property
    def coupon_payment(self) -> float:
        return self.face_value * self.coupon_rate / self.frequency

    def cash_flows(self) -> list[tuple[int, float]]:
        flows = [(period, self.coupon_payment) for period in range(1, self.periods + 1)]
        flows[-1] = (self.periods, flows[-1][1] + self.face_value)
        return flows


def _validate_yield(annual_yield: float, frequency: int) -> None:
    if not isfinite(annual_yield) or annual_yield <= -frequency:
        raise ValueError(f"Annual yield must be greater than {-frequency:.0f}.")


def price_from_yield(bond: Bond, annual_yield: float) -> float:
    """Return dirty price using a nominal annual yield compounded by frequency."""
    _validate_yield(annual_yield, bond.frequency)
    periodic_yield = annual_yield / bond.frequency
    return sum(cf / (1 + periodic_yield) ** period for period, cf in bond.cash_flows())


def yield_to_maturity(
    bond: Bond, market_price: float, tolerance: float = 1e-11, max_iterations: int = 250
) -> float:
    """Solve nominal annual YTM with a dependency-free bisection method."""
    if market_price <= 0:
        raise ValueError("Market price must be positive.")

    low = -0.999999 * bond.frequency
    high = 1.0
    while price_from_yield(bond, high) > market_price and high < 1_000:
        high *= 2
    if price_from_yield(bond, high) > market_price:
        raise ValueError("Could not bracket a yield for this price.")

    for _ in range(max_iterations):
        midpoint = (low + high) / 2
        midpoint_price = price_from_yield(bond, midpoint)
        if abs(midpoint_price - market_price) <= tolerance:
            return midpoint
        if midpoint_price > market_price:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2


def duration_and_convexity(bond: Bond, annual_yield: float) -> dict[str, float]:
    """Calculate Macaulay duration, modified duration, and annualized convexity."""
    _validate_yield(annual_yield, bond.frequency)
    m = bond.frequency
    periodic_yield = annual_yield / m
    price = price_from_yield(bond, annual_yield)

    weighted_time = 0.0
    convexity_numerator = 0.0
    for period, cf in bond.cash_flows():
        pv = cf / (1 + periodic_yield) ** period
        weighted_time += (period / m) * pv
        convexity_numerator += cf * period * (period + 1) / (1 + periodic_yield) ** (period + 2)

    macaulay = weighted_time / price
    modified = macaulay / (1 + periodic_yield)
    convexity = convexity_numerator / (price * m**2)
    return {
        "price": price,
        "macaulay_duration": macaulay,
        "modified_duration": modified,
        "convexity": convexity,
    }


def shock_analysis(bond: Bond, annual_yield: float, shock_bps: float) -> dict[str, float]:
    """Compare actual repricing with duration and duration-plus-convexity estimates."""
    delta_yield = shock_bps / 10_000
    metrics = duration_and_convexity(bond, annual_yield)
    original_price = metrics["price"]
    shocked_price = price_from_yield(bond, annual_yield + delta_yield)
    actual_change = shocked_price / original_price - 1
    duration_change = -metrics["modified_duration"] * delta_yield
    convexity_change = duration_change + 0.5 * metrics["convexity"] * delta_yield**2
    return {
        "shock_bps": shock_bps,
        "actual_price": shocked_price,
        "actual_change": actual_change,
        "duration_change": duration_change,
        "duration_convexity_change": convexity_change,
    }
