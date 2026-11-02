# PPU architecture reconnaissance

## Inputs

- Architecture reference: {ARCH_REF}
- Performance baseline: {REF_BASELINE}
- Timed-window contract: {WINDOW_CONTRACT}
- Policy: {META_MILESTONE_PATH}
- Milestone format: {MILESTONES_TEMPLATE_PATH}
- Target generation: {KB_ARCH}
- Recon tree: {RECON_DIR}
- Report: {RECON_REPORT}
- Candidate table: {CANDIDATES_PATH}
- Calculator location: {SIMULATOR_DIR}
- Probe rounds available: {MAX_RECON_ROUNDS}

## Method

Use the reference measurements already supplied. Confirm actual PPU identity,
SDK, compiler target, dispatched bodies, workload and window before interpreting
them. In source mode, use the PPU knowledge/profiling skills and relevant
history before selecting candidates. Record source section, original target,
evidence level, applicability and the experiment that can disprove a lesson.
Respect blackbox/source restrictions when that history is withheld.

Use ACU for native per-kernel counters, actual metric names and units.
Use hgobjdump on the actual loaded native artifact for instructions/resource
use; use Asys when the question concerns multiple stages, host gaps or overlap.
Preserve the profiler window and separate replay from clean benchmark timing.
NVIDIA SASS, NCU counters, warpgroup assumptions and fixed SM resource tables
are not PPU evidence. The NVIDIA-only frozen pricing/census tools are disabled.

Distinguish effective work from padding, repetition and issued work. Inspect
operand delivery, dataflow, copies, shared layouts, synchronization, grid
supply and residency. Record actual ownership and completion edges. Attribute
counter changes to a mechanism only with native code or a discriminating
control. Keep compiler acceptance, layout checks, device correctness and
measured performance separate.

Probe scripts run through the driver:

    RECON_REQUEST: notes/<name>.py

Do analysis in the job and print compact measured findings with raw report
paths. Do not invent hardware constants for an uncalibrated calculator.
Interface expressibility goes from installed public headers to a native
compile/ISA probe and finally device validation; record an actual failed
alternative before declaring a compiler or hardware limit.

## Deliverables

Write both report and candidate table. Mark observations [MEASURED, job N],
inferences [ESTIMATE] with their derivation and a falsifying observation, and
unavailable channels explicitly. Include compiler/dependency differences,
actual dispatch scope, intermediate producer/consumer ownership and the
current binding constraint.

Compare concrete architectures with native tile/stage/warp layout, CTA/grid,
shared/register budgets, movement, synchronization and epilogue contracts.
Mark facts [VERIFY: acu-direct], derived counter claims [VERIFY: acu-derived],
native lowering [VERIFY: native-isa-derived], numerical contracts
[VERIFY: correctness], and unresolved candidates [VERIFY: none].
Unmeasured claims do not become gate acceptance criteria.

The native write-up gate requires ACU-EVIDENCE: and NATIVE-ISA-EVIDENCE:
lines in the report. Each identifies the job/report and measured scope, or
says unavailable with the concrete reason and remaining unknowns. These
coverage statements do not certify a mechanism. Keep raw findings beside
them. Do not fabricate NVIDIA OK verdicts; its SASS/ROLE/PMTL instruments
are disabled for PPU.

Stop after both deliverables are written; further measurements belong to
the candidate or revision that needs them.
