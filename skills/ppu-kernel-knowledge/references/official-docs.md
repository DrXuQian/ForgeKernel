# Official PPU documentation and remaining questions

Sources: [S13, S14, S15](sources.md). Reviewed on 2026-10-30. The table points
to official documents; the linked local references contain the selected guidance
needed for PPU work. Raw manuals are not bundled. Read the section relevant to the
task, retaining its SDK version, architecture and evidence scope.

## Document map

| Official document | Version / sections reviewed | Local application |
|---|---|---|
| [HGGC programming guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=39&chapterId=644&versionId=44) | SDK2.1.1; hardware model, shared groups, caches, async pipelines, numerics and compute-capability tables; compared with SDK2.2.0 chapter 611 | [Architecture](architecture.md), [memory hierarchy](memory-hierarchy.md), [numerics](numerics.md) |
| [TIX programming guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=39&chapterId=612) | SDK2.2.0; architecture/inline assembly, scalar arithmetic, cache operators, async copies, awbar and Tensor Cell; compared with [SDK2.1.1](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=39&chapterId=645&versionId=44) | [TIX porting](tix-porting.md) |
| [Kernel optimization guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=39&chapterId=832) | SDK2.2.0; representative **810E**, occupancy, shared banks/groups, compiler options | Resource and bank guidance; distinguish the representative SKU from ZW810 and historical cards |
| [M890 architecture guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=48&chapterId=768) | Document 1.0, 2026-09-16; sections 2–5, M890 OAM / M530 PCIe | M890 is `ppu0015`; use its product counts only for that product |
| [HGCC compiler guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=39&chapterId=658&versionId=44) | SDK2.1.1; native build/target, compilation phases and diagnostic options | [PPU build and target selection](forge-integration.md#target-and-build-selection); `ppu_10` / `ppu_15` select distinct native targets; virtual TIX is not the final machine ISA |
| [Runtime device properties](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=39&documentId=1645&versionId=44) | SDK2.1.1; resource fields, `l2CacheSize` | Preserve returned values and units; the API description does not specify cache aggregation scope |
| [ACU user guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=1&chapterId=734&versionId=50) | Asight2.1.1; replay, cache control, memory chart, occupancy and metric details; cache policy also checked in [2.2.0](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=1&chapterId=718) | [Collection](../../ppu-profiling/references/collection.md), [metrics](../../ppu-profiling/references/metrics.md) |
| [ACU Python report interface](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=1&chapterId=721) | Asight2.2.0; `acu_report` loading, actions and typed metrics | Optional structured report access; absent from the local SDK2.1.1 installation used for this review |
| [Asys AI analysis](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=1&chapterId=709) | Asight2.2.0; official GUI and CLI MCP, stdio/HTTP | [Tool access](../../ppu-profiling/references/tool-access.md#mcp-access); CLI remains sufficient for PPU work |

The TIX comparison found substantive corrections to the ppu0015 AIU examples:
SDK2.2.0 uses byte strides such as `{256, 16384}` where the archived example
used `{64, 128}`. Follow the operand's declared units and the corrected example;
copying an older example is not a layout proof.

## Official implementation starting points

The [source index](sources.md#official-upstreams) lists public T-Head projects.
Choose the implementation matching the task before writing a replacement:

| Task | Reviewed official starting point | Boundary |
|---|---|---|
| CuTe/CUTLASS GEMM | [actlize guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=46&documentId=1758): `v1.0.0`, CUTLASS3.6 | Keep the [inspected implementation limits](cutlass-porting.md#official-actlize-baseline); an ISA feature need not have an implemented wrapper |
| Exact attention | [flash-attention-for-sail guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=46&documentId=1764): `v2.8.2`, FA2/FA3 | Documented FP16/BF16 forward/backward, FA3 FP8 forward and head dimensions up to 256; check target-specific dispatch, especially FP8 |
| Linear attention | [PLA guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=46&documentId=2092): `v1.0.0`, commit `700ae21741aa13cc7af2edf503262867d418bfab` | `ppu001`/`ppu0015` GDN and Kimi Delta Attention decode/prefill; check state layout, API and device-specific tuning |
| Triton kernel | [triton-for-sail guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=46&documentId=2108); README reviewed at `e04ef69c7e803a773ca9b14fd11d328686893044` | PPU backend exists for both generations; select a compatible release and validate native execution. Import success alone is insufficient |
| CUDA CMake migration | [cmake-hgcc guide](https://developer.t-head.cn/docs_center/doc_detail/index.html?projectId=46&documentId=2099): `v1.0.0` | Native `HG` language, `CMAKE_HG_ARCHITECTURES`, toolkit targets and RDC; preserve an already working task build |

These are public implementation/documentation findings, not new device results.
PLA's algorithm named KDA means Kimi Delta Attention, distinct from the agent
workflow used to optimize it. NVIDIA upstreams remain useful algorithm
and correctness references.

## Remaining questions for the perf model

The basic architecture, scalar numerical rules, copy protocol and public backend
availability are documented. Request model evidence for these narrower items:

| Unresolved item | Concrete question / current handling |
|---|---|
| Register capacity and allocation | HGGC §5.5 and TIX §1.2 list **64K VREG/CU**; the 810E optimization guide lists **128K**, matching the older 131072-register record. Resolve units, physical partitioning, SKU and allocation granularity, including the observed 186-to-256 residency effect. Do not silently choose one table. |
| Barrier alignment | TIX §8.5.1 says an 8-byte-aligned `.b64` awbar; several operation sections say 64-byte alignment. Confirm the selected target's rule. Preserve the backend's validated barrier storage rather than changing it from these conflicting descriptions. |
| Cache-control behavior | ACU2.1.1/2.2.0 §2.2.9 tables say `none` still flushes L1/L2; their prose says it disables all flushing. Confirm the exact tool/runtime behavior. `all` explicitly includes LLC. |
| SKU and cache/performance quantities | Identify the supplied 288 GB / 64 MB diagram, ZW810 cache capacities and `l2CacheSize` aggregation; obtain clocks, per-direction bandwidth, queue/port limits, instruction issue/latency and model calibration. Public topology does not supply every quantity. |
| Tensor numerical details and model fidelity | Establish MMA internal reduction/rounding and model approximations where they affect the task. Scalar FMA/FTZ and approximate reciprocal/exponential rules are already documented; the FP16-output MMA also passed a native compile check. |

For each answer, include the model/config revision, parameter or handler,
units and sharing domain, and whether it is a hardware specification, model
assumption or device measurement. Include the necessary explanation in the
reply so the resulting reference does not depend on an internal link.
