from __future__ import annotations

import pytest

from real_estate_svc.domain.valuation import implied_cagr, index_forward, value_independent_house


def test_index_forward_compounds_at_corridor_cagr() -> None:
    # Rs 1 Cr at 9% for 3 years.
    assert index_forward(1e7, 2023, 9.0, 2026) == pytest.approx(1e7 * 1.09**3)


def test_index_forward_same_year_is_identity() -> None:
    assert index_forward(5e6, 2026, 12.0, 2026) == 5e6


def test_index_forward_rejects_backwards_year() -> None:
    with pytest.raises(ValueError):
        index_forward(1e7, 2026, 9.0, 2020)


def test_implied_cagr_recovers_a_known_doubling() -> None:
    # Doubling over 8 years is ~9.05% a year.
    assert implied_cagr(1000, 2000, 8) == pytest.approx(9.05, abs=0.05)


def test_implied_cagr_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        implied_cagr(1000, 2000, 0)


def test_value_independent_house_splits_land_and_build() -> None:
    v = value_independent_house(
        asking=2.4e7,
        plot_sqft=1500,
        land_psf=5000,
        builtup_sqft=2200,
        grade="premium",
        furnishing=15e5,
    )
    assert v.land_value == 1500 * 5000
    assert v.build_value == 2200 * 2450  # midpoint of premium band
    assert v.component_fair == v.land_value + v.build_value + v.furnishing
    assert v.premium_pct > 0


def test_value_independent_house_flags_a_rich_premium() -> None:
    v = value_independent_house(
        asking=3e7, plot_sqft=1200, land_psf=3000, builtup_sqft=2000, grade="standard"
    )
    assert v.premium_pct > 80
    assert v.verdict == "very rich premium"


def test_value_independent_house_at_fair_value_reads_as_fair() -> None:
    fair = 1200 * 5000 + 2000 * 2450
    v = value_independent_house(asking=fair, plot_sqft=1200, land_psf=5000, builtup_sqft=2000)
    assert v.premium_pct == pytest.approx(0.0)
    assert v.verdict == "at or below fair build-up value"


def test_corridor_comparison_is_optional() -> None:
    v = value_independent_house(asking=2e7, plot_sqft=1200, land_psf=4000, builtup_sqft=2000)
    assert v.corridor_value is None and v.premium_over_corridor_pct is None
    v2 = value_independent_house(
        asking=2e7, plot_sqft=1200, land_psf=4000, builtup_sqft=2000, corridor_psf=6600
    )
    assert v2.corridor_value == 2000 * 6600
