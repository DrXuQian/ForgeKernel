# Capture and read a PPU timeline

Sources: [S01, S08, S10](../../ppu-kernel-knowledge/references/sources.md).
The CLI below is the inspected Asys interface; recheck version/help on another
SDK. Select a new output directory in the task workspace.

## Capture and export

The established PPU runner uses the native runtime/HGTX/library trace categories:

```bash
"$PPU_SDK/asight/bin/asys" profile \
  --hggc-memory-usage=true -t hggc,hgtx,acdnn,acblas \
  -o "$REPORT_BASE" "$HARNESS" ...

"$PPU_SDK/asight/bin/asys" export -o "$SQLITE" "$ASYS_REPORT"
```

Fill in real harness arguments and the report filename emitted by that run.
The recorded exporter takes no `--type sqlite` option; do not transplant an
Nsight Systems command by renaming its executable. Inspect `asys --help export`
and `asys --help profile` for the installed version. Capture only the required
categories and workload interval. The task's existing wrapper may already
bind scopes and application inputs more precisely than a generic command.

Keep the original `.asysrep` and log. `stats`, `analyze` and `compare` may offer
useful summaries, but their rows still need a scope and device-activity check.
Use an existing compatible importer runtime if host libraries are too old.
Do not alter unrelated profiler services to repair a capture.

## Inspect the database before interpreting it

Open SQLite read-only. Enumerate tables/columns, resolve string IDs and verify
duration or start/end units from the exporter/schema. One recorded schema uses
`HGPTI_ACTIVITY_KIND_KERNEL`; do not hardcode NVIDIA `CUPTI_*` tables or assume
all Asys versions use the same column names.

Record the chosen table/name/time columns explicitly. In a historical capture,
timestamp-calibration failure left
thousands of host API rows but no device kernels. Report size and successful
export were not evidence of device timing. An empty device table remains a
failed capture for this question, not a reason to choose another populated table.

Confirm kernel names and expected activity count against the harness/trace.
Do not identify the target by the most frequent kernel: a launch-floor probe,
poison fill or witness kernel may dominate the counts. Exclude known harness
activities explicitly for kernel-only analysis, and list those exclusions.
Retain production helpers in a complete operator/model analysis.

## Attribute the correct interval

For each selected range, distinguish:

- Host API duration and launch/dispatch gaps.
- Individual device kernel durations and invocation counts.
- Copies and synchronization on the relevant dependency path.
- Elapsed operation/phase interval and overlap across streams/devices.

Use available correlation IDs and range markers; preserve ambiguous attribution
as unknown. For sequential kernels, a sum can describe device compute within
the range. For overlapping kernels, the sum double-counts overlap and is not
the range's elapsed time. Do not infer a critical path from a sorted duration
table alone. Compare matched ranges and disclose concurrent work.

Warmup/JIT exclusion must follow the recorded harness/range policy. Do not
drop the first activity merely because it is first. In a single-target
simulation workflow there is no repeated timing loop to strip.

If host launch cost dominates, inspect the API path; if a device kernel
dominates, select that exact specialization for ACU. Include the schema,
activity coverage and excluded harness work in the task's report. A route
fallback, missing activity or failed calibration invalidates that comparison.
