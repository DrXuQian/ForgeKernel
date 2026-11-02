"""Collect native ACU CSV for the card's existing confined profile window."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def acu_executable() -> str:
    explicit = os.environ.get("FK_ACU")
    if explicit:
        return explicit
    sdk = os.environ.get("PPU_SDK")
    native = Path(sdk) / "asight/bin/acu" if sdk else None
    if native and native.is_file():
        return str(native)
    found = shutil.which("acu")
    if not found:
        raise FileNotFoundError("ACU is unavailable; set FK_ACU or use the installed PPU SDK")
    return found


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--probe", action="store_true")
    p.add_argument("--launch-count", type=int,
                   help="optional explicit cap; by default collect the complete confined window")
    args = p.parse_args()
    if args.launch_count is not None and args.launch_count <= 0:
        p.error("--launch-count must be positive")
    metrics = os.environ.get("FK_ACU_METRICS", "ppu__time_duration.sum")
    metrics = ",".join(dict.fromkeys(["ppu__time_duration.sum",
                                     *(m.strip() for m in metrics.split(",") if m.strip())]))
    app = "eval/ncu_probe.py" if args.probe else "eval/ncu_run.py"
    command = [acu_executable(), "--csv", "--page", "raw", "--metrics", metrics]
    if args.probe or args.launch_count is not None:
        command += ["--launch-count", str(1 if args.probe else args.launch_count)]
    if not args.probe:
        command += ["--profile-from-start", "off"]
    command += [sys.executable, app]
    print("FORGE_PPU_ACU_CSV", flush=True)
    result = subprocess.run(command, check=False)
    if result.returncode:
        print(f"PPU_PROFILE_UNAVAILABLE: ACU exited {result.returncode}", flush=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
