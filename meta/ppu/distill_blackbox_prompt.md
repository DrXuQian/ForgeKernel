# PPU blackbox milestone

## Inputs

- Withheld oracle identity: {ORACLE}
- Recon report: {RECON_REPORT}
- Candidate table: {CANDIDATES_PATH}; selected candidate: {CANDIDATE}
- Reference evidence: {ARCH_REF}; baseline: {REF_BASELINE}
- Window: {WINDOW_CONTRACT}; timing: {GATE_WINDOW}
- Target: {TARGET_MS}; ratio: {EQUIVALENCE_RATIO}
- Policy: {META_MILESTONE_PATH}; template: {MILESTONES_TEMPLATE_PATH}
- Output: {MILESTONE_PATH}; language: {LANGUAGE}
- Target generation: {KB_ARCH}; certified KB: {KB_READ_DIR}

Use only permitted blackbox observations and target-certified hardware
knowledge. Do not retrieve the reference source or imported operator-history
packs. Distill the selected candidate using the supplied recon evidence,
including explicit unresolved questions and falsifying experiments.

Preserve ForgeKernel's fixed milestone skeleton, decision five-tuples, DAG,
phase gates, Worked Example and [SYNC:]/[GATHER:]/[PHASE:] declarations. Native SYNC may be
native-pipeline or native-barrier; specify its actual primitive and completion
contract. A non-none SYNC/GATHER needs a sync: / gather: verification line
with native ACU/ISA evidence or a correctness probe.
M0 settles architecture and orchestration;
later phases tune inside it. Express native PPU interfaces, physical layouts,
resources, scheduling and completion contracts rather than substituting
NVIDIA assumptions. A counter-derived inference needs a measured premise.

Use [VERIFY: acu-direct], [VERIFY: acu-derived], [VERIFY: native-isa-derived]
and [VERIFY: correctness] for established channels. Unverified items are
[VERIFY: none] guidance outside gates. Price a native-ISA acceptance line
with a target-device experiment. Write the milestone file before reporting
completion, and keep optimized implementation bodies out of it.
