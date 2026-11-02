# FlashAttention

Sources: [S01, S02, S03, S05, S15](sources.md). Separate public PPU1.0/1.5
implementations from the historical PPU1.7 Hopper experiment below.

## Official PPU starting point

Use [t-head/flash-attention-for-sail v2.8.2](https://github.com/t-head/flash-attention-for-sail/tree/v2.8.2)
when the task needs an existing PPU implementation. Its README lists 810/810E
and M890 among supported products, FP16/BF16 forward/backward, head dimensions
up to 256, and FP8 forward for FA3. Feature availability still follows the
selected generation and dispatch: ppu001 does not gain tc02 FP8 from a broad
repository support statement. Inspect the exact build and specialization.

The public FA2/FA3 adaptation uses PPU operand delivery and scheduling. A
`hopper/` directory or FA3 algorithm does not make it the historical 10700
TMA/WGMMA port. Keep NVIDIA upstream as an algorithm/oracle reference and
validate the official PPU baseline before optimizing it.

## Algorithm contract

Preserve QK scaling, online maximum/denominator, old-output rescaling, PV
accumulation, output conversion and LSE convention. Record head layouts,
GQA mapping, causal alignment, sequence tails and mask semantics. Verify O
and LSE against an independent reference; finite output alone is insufficient.

For a causal mask optimization, establish equivalence from the caller's
semantics. An external bias, sliding window or different KV alignment may
invalidate a positional-only shortcut. Q/K/V strides and base offsets belong
in the fixture, especially for tails and distinct KV heads.

## Legacy PPU lessons

The standalone PPU0010 FA history found a useful combination: FP32 QK/PV
accumulators, persistent Q in shared memory, bounded K/V staging, a proven
MMA C-to-A probability bridge, boundary-only masks and workload-aware ordering.
These are hypotheses for a matching kernel, not a universal tile recipe.

Resource cliffs matter. In the recorded D128 case, adding a mask tile crossed
the shared-memory boundary and reduced resident CTAs even though it hid some
load latency. Prove the causal hint at the graph/caller and account for a
redundant mask scan in the complete call before adding more staging.

QK and PV have different operand roles. The V write/read transpose pairing
must match the tested PPU layout. The bridge from accumulator to next MMA A
is also target-specific; reuse the actual traits and mapping proof, not a
NVIDIA shuffle pattern. See [SageAttention](sage-attention.md).

## Historical PPU1.7 Hopper path

Start with the existing Hopper collective, TMA/WGMMA pipeline and scheduler.
Audit build target, dependency API, descriptors, barrier arrivals, retirement,
epilogue store and runtime SM count. A CTA barrier does not replace asynchronous
MMA completion. Validate all generated admitted bodies, including causal
specializations, and the actual host dispatch/link path.

The reviewed FA source admits fixed-length FP16/BF16 forward with D64/128/256,
ordinary GQA and tails. Other features require separate implementation/admission.
That source-level scope does not certify native PPU1.7 execution. In particular,
FP8, backward, paged/append KV and cluster features are not implied by a
successful fixed BF16 build.

For the recorded single-call simulation workflow, create data and the oracle
on CPU, copy prepared tensors, invoke the target once, and compare on CPU.
Audit API-side fills, metadata and auxiliary launches. Record actual simulator
model/frequency/SM/cache settings; Python elapsed time is not simulated time.

## Performance interpretation

Report useful versus issued arithmetic for causal/padded tiles. GQA reduces
KV storage but does not eliminate query-head arithmetic. Tile ordering may
affect imbalance and cache locality; the correct choice depends on the actual
scheduler/model. An optimization measured on NVIDIA or a different PPU model
needs matched PPU validation before promotion.
