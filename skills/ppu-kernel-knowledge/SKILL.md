---
name: ppu-kernel-knowledge
description: Research, write, port and debug PPU kernels. Use for NVIDIA-to-PPU migration, actlize/CUTLASS differences, CuTe numerical debugging, linear attention, FlashAttention, SageAttention, quantized GEMM/GEMV and MoE.
---

# PPU Kernel Knowledge

Use this collection for PPU reconnaissance and milestone decisions. Establish
the actual generation and implementation, then read the architecture page and
the relevant operator page before selecting the first candidate architecture.
These are documented contracts and scoped historical lessons, not automatically
certified entries in ForgeKernel's hardware knowledge base.

In ForgeKernel, this operator-history collection is available to source-mode
teachers. Preserve the student and blackbox boundaries; see
[ForgeKernel integration](references/forge-integration.md).

## Select a reference

| Task or symptom | Read |
|---|---|
| PPU target, MMA/copy semantics, native lowering, Hopper port | [Architecture](references/architecture.md) |
| TIX instruction selection, tc01/tc02, AIU tails, cache modifiers and async completion | [TIX porting](references/tix-porting.md) |
| CU/SM comparison, KVD/TSM, L2/LLC reuse, bandwidth scope | [Memory hierarchy](references/memory-hierarchy.md) |
| NVIDIA CUTLASS to actlize, builder dispatch, CuTe copy/fragment contracts | [CUTLASS and actlize](references/cutlass-porting.md) |
| Gated DeltaNet, chunking, recurrent state, WY/residual | [Linear attention](references/linear-attention.md) |
| Exact attention, online softmax, masks, GQA, FA2/FA3 | [FlashAttention](references/flash-attention.md) |
| Quantized attention, QK/PV split, bridge, FP8/FP4 | [SageAttention](references/sage-attention.md) |
| K-pack, GGUF, bitplanes, cold GEMV, scale/zero | [Quantization and GEMV](references/quantization.md) |
| Dense/grouped GEMM, MoE, tile and scheduler choices | [GEMM and MoE](references/gemm-moe.md) |
| Wrong values, fragment ownership, races, sub-byte pitches | [Numerical debugging](references/numerics.md) |
| Official manuals, public PPU backends, unresolved documentation conflicts | [Official documentation](references/official-docs.md) |

For text search, run `rg -n -i 'topic' references` from this skill's directory.
[Sources](references/sources.md) maps the included PPU documentation and official
public upstreams. Use official dependencies and keep necessary extensions in
the task workspace. The references contain the reusable findings; no personal
fork, private memory or globally installed skill is a reading prerequisite.
Historical evidence is not a new hardware-validation campaign.

## Apply a lesson

1. Match generation, SDK/backend, shape, dtype, layout and numerical schedule.
2. For a port, map the original algorithm and execution structure before
   replacing primitives. Separate a missing implementation from a hardware limit.
3. Classify the evidence: host/layout, native compile, simulator, device
   correctness, or measured performance. Record the reference path/section,
   original target, applicability and remaining checks in the recon report and
   candidates table before distilling M0.
4. Turn the lesson into a candidate mechanism and a check that can disprove it.
   Revisit the relevant references after profiling, a numerical failure or an
   unexpected regression; record why the next decision changed.
5. Feed validated decisions into the milestone. Later milestones tune inside
   the accepted M0 structure; a structural change returns to the teacher.
   Only a target-device probe can promote an operator-agnostic recipe to hw_kb.

Retain applicable NVIDIA algorithm and diagnosis methods, checking their
hardware premises on the selected PPU. NVIDIA-certified hw_kb recipes retain
their original target. The [official document map](references/official-docs.md)
records current evidence and unresolved questions.

Equal math does not guarantee equal operand delivery or rounding. Use actual
backend traits and native code, then validate on the requested PPU. For report
analysis, use [PPU profiling](../ppu-profiling/SKILL.md).
