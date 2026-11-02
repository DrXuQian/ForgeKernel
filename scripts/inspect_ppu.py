#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Record SDK tools and PPU runtime properties without launching a kernel."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


DEVICE_SOURCE = Path(__file__).with_name("ppu_device_info.cpp")
DEVICE_MARKER = "FORGE_PPU_DEVICE_JSON="


def run(command: list[str], out: Path, label: str, timeout: float) -> dict:
    record = {"command": command, "log": str(out / f"{label}.log")}
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=timeout, check=False)
        output = result.stdout
        record.update(returncode=result.returncode,
                      status="ok" if result.returncode == 0 else "failed")
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or b"") + b"\nCommand timed out.\n"
        record.update(returncode=None, status="timeout")
    except OSError as exc:
        output = str(exc).encode()
        record.update(returncode=None, status="unavailable")
    Path(record["log"]).write_bytes(output)
    record["output"] = output.decode("utf-8", errors="replace")
    return record


def parse_device(output: str, selected: int) -> dict:
    rows = [line[len(DEVICE_MARKER):] for line in output.splitlines()
            if line.startswith(DEVICE_MARKER)]
    if len(rows) != 1:
        raise ValueError("Runtime query did not return exactly one device record")
    device = json.loads(rows[0])
    if not isinstance(device, dict) or device.get("ordinal") != selected:
        raise ValueError("Runtime query returned the wrong device")
    count = device.get("visible_devices")
    if type(count) is not int or count <= selected or not device.get("name"):
        raise ValueError("Runtime query returned an invalid device identity")
    return device


def inspect(sdk: Path, device: int, out: Path, timeout: float, cxx: str = "c++") -> dict:
    report = {
        "requested_target": "PPU",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "sdk": str(sdk), "selected_device": device,
        "status": "unavailable", "device": None, "tools": {},
        "kernel_execution": "not_performed",
        "query_mode": "host_runtime_only",
    }
    locations = {
        "hgcc": [sdk / "bin/hgcc"],
        "hgobjdump": [sdk / "bin/hgobjdump"],
        "acu": [sdk / "asight/bin/acu"],
        "asys": [sdk / "asight/bin/asys"],
    }
    for name, candidates in locations.items():
        # Inspect the selected SDK tools. Profilers may be separately installed.
        if name in {"acu", "asys"} and shutil.which(name):
            candidates.append(Path(shutil.which(name)))
        executable = next((p for p in candidates if p.is_file() and os.access(p, os.X_OK)),
                          candidates[0])
        report["tools"][name] = run([str(executable), "--version"], out, name, timeout)

    report["tools"]["cxx"] = run([cxx, "--version"], out, "cxx", timeout)
    if report["tools"]["cxx"]["status"] != "ok":
        report["reason"] = "Host C++ compiler is unavailable; inspect cxx.log or pass --cxx"
        return report

    binary = out / "ppu_device_info"
    # Compile only the host runtime query. Selecting a device ISA belongs to
    # the task's kernel build, after the actual device has been identified.
    command = [cxx, "-DSWITCH_TO_HGGCRT", "-std=c++17", "-I", str(sdk / "include"),
               "-L", str(sdk / "lib"),
               str(DEVICE_SOURCE), "-Wl,--start-group", "-lhggc", "-lhggcrt1",
               "-Wl,--end-group", "-o", str(binary)]
    report["build"] = run(command, out, "device-query-build", timeout)
    if report["build"]["status"] != "ok" or not binary.is_file():
        report["reason"] = "Runtime query build failed; inspect device-query-build.log"
        return report

    report["runtime"] = run([str(binary), str(device)], out, "device-query", timeout)
    if report["runtime"]["status"] != "ok":
        report["reason"] = "PPU runtime/device query failed; inspect device-query.log"
        return report
    try:
        report["device"] = parse_device(report["runtime"]["output"], device)
    except (ValueError, TypeError) as exc:
        report["reason"] = str(exc)
        return report
    report["status"] = "runtime_queried"
    report["reason"] = (
        "Confirm the reported PPU model and select the matching kernel target in "
        "the task's build. Runtime properties do not validate a kernel, compiler "
        "device lowering or profiler capture."
    )
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", default=os.environ.get("PPU_SDK"),
                        help="Installed SDK root (default: PPU_SDK)")
    parser.add_argument("--device", type=int, default=0, help="Runtime-visible device ordinal")
    parser.add_argument("--cxx", default="c++",
                        help="Host C++ compiler executable for the query (default: c++)")
    parser.add_argument("--out", type=Path, required=True, help="New output directory in the task workspace")
    parser.add_argument("--timeout", type=float, default=60, help="Seconds allowed for each command")
    args = parser.parse_args(argv)
    if not args.sdk:
        parser.error("Set PPU_SDK or pass --sdk for the SDK installed on this machine")
    if args.device < 0 or args.timeout <= 0:
        parser.error("--device must be nonnegative and --timeout must be positive")
    out = args.out.expanduser().resolve()
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        parser.error("--out already exists; choose a new directory to preserve prior evidence")
    sdk = Path(args.sdk).expanduser().resolve()
    report = inspect(sdk, args.device, out, args.timeout, args.cxx)
    path = out / "environment.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['status']}: {path}")
    print(report["reason"])
    if report["device"]:
        print(json.dumps(report["device"], indent=2))
    for name, value in report["tools"].items():
        if value["status"] != "ok":
            print(f"{name}: {value['status']} (see {value['log']})")
    return 0 if report["status"] == "runtime_queried" else 1


if __name__ == "__main__":
    sys.exit(main())
