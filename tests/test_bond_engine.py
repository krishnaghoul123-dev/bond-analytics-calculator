import pytest

from bond_engine import Bond, duration_and_convexity, price_from_yield, shock_analysis, yield_to_maturity


def test_par_bond_prices_at_face_value():
    bond = Bond(1000, 0.08, 5, 2)
    assert price_from_yield(bond, 0.08) == pytest.approx(1000, abs=1e-8)


def test_ytm_round_trip():
    bond = Bond(1000, 0.08, 5, 2)
    price = price_from_yield(bond, 0.093)
    assert yield_to_maturity(bond, price) == pytest.approx(0.093, abs=1e-9)


def test_discount_bond_ytm_exceeds_coupon_rate():
    bond = Bond(1000, 0.08, 5, 2)
    assert yield_to_maturity(bond, 950) > 0.08


def test_duration_and_convexity_are_positive():
    metrics = duration_and_convexity(Bond(1000, 0.08, 5, 2), 0.09)
    assert 0 < metrics["modified_duration"] < metrics["macaulay_duration"] < 5
    assert metrics["convexity"] > 0


def test_convexity_improves_large_shock_estimate():
    result = shock_analysis(Bond(1000, 0.08, 10, 2), 0.09, 200)
    duration_error = abs(result["actual_change"] - result["duration_change"])
    convexity_error = abs(result["actual_change"] - result["duration_convexity_change"])
    assert convexity_error < duration_error


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        Bond(0, 0.08, 5, 2)
    with pytest.raises(ValueError):
        yield_to_maturity(Bond(1000, 0.08, 5, 2), 0)
