"""Load an evaluator-built native PPU extension without an NVIDIA fallback."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile

_MODULES: dict[tuple, object] = {}


def load_ppu_entry(path: Path, entry: str, config: dict):
    path = Path(path).resolve()
    arch = config.get("arch")
    if arch not in ("ppu10", "ppu15"):
        raise ValueError(f"PPU card has no supported native target: {arch!r}")
    builder = Path(__file__).with_name("ppu_build.py")
    if not builder.is_file():
        raise FileNotFoundError("the card's PPU build adapter is missing")
    source = path.read_bytes()
    digest = hashlib.sha256(source + builder.read_bytes()).hexdigest()
    key = (str(path), digest, arch, os.environ.get("PPU_SDK"),
           os.environ.get("PPU_ACTLIZE_DIR"))
    if key not in _MODULES:
        # Reuse within this process only. Each job rebuilds against its actual
        # SDK/dependencies, so an old binary cannot masquerade as a new target.
        root = os.environ.get("FK_KERNEL_BUILD_DIR")
        if root:
            Path(root).mkdir(parents=True, exist_ok=True)
        build = Path(tempfile.mkdtemp(prefix=f"fk_ppu_{arch}_{digest[:12]}_", dir=root))
        module = build.name
        staged = build / path.name
        staged.write_bytes(source)
        output = build / (module + (sysconfig.get_config_var("EXT_SUFFIX") or ".so"))
        command = [sys.executable, str(builder), "--source", str(staged),
                   "--output", str(output), "--module", module, "--arch", arch]
        result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                timeout=float(os.environ.get("FK_PPU_BUILD_TIMEOUT", "900")))
        (build / "build.log").write_text(result.stdout, encoding="utf-8")
        if result.returncode != 0 or not output.is_file():
            raise RuntimeError(f"PPU build failed (exit {result.returncode}); {build / 'build.log'}\n"
                               + result.stdout[-12000:])
        manifest = {"backend": "ppu", "arch": arch, "source_sha256": hashlib.sha256(source).hexdigest(),
                    "builder_sha256": hashlib.sha256(builder.read_bytes()).hexdigest(),
                    "module": module, "binary": str(output), "command": command}
        (build / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print("PPU_BUILD_MANIFEST=" + json.dumps(manifest), flush=True)
        spec = importlib.util.spec_from_file_location(module, output)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load native PPU extension {output}")
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
        _MODULES[key] = loaded
    function = getattr(_MODULES[key], entry, None)
    if not callable(function):
        raise AttributeError(f"the native PPU extension exports no callable {entry!r}")
    return function
