# PPU memory hierarchy and the Hopper comparison

Sources: [S12, S13, S14](sources.md), reviewed on 2026-10-30. Official HGGC,
M890 and Asight documentation now establishes the topology and several roles
that the user-supplied `PPU架构与NVIDIA_SM对照.md` left open. The numeric
annotations from that unidentified diagram are retained separately below.
See the [official document map](official-docs.md) and
[target resource evidence](architecture.md#resources-and-evidence).

## Match roles and sharing domains

| PPU element | Documented role / NVIDIA comparison | Consequence for a port |
|---|---|---|
| CU | HGGC places a complete CTA on one CU, using 32-thread warps; broadly comparable to SM execution scope | Use the target's resource and allocation limits for occupancy. |
| WS and WE; repeated `P00, WS+2WE` labels | Scheduler and execution roles within an SM | A WE is not one CUDA Core or one SM. Repeated read/write drawings do not establish a partition count. |
| TSM | CTA-shared storage, separate from the global-cache hierarchy | Check both 32-bank/four-byte-bank behavior and generation-specific group contention. |
| KVD / KSD | Asight identifies vector/scalar data caches; HGGC places L1 at CU scope | Asight's L1 chart groups KVD, KSD and TSM for analysis; that does not imply Hopper's unified capacity pool or interchangeable NCU metrics. |
| CE-shared L2 | A cache near a group of compute units; M890 documents four-CU CEs | It is neither per-CU L1 nor the chip-wide NVIDIA L2. |
| LLC shared across CEs | Closest functional comparison to NVIDIA's chip-wide L2 | Revisit NVIDIA L2 reuse and weight-residency strategies at this sharing scope. |
| AIU / TFU | AIU moves tensors to TSM; TFU performs tensor computation | Keep data-delivery cost distinct from matrix execution throughput. |

Hopper's L1/texture/shared storage is a combined 256 KB pool per SM; its
shared-memory limits are 228 KB/SM and 227 KB/block, not an additional pool.
Hopper clusters also have explicit scheduling, distributed shared memory and
synchronization semantics. Four PPU CUs sharing a cache do not establish those
semantics. See the official [Hopper tuning guide](https://docs.nvidia.com/cuda/hopper-tuning-guide/index.html).
The [Nsight Compute SM model](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html#streaming-multiprocessor)
describes four SM subpartitions with schedulers; it does not determine PPU's
WS/WE organization or warp width.

The uploaded summary's illustrated global-read request path is
`WS -> AIU -> KVD -> L2 -> Fabric -> LLC -> external memory`; writes use
`WS -> LSU -> KVD` before that hierarchy. TSM has a separate execution-side
read/write path. These paths do not establish every opcode's cache/bypass
policy, write allocation, coherence or completion rules.

The official guides describe the L1/CE-L2/LLC hierarchy for ppu001/ppu0015;
M890's product table gives 39 CUs for OAM and 30 for M530 PCIe. Neither the
text nor its reviewed architecture figure binds the following 288 GB diagram
to those products. The runtime API calls `l2CacheSize` an L2 byte capacity,
without specifying per-CE versus aggregate scope; do not treat it as LLC size.

## Unidentified diagram annotations

The supplied summary does not identify its PPU SKU or generation. Its values
are not ZW810 defaults. Keep KB/MB/GB labels until their byte convention is confirmed.
Interface width, bytes per cycle, clock domain and sustained bandwidth are
different quantities.

| Interface or resource | Annotation in the summary | Interpretation boundary |
|---|---|---|
| Each CU's read interface from L2 | `2 * 128 B/cycle` | 256 B/cycle at that interface; simultaneous delivery to all four CUs is unproven. |
| Each CU's write interface to L2 | `2 * 32 B/cycle` | 64 B/cycle; the 4:1 read/write ratio is an interface ratio, not a measured kernel ratio. |
| Shared L2 and its Fabric link | 512 KB per four-CU group; 256 B/cycle with a bidirectional arrow | A group-shared downstream interface, not four independent HBM links. The arrow alone does not specify a per-direction peak. |
| LLC channels | 1 MB/channel, 32 channels/die; 64 B/cycle per channel to Fabric | Preserve channel, die and direction scopes; the total is not one channel's rate. |
| LLC aggregate | 64 MB; about 12 TB/s at 1.5 GHz, **read plus write** | Not a 12 TB/s read ceiling. Die count and aggregation still need confirmation. |
| LLC-to-memory-controller path | `3 * 32 B -> CDC -> 3 * 16 B -> CDC -> 3 * 32 B`; middle clock is higher | Compare width times the corresponding clock, not widths alone. |
| TSM to/from two WEs | Two 64 B read paths; two 32 B write paths | These are byte widths; binding them to the public bank/group model or CU-wide throughput requires the diagram's target. |
| HBM3 | 288 GB; 1 TiB/s per stack, 6 TiB/s total; 8 Gbps | Unidentified product and unresolved bandwidth units; do not use as a ZW810 roofline denominator. |

Four 256 B/cycle CU interfaces do not establish 1024 B/cycle through the
shared L2's Fabric link. Cache-hit delivery and miss/fill traffic have different
paths; internal banks, ports and arbitration also constrain concurrent hits.

The input records three useful consistency checks:

- Moving 512 B through 256 or 64 B/cycle takes 2 or 8 ideal transfer cycles.
  Neither is load-to-use latency. The separately annotated 20-cycle LSU/TSM
  pipeline latency is not HBM latency or an automatically additive term.
- One annotation combines `r+w=384 B` with `512 B / 128 B ~= 1.33`.
  The latter division is 4; dividing by 384 gives about 1.33. Its intended
  interface/aggregation remains unresolved. Likewise, 32 MB/die and 64 MB
  total are consistent with two dies but do not prove that configuration.
  Assuming 64 channels, 64 B/cycle **per direction** and 1.5 GHz yields
  6.144 TB/s per direction, or 12.288 TB/s combined; this is conditional
  arithmetic, not confirmation of those assumptions or a measurement.
- Assuming 1024 bits/stack at 8 Gbps/pin gives 1.024 TB/s/stack;
  six stacks give 6.144 TB/s, about 5.588 TiB/s. The input's 6 TiB/s label
  needs clarification. Comparing that label to a bidirectional LLC rate
  does not establish a twofold pure-read bandwidth advantage.

## Turn the topology into a candidate experiment

After binding the topology to the task's device, use it to frame a candidate:

| Question | Candidate and evidence |
|---|---|
| Does tile/expert ordering improve reuse? | Distinguish reuse within a CU group from reuse across the LLC. Compare schedules at equal work with relevant cache and DRAM counters; CTA order alone does not prove CU affinity. |
| Do intermediate outputs overload the write path? | Compare fusion or reduced materialization with the baseline, including registers, TSM, synchronization and complete-call time. Fewer stores can still lose through reduced residency. |
| Are weight accesses cold at the intended level? | Name that level, document working-set bytes and rotation/eviction, then check misses or downstream traffic where available. Exceeding the nearby L2 alone does not establish HBM-cold accesses. |
| Is traffic reduced or moved to another interface? | Compare useful bytes, KVD/L2 requests, available LLC traffic and DRAM traffic separately. Do not sum counters that count the same transfer at different boundaries. |

Record the hypothesis and its falsifying check in the task's draft/plan; use
the existing correctness and keep/revise/reject loop. See
[ACU metric interpretation](../../ppu-profiling/references/metrics.md) and
[cold-weight experiments](quantization.md#cold-weight-experiments).
Missing model identity prevents using the numeric table as a device spec;
it does not prevent building and measuring an otherwise supported ZW810 kernel.
