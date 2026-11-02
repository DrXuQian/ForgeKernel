# Dense GEMM, MoE and related operators

Sources: [S01, S02, S08](sources.md). These lessons come from PPU0010
Marlin, actlize/Quactlize mixed-input and grouped GEMM work. They are starting
hypotheses for the corresponding family, not constants for PPU1.7.

## Keep algorithm and backend layers explicit

Separate the kernel/scheduler/epilogue from format-specific operand delivery
and conversion. Dense and grouped problem shapes can share a collective where
the backend interfaces permit it. A missing loader hook is an implementation
cost; it is not proof that the hardware cannot support a format.
See [CUTLASS/actlize](cutlass-porting.md) for builder dispatch and extension seams.

Native packed readers, offline rearrangement and dequantize-then-dense are
different tradeoffs. Earlier native-format-only design notes precede the later
canonical K-pack implementation. Preserve the selected task's format contract
rather than imposing one historical strategy on every workload.

For a Marlin port, align warp-K splitting, reduction, copy cadence, dequantization
and accumulator chain, not just CTA geometry. A partially aligned mixed-input
path cannot establish that original Marlin's mechanism is ineffective on PPU.
Write the difference table and compare on the same PPU and workload.

## Shape, format and resource interactions

Decode, moderate-M and prefill may favor different paths. The crossover depends
on actual M/N/K, group size, precision and preparation cost. Measure the useful
range; do not freeze old M thresholds into a global selector without evidence.

Changing operand width changes delivered columns per load and therefore warp
geometry. The FP16-to-INT4 MoE history exposed an out-of-range column when the
old warp grid was reused. Stage count also interacts with format and tile
resources. A hand-picked table that silently fixes one axis can misattribute
its winner to bitwidth.

Account for A shared memory when B is compressed. A can dominate the shared
budget; increasing TileK may reduce occupancy even while improving B delivery.
Conversely, saving shared memory cannot increase achieved occupancy when the
available work is grid-limited. Compute both ceilings before proposing a change.

The one-row-A decode experiment succeeded with a complete plain-copy/read
contract. A stride-zero CuTe layout alone could not make a SWZL instruction
stop reading its physical rows. Keep the fragment-shaping layout distinct from
the aliased storage layout and preserve alignment of following shared members.
Its M=1 validity does not extend to multi-row GEMM.

## Grouped work and correctness

Use distinct expert weights/scales/zeros and poison inactive experts. Repeating
one expert's bytes across every expert cannot validate routing or expert pitch.
The historical int4 bug interpreted code count as byte count, sending expert e
to 2e and eventually outside the allocation. Test actual byte arithmetic at the
native boundary as well as logical scheduling coverage.

Record ragged expert-row distributions and tail work. Fewer M tiles, less
padding or lower theoretical traffic do not individually predict the winner.
For persistent scheduling, verify output coverage and synchronization, then
measure imbalance and the tail with the actual workload.

## Other operator lessons

- Integer MMQ and weight-only FP16 GEMM have different activation/arithmetic
  contracts. Do not merge their correctness or throughput claims.
- Vectorized conversion needs bit/rounding and tail checks. Its optimal grid
  can differ from a reduction-limited GEMV grid, so unroll factors do not transfer.
- Fusion must include gather, top-k/prepare, reduction and output costs in the
  declared API/model scope. A faster isolated GEMM may leave the model unchanged.

Use [PPU profiling](../../ppu-profiling/SKILL.md): Asys locates call overhead;
ACU investigates the selected device kernel.
