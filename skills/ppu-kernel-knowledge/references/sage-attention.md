# SageAttention

Sources: [S06, S07, S13](sources.md), with [S01/S02](sources.md) for the original
PPU bridge. Algorithm and target changes need separate evidence.

## PPU1.0 INT8-QK / FP16-PV contract

The reviewed PPU implementation uses INT8 QK, FP16 PV and FP32 accumulation.
BF16 input and output do not make PV a BF16 multiply. Q per-warp and K per-block quantization,
optional K smoothing, softmax scale and LSE correction are algorithm semantics.
An INT8-PV path is a different algorithm and needs separate accuracy evidence.

The recorded route quantized Q in 32-row warp groups inside a 128-row Q tile
and K in 64-row blocks. D128 used two validated 64-wide operand slices. Q/K
used non-transposed AIU/SWZL delivery; V used a non-transposed AIU write and
transposed shared read. Preserve those roles when rebuilding the route from
the official algorithm and PPU dependency.

Use two references for different questions: actual quantized operands/scales
for kernel correctness, and original full-precision attention for quantization
loss. A relaxed original-input comparison can hide a layout defect. Model
quality is another acceptance question, not established by either tiny fixture.

## PPU fragment bridge and compiler boundary

The accumulator C layout and the next FP16 MMA A layout differ. The proven
bridge takes score as A and fixed bridge weights as B. The reversed bridge and
row-major interpretation of a CuTe-linearized coordinate were each wrong in
240 of 256 values in the historical oracle. Preserve the full coordinate map
and test the historical wrong direction as a negative.

The first device admission found a separate codegen defect: an atom treated
four reference arguments as a contiguous array. Reusing one zero object left
only one of four accumulator registers initialized in native ISA. Bind each
reference independently and inspect the generated bridge sites. A host layout
proof cannot certify compiler operand binding.

This repaired bridge was a local extension. In the inspected official actlize
baseline, its FP16-output MMA atom is an unimplemented device body; see
[official dependency limits](cutlass-porting.md#official-actlize-baseline).
Implement and verify the required bridge in the task instead of assuming that
installing official actlize supplies the historical repair. Retain a coordinate
oracle (all 256 values, with the reversed direction as a negative) and inspect
the actual accumulator bindings in native code.

The retained K-block-major PV traversal reduced live probability operands
while preserving each output's accumulation order. Its spill reduction was
native compile evidence; latency still required a device measurement.

## Low-bit experimental targets

The official [TIX contract](tix-porting.md) now documents ppu0015 tc02 FP8
and MXFP4 (E2M1 with E8M0, K=32 scale groups). Use that public contract for
a new ppu0015 task; it does not establish UE4M3 NVFP4 or a PPU1.7 backend.

The reviewed experimental PPU1.5 INT8/FP8 and PPU1.7 FP4 work has separate
evidence from the PPU1.0 case. Native1.5 compilation and 1.7 source checks were
recorded; device numerics/performance were not established by that delivery.

In the inspected PPU CUTLASS4 archive, the 10700 FP4 interface uses E2M1 with
UE8M0 scales. A wrapper named `nv_float4_t` did not establish NVFP4 UE4M3.
The actual UE4M3 example targeted 20000/SM100a. This is an interface/source
finding, not proof that PPU1.7 hardware can never support NVFP4. Match the
requested generation, scale encoding/group size, descriptor and compiled atom.

The reviewed vendor archive was CUTLASS4.3 PPU, revision `0eb6a3b218977892e2b6cd30d59880c440e54fd6`.
Its 10700 FP4 header contained 16 opcode sites using UE8M0, with group16/32
variants. The builder selected from data types without a scale-type argument;
the UE4M3 example instead used an explicit `(E2M1, UE4M3, 16)` tuple and the
20000/SM100 path. This included audit is a source finding for that archive,
not an instruction to obtain a personal fork or claim official actlize supports
the same 10700 interfaces. Native1.7 and device numerical/performance checks
were not established by that review.

Carry the low-bit format ID through the prepared artifact, manifest and native
ABI. Byte buffers of equal size can contain incompatible scale encodings;
reject wrong formats before launch rather than reinterpret them.

## Measure the declared scope

Separate prequantized attention core from Q/K quantization, V cast, smoothing
and the full public call. Compare equal input/output dtype, layout, mask and
shape against FA. A BF16-equivalent MFU is a normalization, not mixed
INT8/FP16 hardware utilization. Confirm the selected native QK/PV route.
