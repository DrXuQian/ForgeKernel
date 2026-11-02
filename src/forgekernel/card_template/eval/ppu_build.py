"""Trusted build adapter for a single PPU C++ PyTorch extension.

A task may replace this adapter with its own SDK build via [ppu].build.
The student edits the kernel, not this evaluator-owned file.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sysconfig

TARGETS = {"ppu10": "ppu_10", "ppu15": "ppu_15"}


def build_command(source: Path, output: Path, module: str, arch: str, *,
                  sdk: Path, torch_root: Path, python_include: str, abi: int,
                  actlize: Path | None = None) -> list[str]:
    if arch not in TARGETS:
        raise ValueError(f"unsupported PPU target {arch!r}")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", module):
        raise ValueError("invalid extension module name")
    includes = [sdk / "include", torch_root / "include",
                torch_root / "include/torch/csrc/api/include", Path(python_include)]
    if actlize is not None:
        includes.append(actlize / "include")
    lib = torch_root / "lib"
    command = [
        str(sdk / "bin/hgcc"), "-x", "hg", f"-arch={TARGETS[arch]}",
        "-DSWITCH_TO_HGGCRT", "-std=c++17", "-O3", "-shared",
        "-Xcompiler=-fPIC", f"-DTORCH_EXTENSION_NAME={module}",
        f"-D_GLIBCXX_USE_CXX11_ABI={abi}",
    ]
    for directory in includes:
        command += ["-I", str(directory)]
    command += ["-L", str(sdk / "lib"), "-L", str(lib),
                str(source), "-ltorch_python", "-ltorch", "-ltorch_cpu", "-lc10"]
    # Native SDK PyTorch distributions retain their own library naming.
    for name in ("torch_cuda", "c10_cuda", "torch_ppu", "c10_ppu"):
        if (lib / f"lib{name}.so").is_file():
            command.append(f"-l{name}")
    command += ["-o", str(output)]
    return command


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--arch", choices=tuple(TARGETS), required=True)
    args = parser.parse_args()
    sdk_text = os.environ.get("PPU_SDK", "")
    if not sdk_text:
        parser.error("PPU_SDK must name the installed native PPU SDK")
    sdk = Path(sdk_text).expanduser().resolve()
    if not (sdk / "bin/hgcc").is_file():
        parser.error(f"no native hgcc under {sdk}; select the matching PPU SDK")
    import torch
    actlize = os.environ.get("PPU_ACTLIZE_DIR")
    command = build_command(
        args.source.resolve(), args.output.resolve(), args.module, args.arch,
        sdk=sdk, torch_root=Path(torch.__file__).resolve().parent,
        python_include=sysconfig.get_paths()["include"],
        abi=int(torch._C._GLIBCXX_USE_CXX11_ABI),
        actlize=Path(actlize).expanduser().resolve() if actlize else None)
    print("PPU_BUILD_COMMAND=" + json.dumps(command), flush=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, check=False)
    if result.returncode:
        return result.returncode
    if not args.output.is_file():
        raise RuntimeError("PPU compiler returned success without the requested extension")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
