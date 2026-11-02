# SPDX-License-Identifier: Apache-2.0
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/inspect_ppu.py"
spec = importlib.util.spec_from_file_location("inspect_ppu", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def record(ordinal=0, count=1, name="ZW810"):
    return probe.DEVICE_MARKER + json.dumps({
        "name": name, "ordinal": ordinal, "visible_devices": count})


@pytest.mark.parametrize("output", ["", record(1, 2), record() + "\n" + record(), record(0, 0)])
def test_missing_wrong_or_ambiguous_device_is_rejected(output):
    with pytest.raises(ValueError):
        probe.parse_device(output, 0)


def test_existing_evidence_is_not_overwritten(tmp_path):
    marker = tmp_path / "environment.json"
    marker.write_text("prior evidence")
    with pytest.raises(SystemExit) as exc:
        probe.main(["--sdk", "/unused-sdk", "--out", str(tmp_path)])
    assert exc.value.code == 2
    assert marker.read_text() == "prior evidence"


def test_failed_build_does_not_execute_a_stale_binary(tmp_path, monkeypatch):
    calls = []
    (tmp_path / "ppu_device_info").write_text("stale output")

    def run(command, out, label, timeout):
        calls.append(label)
        return {"status": "failed" if label == "device-query-build" else "ok", "output": ""}

    monkeypatch.setattr(probe, "run", run)
    report = probe.inspect(tmp_path / "sdk", 0, tmp_path, 1)
    assert report["status"] == "unavailable"
    assert report["device"] is None
    assert "device-query" not in calls


def test_runtime_failure_is_not_a_successful_environment(tmp_path, monkeypatch):
    def run(command, out, label, timeout):
        if label == "device-query-build":
            (out / "ppu_device_info").touch()
        return {"status": "failed" if label == "device-query" else "ok", "output": record()}

    monkeypatch.setattr(probe, "run", run)
    report = probe.inspect(tmp_path / "sdk", 0, tmp_path, 1)
    assert report["status"] == "unavailable"
    assert report["device"] is None


def test_missing_host_compiler_does_not_attempt_a_build(tmp_path, monkeypatch):
    calls = []

    def run(command, out, label, timeout):
        calls.append(label)
        return {"status": "unavailable" if label == "cxx" else "ok", "output": ""}

    monkeypatch.setattr(probe, "run", run)
    report = probe.inspect(tmp_path / "sdk", 0, tmp_path, 1)
    assert report["status"] == "unavailable"
    assert "device-query-build" not in calls


def test_host_query_can_identify_a_device_without_a_kernel_compiler(tmp_path, monkeypatch):
    commands = {}

    def run(command, out, label, timeout):
        commands[label] = command
        if label == "device-query-build":
            (out / "ppu_device_info").touch()
        return {"status": "unavailable" if label == "hgcc" else "ok",
                "output": record(1, 2, "M890") if label == "device-query" else ""}

    monkeypatch.setattr(probe, "run", run)
    report = probe.inspect(tmp_path / "sdk", 1, tmp_path, 1, cxx="/host/bin/g++")
    assert commands["device-query-build"][0] == "/host/bin/g++"
    assert commands["device-query"][-1] == "1"
    assert report["status"] == "runtime_queried"
    assert report["device"]["name"] == "M890"
    assert report["tools"]["hgcc"]["status"] == "unavailable"
    assert report["kernel_execution"] == "not_performed"


@pytest.mark.parametrize("name", ["ZW810", "M890", "Other PPU"])
def test_missing_profiler_does_not_hide_a_valid_runtime_query(tmp_path, monkeypatch, name):
    def run(command, out, label, timeout):
        if label == "device-query-build":
            (out / "ppu_device_info").touch()
        return {"status": "unavailable" if label in {"acu", "asys"} else "ok",
                "output": record(name=name) if label == "device-query" else ""}

    monkeypatch.setattr(probe, "run", run)
    report = probe.inspect(tmp_path / "sdk", 0, tmp_path, 1)
    assert report["status"] == "runtime_queried"
    assert report["device"]["name"] == name
    assert report["requested_target"] == "PPU"
    assert report["query_mode"] == "host_runtime_only"
    assert report["tools"]["acu"]["status"] == "unavailable"
    assert report["kernel_execution"] == "not_performed"
