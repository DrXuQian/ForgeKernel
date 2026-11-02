"""Native ACU CSV evidence; preserve PPU metric identities and units.

Only duration is normalized to the driver's existing nanosecond time fields.
Other PPU metrics are retained per launch rather than assigned NVIDIA names,
thresholds or aggregation rules.
"""
from __future__ import annotations

import csv
import io
import math

TIME = "ppu__time_duration.sum"
_NS = {"ns": 1, "nsecond": 1, "nanosecond": 1, "nanoseconds": 1,
       "us": 1e3, "µs": 1e3, "μs": 1e3, "usecond": 1e3,
       "microsecond": 1e3, "microseconds": 1e3,
       "ms": 1e6, "msecond": 1e6, "millisecond": 1e6,
       "milliseconds": 1e6, "s": 1e9, "second": 1e9, "seconds": 1e9}


def _number(value: str) -> float | None:
    try:
        result = float(value.replace(",", "").strip())
    except (ValueError, TypeError):
        return None
    return result if math.isfinite(result) else None


def launches_from_acu(text: str) -> list[dict]:
    if "PPU_PROFILE_UNAVAILABLE:" in text:
        return []
    header = None
    launches: dict[tuple, dict] = {}
    for cells in csv.reader(io.StringIO(text)):
        if "Metric Name" in cells and "Kernel Name" in cells:
            header = cells
            continue
        if header is None or len(cells) != len(header):
            continue
        row = dict(zip(header, cells))
        ident = row.get("ID", row.get("Kernel ID"))
        name, metric = row.get("Kernel Name", ""), row.get("Metric Name", "")
        if not ident or not name or not metric:
            continue
        key = (row.get("Process ID", ""), row.get("Context", ""), row.get("Stream", ""),
               ident, name)
        launch = launches.setdefault(key, {"name": name, "id": ident, "metrics": {}})
        value = _number(row.get("Metric Value", row.get("Value", "")))
        item = {"value": value, "unit": row.get("Metric Unit", row.get("Unit", "")),
                "raw": row.get("Metric Value", row.get("Value", ""))}
        previous = launch["metrics"].get(metric)
        if previous is not None and previous != item:
            return []  # ambiguous duplicate readings cannot define one launch
        launch["metrics"][metric] = item
    result = []
    for launch in launches.values():
        t = launch["metrics"].get(TIME, {})
        factor = _NS.get(str(t.get("unit", "")).strip().lower())
        value = t.get("value")
        if factor is None or value is None or value <= 0:
            # No partial window totals: missing or unknown time units would
            # silently omit launches and misidentify the dominant kernel.
            return []
        launch["time_ns"] = value * factor
        result.append(launch)
    return result


def kernels_from_acu(text: str) -> list[dict]:
    grouped: dict[str, dict] = {}
    for launch in launches_from_acu(text):
        row = grouped.setdefault(launch["name"], {"name": launch["name"], "launches": 0,
                                                 "time_ns": 0.0})
        row["launches"] += 1
        row["time_ns"] += launch["time_ns"]
    total = sum(r["time_ns"] for r in grouped.values())
    for row in grouped.values():
        row["pct"] = round(row["time_ns"] / total * 100, 2) if total else 0.0
    return sorted(grouped.values(), key=lambda r: r["time_ns"], reverse=True)


def profiler_from_acu(text: str, *, kernel: str | None = None) -> dict:
    launches = launches_from_acu(text)
    table = kernels_from_acu(text)
    if not launches or not table:
        return {}
    selected = next((r for r in table if r["name"] == kernel), None) if kernel else table[0]
    if selected is None:
        return {}
    native: dict[str, list] = {}
    for launch in launches:
        if launch["name"] == selected["name"]:
            for name, metric in launch["metrics"].items():
                native.setdefault(name, []).append({"launch_id": launch["id"], **metric})
    return {
        "backend": "acu", "kernel": selected["name"],
        "time_ns": selected["time_ns"] / selected["launches"],
        "dominant_launches": selected["launches"],
        "kernel_count": len(table), "total_launches": len(launches),
        "total_time_ns": sum(r["time_ns"] for r in table),
        "dominant_time_pct": table[0]["pct"],
        "ppu_metrics": native,
    }
