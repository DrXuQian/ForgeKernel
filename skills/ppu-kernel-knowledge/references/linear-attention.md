# Linear attention and Gated DeltaNet

Sources: [S01, S04, S08, S15](sources.md). The PPU1.0 residual implementation below
is a historical case study. Use the official algorithm reference and the
task's own PPU code; no external operator fork is required to read this guide.

## Official PPU starting point

[T-Head PLA v1.0.0](https://github.com/t-head/pla/tree/700ae21741aa13cc7af2edf503262867d418bfab)
provides ppu001/ppu0015 GDN and Kimi Delta Attention decode, MTP and prefill.
Its prefill depends on official actlize v1.0.0. Inspect the selected namespace,
k-last/v-last state layout, packed inputs and target tuning before adapting
it; the historical C64 case below does not define every PLA API.
`PPU_SDK_DIR` and `PPU_ACTLIZE_DIR` select its SDK/dependency locations.
Use its validation entry plus an independent recurrence check. The algorithm
abbreviation KDA in PLA means Kimi Delta Attention, an operator rather than
an agent framework.

## Freeze the recurrence and state contract

For the scalar-gated DeltaNet studied here, with state H indexed [key,value]:

```text
H_t = g_t (I - beta_t k_t k_t^T) H_(t-1) + beta_t k_t v_t^T
o_t = scale * q_t^T H_t
g_t = exp(graw_t)
```

The contract includes gate units, beta/QK normalization, grouped-value head
mapping, initial state, final state, tails and state precision. Validate both
output and final state against a recurrent oracle. Distinct heads and nonzero
carried state expose bugs that a zero-state single-head fixture hides.

The early chunk derivation transforms the state with the inclusive gate
cumsum; the chunk output uses the chunk-start state and the state update comes
afterwards. This is an algebraic reference, not permission to replace the
retained kernel's rounding or stable gate handling. One-token and multi-chunk
cases distinguish update order and missing gate factors.

## Compare complete numerical schedules

Keep original, materialized-WY and residual schedules distinct.
The retained residual path has BF16 operands/output and FP32 carried state;
its C64 full-chunk specialization and guarded tail preserve the admitted
arithmetic. An original reset approximation or a different state dtype cannot
silently become the oracle for that path.

Delivery-only changes use equality to the admitted schedule plus an independent
numerical check. Approximate recurrence changes need their own accuracy
contract and representative activations.

The historical retained case used Q/K `[B,T,Hk,128]`, V/output
`[B,T,Hv,128]`, and FP32 state `[B,Hv,128,128]`, with `Hv` a multiple of `Hk`.
Gate/beta were `[B,T,Hv]`, with gates in natural-log units. Q/K/V/output and
beta were BF16; gates were BF16 or FP32. C64 was an internal chunk size, and incomplete chunks used a guarded
tail. Validation covered output and final state, nonzero initial state,
grouped-value heads, tails and input immutability. This defines the evidence
scope of that example, not a fixed shape or tolerance for every GDN task.

## Preserve the execution graph before tuning

Inspect prefix, KKT/solve, W/U preparation when present, state recurrence and
output as separate mathematical phases. Include fills and auxiliary kernels
in the declared comparison. FLA's selected generated kernel, not merely
`tl.dot`, is the structural reference for layouts, reuse and synchronization.

An early scalar chunk kernel had too few CTAs, serial chunks and no tensor
cores. That result does not reject chunking. Later native AIU/SWZL delivery
and split preparation established different implementations. The early
"in-kernel intermediates make tensor-core GDN impossible" conclusion is obsolete.
Global operands can use AIU; register-produced state/residual operands need
their own shared/fragment producer contract.

| Operand or phase | Producer and consumer to preserve |
|---|---|
| Gate prefix | Scalar reads and scan/carry; it is not a matrix load. |
| KKT and global chunk operands | Matched AIU.swzl producer, ld.swzl consumer and BF16 MMA, including tail padding. |
| Inverse solve | CTA-produced FP32 data with the selected TF32 high/residual arithmetic and diagonal dependencies; changing delivery must retain that precision schedule. |
| FP32 state snapshot | Register-to-BF16 shared stores followed by the declared transposed read; the layout may also serve global state publication. |
| Residual / scaled V / probability intermediates | Register-produced shared data; a global AIU instruction cannot replace those stores without a new producer path. |

The split-prepare experiment is a useful controlled counterexample to
"fewer launches or bytes must win": it reduced W/U publication amplification
at the KVD interface, while adding intermediate traffic at L2/DRAM. Independent
phase resource budgets improved the complete profiled sum. Do not relabel
KVD savings as equal HBM savings or attribute the whole gain to one changed seam.

## Choose the next candidate

Use matched phase totals to rank remaining latency. When state and reference
have similar grid, active warps and MMA counts, inspect delivery, address
instructions, reuse and waits before changing the grid. When a publication
uses scalar stores, check transaction amplification and vector ownership.
Recheck the remaining bottleneck after each change.

Compare native GVA or clearly declared pre-expansion on equal logical inputs.
Keep all-kernel ACU sums, event/API spans and Asys timeline measurements
separate. Source/host validation, prior device receipts and a new branch merge
do not constitute a fresh speed measurement.
