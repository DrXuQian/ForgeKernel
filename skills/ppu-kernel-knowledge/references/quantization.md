# Quantization, offline formats and GEMV

Sources: [S01, S08, S12, S13, S14](sources.md). Scope is the recorded Quactlize/PPU0010
format and reader work, with a separately scoped cache-topology reference.
Read the current producer, descriptor and selected kernel before applying a
historical configuration.

## Treat the format as an interface

Weights, scales, minima/zeros and packing metadata together define the stored
format. Preserve element/code/byte units through every pointer and descriptor.
Keep artifact axes (physical bytes/folds) distinct from tactic axes (the
kernel's tile, warps, stages and split). A new reader must consume the declared
artifact, not silently reinterpret it using its own tile constants.

TileK alone does not determine artifact compatibility. Compute the stored
code-slot map from the artifact's tile and folds, then the consumer map from
the proposed tactic. Compare the logical N/K coordinates at every slot,
including high planes, scales, tails and coverage. Preserve artifact-carried
folds rather than recompute them from the reader's TileK. A different TileK
can work when those maps agree; folding alone neither permits nor forbids it.
Historical cross-T witnesses established specific host mappings. A new reader
still needs its own complete mapping check and device validation.

Provide independent full-weight and scale/min recovery for an added format.
An end-to-end GEMM-only test cannot distinguish a packing error from a reader
error. A producer/consumer round trip that shares the same wrong mapping is
also insufficient; compare to an independent logical decode.

## Preserve the arithmetic contract

Storage dtype and compute dtype are separate. Dense F32 endpoints may use
F16 activation compute while a MoE route uses BF16. Changing an intermediate
cast, affine order, clipping or activation quantization changes the task.
For low-bit formats, code extraction, converter output order and scale/zero
ownership are distinct seams. A fast half2 bit-construction path does not imply
FP16 accumulation or remove FP32 affine work.

Q3/Q5/Q6 bitplanes can exploit native power-of-two delivery with a matched
converter. Their high/low planes, per-plane folds and N/K pairing must be
proved together. Avoid padding to a larger bitwidth just to reuse a kernel
unless the task permits the storage and performance tradeoff.

## Cold-weight experiments

Freeze precision, artifact bytes, logical workload, active experts, cache
policy and complete-call scope. Compare the current incumbent and relevant
raw-GGUF/K-pack or alternate reader on the same device and inputs. Include
Split-K reduction in full-call timing and retain a strong unsplit control.

Name the cache level being made cold and use its verified capacity with a
documented eviction/rotation protocol. The historical harness used a ring at
least 2.25 times the capacity it called L2, with complete traversals; that
setting does not establish the cache topology on another target. Official HGGC
[cache guidance](memory-hierarchy.md) distinguishes CE-shared L2 from LLC.
Exceeding only the nearby L2 cannot establish HBM-cold weights. Check the
selected SDK's capacity meaning, ACU's [cache policy](../../ppu-profiling/references/collection.md#cache-and-clock-policy), and available
miss/downstream-traffic evidence. Keep event timing distinct from ACU
forced-cold replay and model Asys timing. Alternate arms, retain raw
distributions and classify missing/invalid rows separately from regressions.

## Derive a candidate before measuring it

Write lane-to-N/K ownership, vector widths, plane alignment, unique/duplicate
requests, active lanes, passes, CTA count and reduction ownership. Do this for
A and metadata as well as B. Check emitted native loads against source intent.

GEMV can be limited by dequantization, metadata or instruction issue even when
its effective weight bandwidth looks low. Historical equal latencies across
different stored bitwidths motivated this diagnosis; they do not prove every
GEMV is ALU-bound. Check DRAM, the actual cache/interface counters, issue/stall
and occupancy evidence.
AIU/shared staging can save requests while adding barriers or address work.
Use the full measured call to select a winner.

Enumerate the intended axes and state pruning reasons. Retain per-case winners
and separate physically invalid mappings from merely slow measurements. A
passing M1 case does not admit a general M/grouped/format dispatch rule.
