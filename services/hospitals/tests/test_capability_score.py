from __future__ import annotations

import pytest

from hospitals_svc.domain.capability_score import score_hospital

FULL = {
    "cath_lab_24x7": True,
    "cardiac_surgery": True,
    "stroke_ready": True,
    "trauma_emergency_24x7": True,
    "blood_bank": True,
    "nabh_or_jci_accredited": True,
}
# Sri Jayadeva: superb cardiac, no stroke or trauma service.
JAYADEVA = {
    "cath_lab_24x7": True,
    "cardiac_surgery": True,
    "stroke_ready": False,
    "trauma_emergency_24x7": False,
    "blood_bank": True,
    "nabh_or_jci_accredited": True,
}


def test_full_capability_hospital_scores_near_top_on_both() -> None:
    s = score_hospital("Full", FULL, beds=600)
    assert s.cardiac_emergency == pytest.approx(1.0)
    assert s.general_emergency == pytest.approx(1.0)


def test_cardiac_institute_beats_generalists_on_cardiac_and_loses_on_general() -> None:
    """The bug this module exists to fix."""
    jd = score_hospital("Sri Jayadeva", JAYADEVA, beds=1150)
    generalist = score_hospital("Mid generalist", FULL, beds=250)
    assert jd.cardiac_emergency > generalist.cardiac_emergency
    assert jd.general_emergency < generalist.general_emergency
    assert jd.cardiac_verdict == "primary cardiac destination"


def test_no_cath_lab_cannot_be_a_primary_cardiac_destination() -> None:
    caps = dict(FULL, cath_lab_24x7=False)
    s = score_hospital("No cath lab", caps, beds=600)
    assert s.cardiac_emergency < 0.65
    assert s.cardiac_verdict in {"stabilise and transfer", "not a cardiac destination"}
    # but it can still be fine for general emergencies
    assert s.general_emergency == pytest.approx(1.0)


def test_unknown_capability_scores_zero_and_is_reported_not_assumed() -> None:
    caps = dict(FULL)
    caps.pop("cath_lab_24x7")
    s = score_hospital("Unknown cath", caps, beds=600)
    assert "cath_lab_24x7" in s.unknowns
    assert s.cardiac_emergency == pytest.approx(0.60)


def test_volume_proxy_saturates_and_never_rescues_a_weak_hospital() -> None:
    big = score_hospital("Big", {"cath_lab_24x7": False}, beds=5000)
    assert big.cardiac_emergency <= 0.15 + 1e-9, "beds alone must not imply capability"
    a = score_hospital("A", FULL, beds=600).cardiac_emergency
    b = score_hospital("B", FULL, beds=6000).cardiac_emergency
    assert a == b, "volume credit must saturate"


def test_missing_capabilities_block_is_handled() -> None:
    s = score_hospital("Nothing known", None, beds=None)
    assert s.cardiac_emergency == 0.0
    assert s.cardiac_verdict == "not a cardiac destination"
    assert len(s.unknowns) >= 5


def test_elective_is_carried_through_separately_not_blended() -> None:
    s = score_hospital("X", FULL, beds=600, elective_score=0.3)
    assert s.elective == 0.3
    assert s.cardiac_emergency == pytest.approx(1.0), "comfort must not drag clinical score"
