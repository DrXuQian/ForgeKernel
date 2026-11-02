"""PPU card entry: native SDK execution, event timing and ACU collection."""
from __future__ import annotations

GPU_ENTRY = r'''#!/bin/bash
# Native PPU card. The machine supplies its matching SDK, driver and PyTorch.
set -euo pipefail
WORKSPACE="$(cd "$(dirname "$0")" && pwd)"
cd "$WORKSPACE"
export PYTHONPATH="$WORKSPACE:$WORKSPACE/eval:${PYTHONPATH:-}"
export PYTHONUNBUFFERED=1
export FK_PPU_ARCH="@ARCH@"
export FK_LB_TIMER=events
export LB_CLOCK_STATE="PPU clocks managed by the task environment; no NVIDIA clock lock"
if [ -z "${PPU_SDK:-}" ]; then
    echo "PPU_ENV_UNAVAILABLE: set PPU_SDK and activate its matching runtime/PyTorch"
    exit 2
fi
if [ ! -x "$PPU_SDK/bin/hgcc" ]; then
    echo "PPU_ENV_UNAVAILABLE: selected SDK has no native hgcc"
    exit 2
fi
TASK="${1:-}"
shift || true
TASK_TIMEOUT="${TASK_TIMEOUT:-1800}"
run_with_timeout() {
    timeout --signal=KILL "$TASK_TIMEOUT" "$@"
}
profile_bounded() {
    if run_with_timeout "$@"; then return 0; fi
    echo "PPU_PROFILE_UNAVAILABLE: continuing with the clean benchmark only"
    return 0
}
case "$TASK" in
    correctness) run_with_timeout python3 eval/bench.py --mode correctness ;;
    perf|all)    run_with_timeout python3 eval/bench.py --mode all ;;
    cardref)     run_with_timeout python3 eval/bench.py --mode all --impl ref ;;
    ref)         run_with_timeout python3 eval/bench.py --mode ref ;;
    calibrate)   run_with_timeout python3 eval/bench.py --mode calibrate ;;
    acu|ncu)     profile_bounded python3 eval/ppu_profile.py ;;
    cmd)         run_with_timeout bash -c "$*" ;;
    *)           echo "Tasks: correctness, perf, all, cardref, ref, calibrate, acu, cmd"; exit 2 ;;
esac
echo "[gpu_entry.sh] task=$TASK finished"
'''


def render_gpu_entry(arch: str) -> str:
    if arch not in ("ppu10", "ppu15"):
        raise ValueError(f"unsupported PPU card architecture {arch!r}")
    return GPU_ENTRY.replace("@ARCH@", arch)
