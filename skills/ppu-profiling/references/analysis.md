<!-- SPDX-License-Identifier: Apache-2.0 -->

# Diagnose the PPU kernel

Sources: [S01, S04, S06, S08, S12, S13, S14](../../ppu-kernel-knowledge/references/sources.md).
Use actual metric names and definitions from the captured ACU version.

| Dimension | Check | Avoid concluding from one number |
|---|---|---|
| Work and duration | Exact selected body, useful/issued work, launches, instrumented duration | A kernel-name match alone does not establish equal workload. |
| Residency and work supply | Grid/active warps, registers, shared storage, spills, CTA limits | Lower registers do not help a grid-limited workload automatically. |
| Arithmetic and delivery | Dynamic MMA/load/conversion/address work, native operand forms | Fewer static instructions do not establish a shorter critical dependency chain. |
| Memory hierarchy | Useful bytes, L1/KVD/KSD, CE-L2, LLC and DRAM traffic, vector widths, reuse | Use actual target definitions; successive interface counts are not additive HBM traffic. |
| Synchronization | Barrier counts, absolute waits, async completion and stage reuse | An unchanged barrier count can have a different waiting cost. |
| Publication and tails | Output stores, shared bank/group conflicts, inactive lanes/tiles | Removing a bank conflict need not remove group contention; padded/masked tensor work still executes. |

For a reuse or store-pressure hypothesis, first resolve the
[memory hierarchy](../../ppu-kernel-knowledge/references/memory-hierarchy.md)
on the selected target. The supplied diagram's narrower CU write interface
motivates checking materialization cost, not a universal fusion rule. Measure
all affected stages and residency. Distinguish near-CU reuse from LLC reuse;
a scheduler change alone does not establish where its CTAs ran.

## PPU counterexamples worth retaining

GDN split preparation reduced scalar publication amplification at the KVD
interface but increased total intermediate L2/DRAM traffic. The complete
prepare improved. This supports investigating publication and independent
resource budgets, not a universal rule to split kernels or minimize one byte
counter. Compare all contributing stages and include reference fills.

PPU SWZL loads with warp-varying cube bases can require a vector-to-scalar
address move. That is not necessarily fragment repair. A fixed-base control
removed that move without changing the load family. Inspect the instruction's
consumer and held-constant controls before naming its cause.

The quantized GEMV history includes low effective bandwidth with saturated
on-chip issue/dequant work. Inspect actual traffic and dynamic instructions.
`stored_weight_bytes / time` is modeled effective bandwidth, not a DRAM
measurement. Include scales/minima and distinct active-expert bytes in the
chosen byte model; do not add AIU traffic twice if a total already includes it.

Sage mixed INT8/FP16 attention needs separate QK, bridge and PV work accounting.
BF16-equivalent MFU is not its physical mixed-dtype SOL. A value above the
declared peak signals a work/time/denominator mismatch to resolve, not a win.

## Attribution and experiments

Separate observation, mechanism and hypothesis. Prefer a control that changes
one semantic seam. If removing an arithmetic use also lets the compiler remove
its load, it is not an arithmetic-only ablation. If layout, scheduling and
publication change together, report the scheme gain and leave individual
contributions unassigned until isolated.

Re-rank remaining phase cost after each measured change. Neither maximizing
occupancy nor minimizing instruction count is the goal; the task's declared
latency/throughput/quality metric is. Numerical failures invalidate timings.

Name the counters and values supporting each finding in the task's report.
Use Asys when the conclusion depends on launch gaps, overlap or full-call time.
