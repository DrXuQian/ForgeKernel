"""Native profiler evidence is not translated into NVIDIA counter semantics."""
import csv
import io
from types import SimpleNamespace

import pytest

from forgekernel.inner import acu, ncu
from forgekernel.loop.driver import _ncu_profiler
from test_loop_driver import FakeBackend


def log(*rows):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["ID", "Kernel Name", "Metric Name", "Metric Unit", "Metric Value"])
    writer.writerows(rows)
    return "FORGE_PPU_ACU_CSV\n" + stream.getvalue()


CSV = log(
    (0, "attention", acu.TIME, "us", "2"),
    (0, "attention", "aiu__native_active.avg", "%", "32.5"),
    (1, "attention", acu.TIME, "nsecond", "3,000"),
    (1, "attention", "aiu__native_active.avg", "%", "61"),
    (2, "epilogue", acu.TIME, "ms", "0.001"),
)


def test_native_duration_and_per_launch_metrics_survive_the_driver():
    prof = ncu.profiler_from_ncu(CSV)
    assert prof["backend"] == "acu" and prof["kernel"] == "attention"
    assert prof["time_ns"] == 2500
    assert prof["total_time_ns"] == 6000 and prof["total_launches"] == 3
    assert prof["kernel_count"] == 2 and prof["dominant_launches"] == 2
    assert "tensor_pct" not in prof
    items = prof["ppu_metrics"]["aiu__native_active.avg"]
    assert [(r["launch_id"], r["raw"], r["unit"]) for r in items] == [
        ("0", "32.5", "%"), ("1", "61", "%")]
    table = ncu.kernels_from_ncu(CSV)
    assert table[0]["time_ns"] == 5000 and table[0]["launches"] == 2
    assert not ncu.summarize_metrics(prof)["flags"]
    trace = ncu.render_ncu_trace([SimpleNamespace(iter=1, decision_id="D1.1", profiler=prof)])
    assert "aiu__native_active.avg" in trace and "32.5" in trace
    be = FakeBackend([], [CSV])
    ctx = SimpleNamespace(language="ppu", backend=be, ncu_retries=0,
                          orch_census=False, workspace="/nonexistent")
    assert _ncu_profiler(ctx, "branch", correctness=True)["backend"] == "acu"
    assert any("acu" in call for call in be.calls)


@pytest.mark.parametrize("unit,value", [("cycle", "3"), ("ns", "n/a"),
                                        ("ns", "NaN"), ("ns", "inf"),
                                        ("ns", "0"), ("ns", "-1")])
def test_incomplete_or_unusable_durations_cannot_define_a_partial_window(unit, value):
    text = log((0, "good", acu.TIME, "ns", "100"),
               (1, "unknown", acu.TIME, unit, value))
    assert not acu.profiler_from_acu(text)
    assert not acu.kernels_from_acu(text)


def test_missing_duration_ambiguous_duplicate_and_failed_profile_are_unavailable():
    assert not acu.profiler_from_acu(log((0, "k", "other", "%", "10")))
    assert not acu.profiler_from_acu(log((0, "k", acu.TIME, "ns", "10"),
                                       (0, "k", acu.TIME, "ns", "20")))
    assert not ncu.profiler_from_ncu(CSV + "\nPPU_PROFILE_UNAVAILABLE: replay failed\n")
    assert not acu.profiler_from_acu(CSV, kernel="absent")


def test_explicit_kernel_keeps_its_own_raw_metrics():
    prof = acu.profiler_from_acu(CSV, kernel="epilogue")
    assert prof["kernel"] == "epilogue" and prof["time_ns"] == 1000
    assert prof["ppu_metrics"][acu.TIME][0]["unit"] == "ms"
