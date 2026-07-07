# pc/tests/test_spc_engine.py
# Run: pytest pc/tests/test_spc_engine.py -v
# ALL 7 TESTS MUST PASS BEFORE GOING TO THE HACKATHON.

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from spc_engine import CrushRiskEngine, SPCConfig


# ── Helpers ───────────────────────────────────────────────────────────────────
def engine_with_short_warmup(warmup: int = 10) -> CrushRiskEngine:
    return CrushRiskEngine(config=SPCConfig(warmup_samples=warmup))


def push_warmup(engine: CrushRiskEngine, value: int = 100, count: int = 12) -> None:
    """Drive engine past warmup with stable readings."""
    for _ in range(count):
        engine.update([value] * 8)


# ── Tests ─────────────────────────────────────────────────────────────────────
def test_warmup_always_zero_risk():
    """Risk must be 0 during warmup regardless of input."""
    e = engine_with_short_warmup()
    for _ in range(9):
        r = e.update([1023] * 8)
        assert r["risk"] == 0, f"Expected risk=0 during warmup, got {r['risk']}"
        assert r["warmup"] is True


def test_stable_baseline_no_alert():
    """Stable pressure matching baseline → no alert fired."""
    e = engine_with_short_warmup()
    push_warmup(e, value=200)
    for _ in range(20):
        r = e.update([200] * 8)
    assert r["alert"] is False, "Stable input should not trigger alert"
    assert r["risk"] < 30, f"Stable risk too high: {r['risk']}"


def test_sudden_spike_triggers_alert():
    """Sudden jump from low baseline to high pressure → alert fires."""
    e = engine_with_short_warmup()
    push_warmup(e, value=100)
    r = e.update([900] * 8)
    assert r["alert"] is True, "Sudden spike should trigger alert"
    assert r["risk"] > 60, f"Risk should be >60, got {r['risk']}"


def test_max_pressure_is_critical():
    """Maximum pressure on all sensors → critical flag set."""
    e = engine_with_short_warmup()
    push_warmup(e, value=100)
    r = e.update([1023] * 8)
    assert r["critical"] is True, "Max pressure should be critical"
    assert r["risk"] > 85, f"Critical risk should be >85, got {r['risk']}"


def test_recalibration_changes_thresholds():
    """Cloud recalibration must update engine configuration."""
    e = engine_with_short_warmup()
    original_sigma = e.cfg.ucl_sigma
    e.recalibrate({"ucl_sigma": 4.5, "alpha": 0.5})
    assert e.cfg.ucl_sigma == 4.5, "ucl_sigma not updated"
    assert e.cfg.alpha == 0.5, "alpha not updated"
    assert e.cfg.ucl_sigma != original_sigma, "Recalibration had no effect"


def test_risk_score_always_in_range():
    """Risk score must always be 0–100, for any input."""
    e = engine_with_short_warmup()
    push_warmup(e)
    for vals in [[0]*8, [512]*8, [1023]*8, [100, 900, 100, 900, 100, 900, 100, 900]]:
        r = e.update(vals)
        assert 0 <= r["risk"] <= 100, f"Risk {r['risk']} out of 0–100 range for input {vals}"


def test_partial_spike_moderate_risk():
    """Half sensors spiking → moderate risk, not critical."""
    e = engine_with_short_warmup()
    push_warmup(e, value=100)
    r = e.update([100, 100, 100, 100, 900, 900, 900, 900])
    assert r["risk"] > 20,  f"Partial spike risk too low: {r['risk']}"
    assert r["risk"] < 90,  f"Partial spike risk too high: {r['risk']}"
    assert r["critical"] is False, "Half-spike should not be critical"
