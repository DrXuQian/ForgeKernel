<!-- SPDX-License-Identifier: Apache-2.0 -->

# ACU metrics and statistics rules

Sources: [S10, S14](../../ppu-kernel-knowledge/references/sources.md), SDK2.1.1,
ACU `v2.1.1_20260725-15d8b9d`, data15000. These names were found in an actual
report and checked against installed sections where applicable. They are lookup
examples, not a complete or cross-version metric contract.

| Question | Observed ACU metric |
|---|---|
| Instrumented duration | `ppu__time_duration.sum` |
| Achieved occupancy | `cu__warps_active.avg.pct_of_peak_sustained_active` |
| Active warps/CU | `cu__warps_active.avg.per_cycle_active` |
| Native executed instructions | `pu__inst_executed.sum` |
| Register allocation | `launch__registers_per_thread` |
| Register/shared residency limits | `launch__occupancy_limit_registers`, `launch__occupancy_limit_shared_mem` |
| KVD load-side traffic toward L2 | `kvd__bytes_load_pipe_l2.sum` |
| DRAM bytes read | `dram__bytes_read.sum` |
| LLC request hit rate | `llc__requests_hit_rate.pct` |
| LLC/Fabric global-load bytes | `llc__bytes_pipe_fabric_mem_global_op_ld.sum` |
| LLC/Fabric global-store bytes | `llc__bytes_pipe_fabric_mem_global_op_st.sum` |
| LLC load misses toward DRAM | `llc__transactions_pipe_dram_mem_global_op_ld_lookup_miss.sum` |
| AIU load transactions | `aiu__transactions_load.avg` |
| Shared-load bank conflicts | `tsm__bank_conflicts_pipe_lsu_mem_shared_op_ld.sum` |
| Commit-dependency stall ratio | `pu__we_average_warps_issue_stalled_commit_dependency_per_issue_active.ratio` |

The imported report had `ppu__time_duration.sum` and did not have the NVIDIA
example's `gpu__time_duration.sum`. Resolve units and aggregation from the
tool/metric definitions before converting values. Missing is not zero. The
`cu`, `pu`, `kvd`, `tsm` and `aiu` families are not a textual replacement of
NCU's SM/L1TEX families.

The official ACU memory chart identifies KVD as vector data cache and KSD as
scalar data cache, grouped with TSM in its L1 analysis view. HGGC documents
per-CU L1, CE-shared L2 and wider LLC; see [memory hierarchy](../../ppu-kernel-knowledge/references/memory-hierarchy.md).
Bind each counter to its endpoint, direction, aggregation, byte/transaction
unit and clock domain. KVD-to-L2 bytes are not HBM bytes. Do not derive LLC hits
by subtracting unmatched counters or add traffic measured at successive
boundaries. A combined read/write peak is not a read peak. SDK `l2CacheSize`
still needs a confirmed aggregation scope before use as a cache-capacity model.

Installed definitions are under `asight/sections`, including `SpeedOfLight`,
`Occupancy`, `InstructionStatistics`, `MemoryWorkloadAnalysis` and
`WarpStateStatistics`. Query only the needed metrics. `--query-metrics` is a
device-capability query; inspecting an existing report or section files does
not require initializing a PPU.

## Documented Python report interface

Asight2.2.0 documents `acu_report` under `$PPU_SDK/asight/extras/python`,
for Python 3.8+. Add the installed directory to `PYTHONPATH` when using it.
`load_report(path)` returns a context; enumerate ranges and actions before
selecting a kernel. An action exposes `metrics()` and `metric_by_name(name)`.
For a selected metric, retain `value()`, `unit()`, `description()` and
`rollup_operation()`. Typed accessors must match the metric's type.

This is an official PPU interface, not an inferred `ncu_report` compatibility
layer. It was absent from the local SDK2.1.1 installation used here, so these
API calls are documentation-backed rather than locally exercised. Use the
tested CSV/rule paths below where that module is unavailable. See the
[official reference](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=1&chapterId=721).

## Programmatic analysis through the SDK

This SDK ships `HgRules` and statistics scripts under
`asight/reports/compute_stats_rules`. The inspected `ExportMetricsByKernel.py`
obtains a context from the handle passed to its `apply` function, iterates
actions and reads `action.metrics()` or `action.metric_by_name(...)`. That is
the SDK's rule interface, not a verified standalone `ncu_report.load_report`
replacement.

Both commands below were exercised on an existing report, without a device
capture. Set new output paths in the task's analysis directory:

```bash
"$PPU_SDK/asight/bin/acu" --import "$REPORT" \
  --stats-rule "$PPU_SDK/asight/reports/compute_stats_rules/ExportMetricsByKernel.py" \
  --stats-rule-output "$METRICS_CSV" \
  --metrics ppu__time_duration.sum,pu__inst_executed.sum

"$PPU_SDK/asight/bin/acu" --import "$REPORT" \
  --stats-rule "$PPU_SDK/asight/reports/compute_stats_rules/StatsSassByStall.py" \
  --stats-rule-output "$STALL_CSV"
```

Review each rule's grouping, filters, range coverage and aggregation before
using its output as a denominator. `StatsSassByStall` contains configured
instruction-family and main-loop filters; successful execution does not prove
those heuristics describe every kernel. Native-source/PC attribution depends
on what was captured. Missing PC data cannot be manufactured by a rule.

Do not copy the SDK scripts into the framework merely to rename their imports.
Keep the installed rule version/digest with the analysis. An MCP adapter can
expose this same report query surface if needed, while returning original
metric names, units, report identity and the applied filters.
