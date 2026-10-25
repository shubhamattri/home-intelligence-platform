from __future__ import annotations

import pytest

from real_estate_svc.domain.plot_build_cost import BUILD_PSF, plot_build_cost


def test_land_and_duty_use_the_plot_price() -> None:
    c = plot_build_cost(plot_sqft=1200, land_psf=10_000, builtup_sqft=2400)
    land = next(x for x in c.lines if x.label == "Plot price")
    stamp = next(x for x in c.lines if x.label.startswith("Stamp duty"))
    assert land.amount == 1_20_00_000
    assert stamp.amount == pytest.approx(1_20_00_000 * 0.05)


def test_guidance_value_overrides_when_higher() -> None:
    """Karnataka charges duty on the higher of consideration or guidance value."""
    c = plot_build_cost(
        plot_sqft=1200, land_psf=8_000, builtup_sqft=2400, guidance_value=1_50_00_000
    )
    stamp = next(x for x in c.lines if x.label.startswith("Stamp duty"))
    assert stamp.amount == pytest.approx(1_50_00_000 * 0.05)


def test_guidance_value_ignored_when_lower() -> None:
    c = plot_build_cost(
        plot_sqft=1200, land_psf=12_000, builtup_sqft=2400, guidance_value=50_00_000
    )
    stamp = next(x for x in c.lines if x.label.startswith("Stamp duty"))
    assert stamp.amount == pytest.approx(1200 * 12_000 * 0.05)


def test_works_contract_adds_gst_and_self_managed_does_not() -> None:
    a = plot_build_cost(1200, 10_000, 2400, gst_mode="self_managed")
    b = plot_build_cost(1200, 10_000, 2400, gst_mode="works_contract")
    assert not any("GST" in x.label for x in a.lines)
    gst = next(x for x in b.lines if "GST" in x.label)
    assert gst.amount == pytest.approx(2400 * BUILD_PSF["premium"] * 0.18)
    assert b.total > a.total


def test_sourced_and_estimated_split_covers_the_total() -> None:
    c = plot_build_cost(1200, 10_000, 2400)
    assert c.sourced_total + c.estimated_total == pytest.approx(c.total)
    assert c.estimated_total > 0, "interiors and fees must be visible as estimates"


def test_contingency_scales_with_everything_before_it() -> None:
    lo = plot_build_cost(1200, 10_000, 2400, contingency_pct=0.0)
    hi = plot_build_cost(1200, 10_000, 2400, contingency_pct=0.10)
    assert hi.total == pytest.approx(lo.total * 1.10)


def test_grade_changes_construction_cost() -> None:
    std = plot_build_cost(1200, 10_000, 2400, grade="standard").total
    lux = plot_build_cost(1200, 10_000, 2400, grade="luxury").total
    assert lux > std


def test_rejects_bad_inputs() -> None:
    with pytest.raises(ValueError):
        plot_build_cost(1200, 10_000, 2400, grade="palatial")
    with pytest.raises(ValueError):
        plot_build_cost(1200, 10_000, 2400, gst_mode="maybe")
