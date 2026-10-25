from __future__ import annotations

import pytest

from platform_common.http import CircuitBreaker


def test_breaker_opens_after_fail_max() -> None:
    b = CircuitBreaker(fail_max=3, reset_s=100)
    assert b.allow()
    for _ in range(3):
        b.record_failure()
    assert not b.allow()


def test_breaker_success_resets() -> None:
    b = CircuitBreaker(fail_max=2, reset_s=100)
    b.record_failure()
    b.record_success()
    b.record_failure()
    assert b.allow()  # only 1 consecutive failure, not tripped


def test_breaker_half_open_after_reset() -> None:
    b = CircuitBreaker(fail_max=1, reset_s=0.0)
    b.record_failure()
    # reset_s = 0 means it immediately half-opens
    assert b.allow()


@pytest.mark.parametrize("fails", [0, 1, 2])
def test_breaker_stays_closed_below_threshold(fails: int) -> None:
    b = CircuitBreaker(fail_max=3, reset_s=100)
    for _ in range(fails):
        b.record_failure()
    assert b.allow()
