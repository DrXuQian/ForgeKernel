# TIX contracts for NVIDIA-to-PPU migration

Source: [S13](sources.md), the official [TIX guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=39&chapterId=612).
This is selected porting guidance; use the linked instruction sections for the
exact form. TIX is a virtual ISA embedded in HGGC C++, then lowered to native
PPU code. Preserve the original algorithm and inspect both the chosen virtual
instruction and its native implementation.

## Select the generation and instruction family

`ppu001` includes 810/610 and their E variants. It uses `tc01` and the original
AIU contract. M890 is `ppu0015`, uses `tc02` and a different AIU contract; the
guide explicitly excludes the original tc01/AIU forms on ppu0015. These are
`hgcc -arch=ppu_10` and `ppu_15`, respectively, not a PPU1.7 target.

| Porting decision | Documented form / action |
|---|---|
| PPU001 FP16/BF16 MMA | `tc01.mma` supports N=16 with M=8/16 and K=8/16. Select the required accumulator/output dtype and actual fragment traits. |
| Try an n8 port | `tc01.ex.mma` offers additional N=8 shapes through **software conversion**, using ppu0015-style fragment layouts. It is an alternative worth comparing, not proof of a native n8 instruction or equal throughput. |
| PPU001 TF32/F32 or INT8 | The native-shape families use K=4/8 for TF32/F32 and K=16/32 for INT8. Integer saturation is a separate `.satfinite` contract. |
| PPU0015 low precision | tc02 adds E4M3/E5M2 and MXFP4: E2M1 operands, E8M0 scales, K=32 scale groups. This does not establish NVIDIA UE4M3 NVFP4 compatibility. |

For tc01 m16n16k16 FP16, each lane holds four packed A and four packed B
32-bit registers. C/D use eight registers for FP32 or four packed registers
for FP16. Full-warp `.sync.aligned` participation is required. The guide's
§9.3/§9.5 fragment diagrams describe different families; a shared shape name
does not make their lane ownership equal.

The official guide specifies
`ppu.tc01.mma.sync.aligned.m16n16k16.row.col.f16.f16.f16.f16`.
A local SDK2.1.1 compile on 2026-10-30, with `-x hg -arch=ppu_10
-DSWITCH_TO_HGGCRT -std=c++17 -c`, emitted
`v.mma.f16.f16.m16n16k16` in a PPU1.0 device body. Four independent read/write
accumulator bindings and four A/four B input bindings were used. This closes
the compile/lowering question, not device numerical validation. The inspected
[actlize wrapper](cutlass-porting.md#official-actlize-baseline) still needs its
task-owned implementation.

## Cache modifiers describe PPU levels

| Operation | Selected documented behavior |
|---|---|
| Global `ld.ca` | Eligible for all cache levels |
| Global `ld.cr` | Excludes L1; caches in L2/LLC |
| Global `ld.cg` | Excludes L1/L2; caches in LLC |
| Global `.ba` | Bypasses all cache levels |
| Plain `cp.async.ca.shared.global` | Caches in L2/LLC, without L1 allocation because the destination is shared |

These are instruction-specific policies, not a textual substitution for NVIDIA
PTX cache modifiers. Hints do not establish memory ordering. LLC prefetch-size
hints require ppu0015. Compare actual traffic at each boundary when changing
a cache policy; see [memory hierarchy](memory-hierarchy.md).

## AIU producer and matching consumer

For ppu001 AIU `.swzl`, the shared destination needs 128-byte alignment.
Reserve rows for `cube_n * cube_h * cube_w` rounded up to eight: reserved extra
rows are not necessarily written. Channel storage rounds to 32-byte slices;
the documented channel padding is zero-filled. Preserve dimensions, transpose
and physical stage pitch with the matching `tc01.ldmatrix.swzl` consumer.
Its H/W coordinates count elements, while `channel_offset` counts **bytes**.
The consumer reverses the producer's swizzle; a second software unswizzle is
not required. B8 AIU transpose is not supported by the ppu001 form.

PPU0015 AIU uses another descriptor/stride contract. Its swizzle-mode channel
rounding reserves storage without automatically writing the aligned excess.
For zero-filled MMA tails, request the full swizzle-width channel extent so
out-of-bounds tensor elements are actually padded. Do not reuse ppu001's
padding assumptions. The corrected SDK2.2.0 examples express strides in bytes;
see [the version comparison](official-docs.md).

## Completion and assembly bindings

`commit_group` groups prior copies by issuing thread. `wait_group N` waits
until at most N groups remain outstanding; `wait_all` also commits pending
copies. Same-group writes to the same destination are undefined. Copy waits
do not order unrelated memory operations or by themselves publish the result
to every other warp. Keep the cross-thread publication and stage-reuse edges.

For awbar tracking, ordinary `cp.async.awbar.arrive` increments the pending
count before its later completion arrival; `.noinc` requires that arrival in
the initial expected count. Preserve phase tokens, participant counts and
invalidation before repurposing the object's storage. The guide contains an
[alignment discrepancy](official-docs.md#remaining-questions-for-the-perf-model);
keep the selected backend's validated allocation until it is resolved.

Bind packed bit containers with integer constraints and FP32 values with the
matching floating constraint. Use read/write (`+`) constraints for accumulators;
output-only (`=`) is not a declaration that an old value is consumed. Check
generated operands as well as source arrays. See [numerics](numerics.md) for
ownership, scalar rounding and failure isolation.
