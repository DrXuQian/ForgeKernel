# PPU architecture-first milestone

## Inputs

- Oracle permitted by this source-mode run: {ORACLE}
- Reference signature: {ARCH_REF}
- Performance baseline: {REF_BASELINE}
- Acceptance target: {TARGET_MS}; required reference speed ratio: {EQUIVALENCE_RATIO}
- Window: {WINDOW_CONTRACT}; acceptance timing: {GATE_WINDOW}
- Policy: {META_MILESTONE_PATH}; template: {MILESTONES_TEMPLATE_PATH}
- Milestone output: {MILESTONE_PATH}
- Language: {LANGUAGE}; target: {KB_ARCH}; certified recipes: {KB_READ_DIR}

## Write M0 and the curriculum

Follow the shared milestone skeleton and driver protocol. Use native PPU
contracts from the actual SDK and measured reference; the shared policy's
NVIDIA-specific examples are examples, not native target specifications.
First read relevant PPU historical lessons available to this source-mode
teacher and record their applicability in recon/candidates.

Settle architecture and orchestration in M0: public semantics, kernel split,
dataflow, physical ownership, accumulation precision, tile/warp roles, live
resources, movement, publication and completion. Separate structural decisions
from later tunable levers. Give parameters and contracts, not the reference
implementation body. Price candidates with matched native evidence.

Write the existing sections ## 0. through ## 6. and ## Worked Example.
Every D<x>.<y> has Action / Purpose / Trigger condition / Cost / Depends on.
Keep the shared [SYNC:]/[GATHER:]/[PHASE:] declarations. PPU SYNC also
accepts native-pipeline and native-barrier; name the actual primitive and its
ownership/completion contract. Non-none SYNC/GATHER require a native
verification line named sync: / gather: with a native channel or a
correctness probe. Do not invent NVIDIA stall_barrier/stall_long_sb readings.
Keep the DAG phase order, coupled groups, dead ends, mechanism checks and
per-phase gates. Mark values [MEASURED] or [ESTIMATE]. Use actual ACU names,
units and scope; valid classes are acu-direct, acu-derived,
native-isa-derived and correctness. A priced native-ISA gate includes
[PRICED: <delta>, <job N or certified KB entry>]. Unverified structure remains
decision guidance with [VERIFY: none], not a fabricated acceptance threshold.

After M0 is accepted, later milestones tune inside it. Reopening a structure
requires a measured price and the normal teacher revision, dependency and
gate-payoff rules. Correctness and the selected clean timing window remain
the promotion basis. Counter utilization has meaning only with its work and
denominator stated.

Edit the milestone file before reporting completion. Validate its structure
with the same ForgeKernel rules; imported history is not a new KB certification.
