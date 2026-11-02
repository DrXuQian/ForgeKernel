# PPU architecture and porting

Sources: [S01, S02, S03, S04, S05, S07, S08, S11, S12, S13, S14](sources.md). Scope: the
inspected PPU backend/SDK revisions, official manuals and scoped hardware summary.
Hardware capabilities and resource limits must be revalidated for a different
target.

## Select the actual backend

| Target | Historical programming path | Decision-changing boundary |
|---|---|---|
| PPU1.0 / ACOMPUTE10000 / PPU0010; public ISA name `ppu001` | ZW810/610 and E variants; tc01 register MMA, AIU/SWZL and plain async copy | Fragment maps and target selection differ from NVIDIA SM80 despite frontend compatibility. |
| PPU1.5 / ACOMPUTE10500 / `ppu0015` | M890; tc02, a different AIU interface, FP8 and MXFP4 | The public ISA excludes original tc01/AIU forms. Do not carry 10000 coordinates or layouts over by name. |
| PPU1.7 / ACOMPUTE10700 | Hopper-style CuTe/CUTLASS TMA/WGMMA structure for FP16/BF16; PPU-specific extensions | Source compatibility does not establish native target support, feature parity or performance. |

Read the actual target manifest and compiler output. An old llama.cpp wrapper
needed `CMAKE_CUDA_ARCHITECTURES=OFF` to avoid an incorrect compatibility target;
the later Sage native build explicitly uses `hgcc -x hg -arch=ppu_10`.
These are different build contracts, not a universal requirement to remove
architecture flags. Inspect the emitted device body and backend resources.

SDK2.1.1 in the recorded 1.7 work exposed 1.0/1.5 targets. Accepting SM90 syntax
or `ACOMPUTE_VERSION=10700` did not make its output native 1.7. Do not fabricate
compiler architecture macros or use an empty guarded body as success.

## Match the memory and execution domains

The official HGGC guide places a complete CTA on one CU, with 32-thread warps.
L1 is per CU, L2 is shared within a CE, and LLC is shared across CEs. Asight
identifies KVD as vector data cache and KSD as scalar data cache. These facts
supersede the earlier diagram-only uncertainty; see [memory hierarchy](memory-hierarchy.md).

TSM is separate from global-cache traffic. The documented ordinary shared
access model has 32 banks of four bytes, plus a separate group-contention
dimension: ppu001 has two groups with 128-byte address spans and 128 B/cycle
per group; ppu0015 has four groups with 1024-byte spans. A 256-byte stride
can repeatedly select one ppu001 group even when bank-level reasoning looks
acceptable. Use the actual AIU/SWZL layout for matrix loads.

The supplied 512 KB L2 / 64 MB LLC / 288 GB diagram still has no confirmed SKU.
Its quantities do not follow from the public topology or establish ZW810 peaks.

## CUDA/PTX compatibility: preserve and check

Reuse the CUDA thread/block model, CuTe layout algebra, tiling, reductions and
pipeline reasoning where the selected backend implements them. Compatibility
does not make every MMA shape, register order or copy descriptor identical.

| Primitive in an NVIDIA port | Evidence from the PPU0010 work | Porting action |
|---|---|---|
| SM80 plain `cp.async` | Used unchanged in the Marlin path | Preserve the copy pipeline when its alignment, completion and lifetime contracts still hold. |
| FP16 `m16n8k16` MMA | PPU `m16n16k16` has four packed A registers, four B registers and eight FP32 accumulators | Recompute tiled-MMA ownership, reduction and epilogue for N=16; an opcode rename is insufficient. |
| INT8 `m16n8k32` MMA | PPU `m16n16k32.s32.s8.s8.s32` passed independent input/layout probes | Preserve INT8 arithmetic; rederive the n16 fragments instead of falling back to FP16 by assumption. |
| Plain `ldmatrix.x4` | The tested Marlin A address map needs output order `(v0,v2,v1,v3)` | Validate the address map and register order together. This permutation is not a rule for SWZL loads. |
| `ldmatrix.x2` | NVIDIA address formulas for the tested narrow tiles did not match PPU | Start from the backend traits or a verified element-wise copy, then probe the intended fast read. |
| `m8n16k16` | Historical ppu0015 assembler and compiler instruction selection disagreed | Check the full compilation path. Assembly-only acceptance cannot admit the kernel. |

The public [TIX guide](tix-porting.md) adds a documented alternative:
`tc01.ex.mma` supports additional n8 shapes through software conversion, with
ppu0015-style fragments. Compare its lowering with a rederived n16 implementation;
do not infer equal throughput from an accepted instruction name.

The recorded PPU0010 n16 accumulator map is
`row = lane/4 + 8*(r/4)`, `col = lane%4 + 4*(r%4)` for `r=0..7`.
It is a useful calibration case, not the A operand map or a PPU1.5/1.7 map.
Generate maps from the active traits before using hand-coded reductions.
See [CUTLASS/actlize](cutlass-porting.md) for source entry points.

## Operand delivery is a complete contract

For an AIU.swzl matrix input, track the global descriptor, physical shared
layout, cube/stage pitch, matching ld.swzl consumer and MMA lane/register
ownership together. Include element/byte units and transpose direction. The
matched FP16 pair does not need a software unswizzle between load and MMA.
Sub-byte converter output order is a separate source of offline permutation.

Plain `cp.async` is a distinct path. Thin GEMV tiles, register-produced
intermediates and alternative Marlin delivery can justify it. The historical
"AIU is only for FlashAttention" rule is superseded by measured GDN and
quantized GEMM/MoE paths. Changing only a load opcode does not change the
producer's layout or prove numerical equivalence.

For CuTe, enumerate the actual A/B/C traits and subview offsets. NVIDIA x2
ldmatrix formulas and A-fragment order have caused PPU failures. A simulator
model also previously disagreed with device int2 register pairing. Calibrate
the questioned seam against an independent logical map or device probe.

## PPU1.7 seams

Preserve the Hopper algorithm and collective while adapting build/dispatch,
descriptors, pipeline API, runtime and scheduler seams. A historical FA
integration used `USE_PPU` for legacy AIU and a separate `FLASHATTN_PPU17`
guard for the Hopper path. These are integration-specific names, not switches
provided by the official FlashAttention project. Keep equivalent target
separation explicit in the task's own port.
The 3.6 and 4.3 backends require different epilogue/pipeline APIs. Keep the
empty-barrier arrival count and release predicate matched.

PPU-specific differences include B128A32 (`Swizzle<2,5,2>`) and a third
descriptor layout bit; existing B128/B64/B32 high bits remain compatible.
TMA adds `.pos_swzl` and sub-byte coordinate conversion. Do not convert an
FP4 coordinate from elements to bytes twice; the tensor-map base still needs
its required alignment. TF32 atoms add MN-major/transpose modes absent from
the corresponding Hopper interface. Match atom, descriptor and producer.

Optional cluster-group synchronization has its own participants and K-step
lifetime. A warpgroup, a CUDA cluster and that private facility are different
concepts. Audit completion before reusing operand storage. AIU source support
also remains in this backend; it is not the default BF16/FP16 Hopper path.

FP8 wide-K and block scaling are separate features. At the inspected revision,
K48 SS and K32 RS do not offer interchangeable operand contracts. A 48/48/32
schedule has a conditional 4/3 issue-throughput ceiling, not a measured device
speedup. Low-bit scale encodings must match the actual atom; see
[SageAttention](sage-attention.md).

## Resources and evidence

The public manuals and historical PPU0010 reports provide different evidence:

| Resource | Recorded value / scope |
|---|---|
| Warp / launch limits | Official ppu001/ppu0015 tables: 32 threads/warp, 2048 threads/CU, 1024 threads/block |
| Shared memory | Official tables: 256 KB/CU and 32 banks; historical allocation unit 128 bytes |
| Registers | Unresolved: HGGC/TIX list 64K VREG/CU; the official 810E optimization guide lists 128K; history records 131072 32-bit registers/CU. The manuals label a 255 VREG/warp limit, while history used 256/thread billing. Resolve units and allocation rules rather than combine these numbers. |
| Register billing | A mixed-GEMM report with 186 registers/thread hit a limit consistent with 256 billed; a small fixed rounding model failed that case |
| Product examples | Official optimization guide: 810E, 64 CUs. M890 guide: OAM 39 CUs/10 CEs; M530 PCIe 30 CUs/8 CEs; four-CU CE organization. Query the task's product instead of using a nominal CE product as its available CU count. |

Use compiler resource output and the selected ACU occupancy limits rather than
extrapolate a universal allocation rule from one observation. Calculate both
resident CTAs and `CTAs * warps_per_CTA`, then compare with actual grid supply.
Reducing blocks/CU can still increase resident warps when the tile changes.

Other PPU0010 card values appear in [S01/S02](sources.md): the mixed-GEMM
history used 72 CUs; the INT8 note records a user-provided 1000 TOPS peak and
derives 500 TFLOP/s FP16, also used in historical GEMM normalization. The
derived FP16 figure is not an independent peak measurement. The legacy skill
cites approximately 2766 GB/s HBM but also discusses a 1792 GB/s part. Keep
each value attached to its original card/run until SKU and clocks are resolved.
A benchmark's 256 MB working-set sweep is not a measured cache capacity.

These are not PPU1.5/1.7 constants. CU count, cache capacity, memory bandwidth,
clocks and dtype-specific peaks must identify the SKU/model and operating
configuration. Historical bandwidth/peak numbers from different boxes are
not a single PPU spec. PPU1.0 still needs a complete card-specific resource
profile, resolved allocation rules and instruction timing. Scalar floating-point
rules are now documented in [numerics](numerics.md#preserve-the-documented-arithmetic);
MMA internal rounding and performance-model fidelity remain task-specific questions.
The [official document map](official-docs.md#remaining-questions-for-the-perf-model)
records the remaining questions; retain the target scope of each answer.

Normalize emitted instruction work per useful tile/output, and separate static
code size from dynamic execution counts. Compiler acceptance, efficient native
lowering, numerical correctness and performance are separate claims. Diagnose
an expansion before calling it emulation: layout/address arithmetic and scalar
publication can also create many instructions.
