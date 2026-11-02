# Sources and included evidence

The PPU knowledge needed by this skill is stored in this ForgeKernel checkout. The
links below lead to maintained local Markdown, not personal repositories,
private memory files or globally installed skills. Selected operator findings
are incorporated into the relevant reference instead of copying entire project
manuals and release procedures.

Reviewed on 2026-10-30. Historical device observations retain their original
target and scope. The included explanations are not raw report archives or a
new device validation. Build and validate the requested kernel on its target.

## Included reference map

| ID | Material in this checkout | Evidence scope |
|---|---|---|
| S01 | [Architecture](architecture.md), [CUTLASS/actlize](cutlass-porting.md), [numerics](numerics.md), [quantization](quantization.md), [GEMM/MoE](gemm-moe.md) | Selected operator-history findings and corrections: physical ownership, storage formats, scheduling and port comparisons. |
| S02 | [PPU0010 instructions](architecture.md#cudaptx-compatibility-preserve-and-check), [resources](architecture.md#resources-and-evidence), [FlashAttention](flash-attention.md) | PPU1.0 PTX/copy and occupancy observations. Historical card values and wrapper behavior are scoped in the text. |
| S03 | [PPU1.7 differences](architecture.md#ppu17-seams), [Hopper API seams](cutlass-porting.md#hopper-integration-has-api-seams-too) | Vendor-backend source comparisons and integration lessons; native PPU1.7 support is not inferred from them. |
| S04 | [GDN contract and operand delivery](linear-attention.md), [profiling diagnosis](../../ppu-profiling/references/analysis.md) | PPU1.0 residual/WY numerical schedules, global versus register-produced inputs, and split-prepare traffic interpretation. |
| S05 | [FlashAttention](flash-attention.md), [CUTLASS/actlize](cutlass-porting.md) | Legacy AIU and Hopper-style PPU paths, online-softmax semantics, pipeline interfaces and execution limits. |
| S06 | [SageAttention](sage-attention.md), [numerical debugging](numerics.md) | INT8-QK/FP16-PV contract, C-to-A bridge validation and historical compiler-binding failure. These are porting lessons, not a claim that an upstream PPU implementation is supplied. |
| S07 | [Low-bit format audit](sage-attention.md#low-bit-experimental-targets) | PPU1.5/1.7 source/native boundaries; E2M1 scale encodings and target mismatch in the reviewed vendor archive. |
| S08 | [CuTe debugging](numerics.md), [cold GEMV](quantization.md#cold-weight-experiments), [PPU profiling](../../ppu-profiling/SKILL.md) | Reusable debugging and measurement guidance, with project budgets and release policy removed. Adapted material retains its stated license. |
| S09 | [ForgeKernel integration](forge-integration.md), [attribution](notices.md) | The collection is adapted to ForgeKernel's teacher/milestone/student loop. Historical operator lessons remain outside the hardware-certified KB. |
| S10 | [ACU collection](../../ppu-profiling/references/collection.md), [metrics/rules](../../ppu-profiling/references/metrics.md), [Asys timeline](../../ppu-profiling/references/timeline.md) | SDK2.1.1 command and schema observations. ACU imports were exercised; Asys help/version was checked without a new device capture. |
| S11 | [Official actlize baseline and extension boundaries](cutlass-porting.md#official-actlize-baseline), [PPU traits](architecture.md) | Official source review at the revision below. Local extensions and historical fixes are distinguished from the official implementation. |
| S12 | [PPU memory hierarchy and Hopper comparison](memory-hierarchy.md), [ACU interpretation](../../ppu-profiling/references/metrics.md) | Adapted from the user-supplied `PPU架构与NVIDIA_SM对照.md`. Includes diagram-derived topology, interface annotations and unresolved units. The PPU model/generation is unspecified; this is not a ZW810 specification or a device measurement. NVIDIA comparisons use the official documentation linked in the local reference. |
| S13 | [Official manual map](official-docs.md#document-map), [architecture](architecture.md), [TIX](tix-porting.md), [numerics](numerics.md) | T-Head HGGC/TIX SDK2.1.1 and 2.2.0, optimization guide and M890 architecture guide. Target identities, cache/shared domains, instruction contracts and scalar numerical rules; explicit register/alignment discrepancies. A local SDK2.1.1 FP16-output MMA probe compiled to native PPU1.0 MMA; no device run. |
| S14 | [Official Asight documents](official-docs.md#document-map), [collection](../../ppu-profiling/references/collection.md), [metrics](../../ppu-profiling/references/metrics.md), [MCP access](../../ppu-profiling/references/tool-access.md#mcp-access) | Asight2.1.1/2.2.0 public documentation; KVD/KSD roles, cache-policy discrepancy, documented `acu_report` and official Asys MCP. Added LLC names were also present in the existing imported report and installed SDK sections. New Python/MCP interfaces were not exercised in the local SDK2.1.1 installation. |
| S15 | [Official implementation map](official-docs.md#official-implementation-starting-points), [FlashAttention](flash-attention.md#official-ppu-starting-point), [linear attention](linear-attention.md#official-ppu-starting-point) | Public T-Head ecosystem guides and official repository READMEs. PPU FlashAttention, PLA, Triton and CMake starting points; source/documentation support is separate from a new task's native validation. |

## Official upstreams

Use official public projects as dependency and algorithm starting points.
Record the selected revision in the task workspace. Do not substitute a
personal fork to obtain an undocumented feature; implement any needed change
in the task's own code or a reviewable patch against the official baseline.

| Project | Official source | Role |
|---|---|---|
| actlize | [t-head/actlize at cace89d](https://github.com/t-head/actlize/tree/cace89de8cb1cfc9345535bdbc1fb5f403bfb01f) | PPU0010/0015 C++/CuTe dependency. This is the inspected `v1.0.0` branch revision, not a claim that every historical extension is included. |
| PPU FlashAttention | [t-head/flash-attention-for-sail v2.8.2](https://github.com/t-head/flash-attention-for-sail/tree/v2.8.2) | Official FA2/FA3 PPU implementation; inspect architecture-specific features and build selection. |
| PPU Linear Attention | [t-head/pla v1.0.0 source](https://github.com/t-head/pla/tree/700ae21741aa13cc7af2edf503262867d418bfab) | GDN/Kimi Delta Attention decode and prefill for ppu001/ppu0015. |
| PPU Triton | [t-head/triton-for-sail at e04ef69](https://github.com/t-head/triton-for-sail/tree/e04ef69c7e803a773ca9b14fd11d328686893044) | Public PPU compiler/backend; this is the reviewed main revision, not a prescribed release for every SDK. |
| HGGC CMake support | [t-head/cmake-hgcc v1.0.0](https://github.com/t-head/cmake-hgcc/tree/v1.0.0) | Optional native HG language/toolkit/RDC support for task builds and CUDA migration. |
| CUTLASS | [NVIDIA/cutlass](https://github.com/NVIDIA/cutlass) | NVIDIA algorithms, CuTe interfaces and original kernel implementations. |
| FlashAttention | [Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention) | Exact-attention algorithm and NVIDIA implementation reference. |
| SageAttention | [thu-ml/SageAttention](https://github.com/thu-ml/SageAttention) | Quantized-attention algorithm and NVIDIA implementation reference. |
| Flash Linear Attention | [fla-org/flash-linear-attention](https://github.com/fla-org/flash-linear-attention) | Linear-attention algorithms and reference implementations. |

The NVIDIA/community attention upstreams remain algorithm references; the
T-Head projects provide official PPU starting points. Validate the selected
revision on the requested device. PPU migration knowledge is included locally.
The SDK/runtime and target kernel source remain task dependencies; ForgeKernel does
not bundle vendor binaries, private backend archives or original profiler
reports. See [target and workflow selection](forge-integration.md) for the execution contract.
