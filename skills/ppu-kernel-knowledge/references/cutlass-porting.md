# CUTLASS, actlize and PPU backend differences

Sources: [S01, S03, S05, S08, S11, S13, S15](sources.md). actlize retains CUTLASS/CuTe's
layered design but changes architecture atoms, builders and operand delivery.
Keep the reusable structure and inspect the actual instantiated backend.

## Official actlize baseline

Use the official T-Head actlize source listed in [S11](sources.md). The inspected
`v1.0.0` branch revision is `cace89de8cb1cfc9345535bdbc1fb5f403bfb01f`.
Its PPU0010 CMake selector is `CUTLASS_PPU_ARCHS=ppu0010`; the native toolchain
uses `hgcc -x hg -arch=ppu_10 -DSWITCH_TO_HGGCRT`. The kernel examples, builder
and atom traits are the starting point for a new ZW810 task.

The following limits were checked in that official source. They explain which
historical fixes require task-owned implementation rather than a fork dependency:

| Seam | Official source at this revision | Required action when the task uses it |
|---|---|---|
| FP16-output MMA | `PPU0010_16x16x16_F16F16F16F16_TN::fma` in `cute/arch/mma_ppu0010.hpp` has an `assert(0)` device body | The historical one-MMA C-to-A bridge needs an implemented atom. Add and validate it locally, or use a verified layout-conversion path that preserves rounding. A declared type is not an implemented instruction. |
| Mixed-input group scales | The builder lists PerCol, Gs64 and Gs128 AIU policies. The collective computes `GroupK = copy_steps / Scale_TileK` before a modulo | A gs=32 extension must resolve each scale group and exclude zero `GroupK`; historical per-MMA-atom scale reload is not supplied by that code. |
| Interleaved expert planes | The `kContinous != 1` branch of `load_init_B` uses a zero L stride | Do not infer multi-expert interleaved support from a single-GEMM example. Implement the proper byte pitch and test distinct experts. |

These are scoped source observations, not new device measurements or hardware
limitations. Preserve the official dependency and keep necessary extension
patches with the task. Do not select a personal fork as an implicit repair.

The public TIX guide specifies the missing FP16-output instruction, and a
local SDK2.1.1 probe emitted native `v.mma.f16.f16.m16n16k16` for PPU1.0.
See [TIX evidence](tix-porting.md). Implementing the wrapper still requires
correct independent accumulator bindings, fragment validation and device tests.

## Choose the tree before choosing an atom

| Source family | Relevant entry points | What transfers |
|---|---|---|
| NVIDIA CUTLASS | CuTe atoms/layouts, collective builder, `GemmUniversal`, epilogue and scheduler | Layout algebra, composition and algorithm structure; architecture-specific traits need comparison. |
| Official actlize, PPU0010/0015 | `include/ppu_include.hpp`, `cute/{arch,atom}/*ppu0010*`, `cutlass/gemm/collective/builders/ppu_mma_builder.inl` | Similar APIs select PPU register MMA and AIU collectives. Start from the matching example and follow its concrete types. |
| PPU CUTLASS 3.6/4.x with 10700 support | `include/ppu/ppu_include_10700.hpp`, `ppu/cute/{arch,atom}`, SM90 builders/pipelines | BF16/FP16 retain Hopper TMA/WGMMA structure; private low-bit atoms and descriptor/runtime seams need separate checks. |

These trees are not interchangeable because their directory or version labels
look similar. Earlier PPU backend trees use `Acompute10000_*`; public actlize uses
`PPU0010_*` names. Resolve types in the selected checkout instead of installing
another tree to satisfy a guessed spelling. Record the include path, dependency
revision, real compiler target and generated specialization.

## Same schedule name can select different hardware

In official actlize S11, `KernelTmaWarpSpecialized*MixedInput` and selected
`KernelAiuMultistageMixedInput*` tags enter the same PPU builder and
`ppu_mma_aiu_multistage_mixed_input.hpp` collective. A `Tma` tag does not prove
Hopper TMA execution. `examples/16_ppu_mixed_dtype_gemm` exercises this route.

Follow the chain from builder to dispatch policy, collective, tiled MMA,
copy atoms and kernel wrapper. For the reviewed mixed-input route:

- The transformed tuple chooses `SwapAB`. Putting quantized weights in B does
  not request an M/N swap. Inspect the arguments actually passed, not unused
  reversed C/D strides inherited from a copied example.
- Runtime B stride remains ordinary packed `(N,K,L)` column-major. The
  interleave contract is carried by the builder's `kContinous` and preprocessing;
  `RowsPerTile=256` must match the interleaved-256 reader.
- Scale layout is MN-major with `Stride<1,int64_t,int64_t>`. Scale application
  cadence must resolve every group touched by a copy step. A historical
  64-K copy step skipped gs=32 scaling; per-MMA-atom reload fixed that route.
- Grouped reuse must implement expert byte pitches and ragged A row offsets.
  Single-GEMM success does not validate the L dimension or a different grouped
  wrapper. Use distinct expert data and an independent dequantized reference.

These are source contracts, not a rule that every format needs that reorder
or every backend supports gs=32. Verify the selected converter and collective.

## CuTe cannot check a layout hidden by the atom

The legacy AIU `.swzl` write and matched `ld.swzl` read cancel at byte level;
the FP16 path needs no offline compensation for that pair. Sub-byte offline
reordering instead matches converter emission order to MMA fragment slots.

Some legacy `Copy_Traits` flatten that contract. They do not express each
endpoint's physical map, so a mismatched producer/read pair can still compile.
Model both endpoints when changing the pair, and model the converter separately.
Use the known FP16 identity composition as a control. Do not add a second
software unswizzle to a working matched path.

The reviewed host SWZL model was XOR-linear within a slice but needed a rotate
across slices. In the recorded PPU0010 int2 case, hardware grouped registers
0/1 in the low N half and 2/3 in the high half; the fallback's register-parity
pairing was wrong. Calibrate the actual lane/register map before composing it
with a converter. See [numerical debugging](numerics.md).

## Extend a collective without changing unrelated dispatch

An additive mixed-input extension exposed a reusable template hazard: overlapping
`CollectiveBuilder` predicates can be ambiguous, while a wrapper tag that
collapses to a vendor tag can silently select the vendor collective. Give a
new dispatch policy its own identity and make specialization predicates
disjoint. Check the selected type for both the new and existing routes.

Use the preprocessor include graph to diagnose umbrella-header cycles; copying
an umbrella does not reproduce its partial-construction state. Keep architecture
guards on shared converter primitives when moving implementations. Those guards
are portability fixes even when the converter also supports a custom format.
The original project's naming rules, CI inventory and packaging policy are not
requirements for another kernel task.

## Hopper integration has API seams too

The reviewed PPU CUTLASS3.6 integration uses `KernelHardwareInfo::sm_count`, a
two-argument accumulator store selector and a three-argument
`PipelineTmaAsync` constructor. Other PPU forks use different APIs. Preserve
the matched empty-barrier arrival count and release predicate when adapting
constructors; copying only one side can deadlock a correct algorithm.

For each changed interface, check a representative generated body and its
caller, then output ownership and numerical behavior. An nvcc template check,
PPU native compile and PPU execution answer different questions.
