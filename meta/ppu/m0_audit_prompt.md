# PPU M0 finish audit

## Inputs

- Milestone: {MILESTONE_PATH}; trajectory: {TRAJECTORY_PATH}
- Meta trajectory: {META_TRAJECTORY_PATH}
- Architecture reference: {ARCH_REF}; window: {WINDOW_CONTRACT}
- Policy: {META_MILESTONE_PATH}; template: {MILESTONES_TEMPLATE_PATH}

{VERDICT_PROBE_BRIEF_AUDIT}

Check whether the first correct implementation realizes M0's declared native
structure. Reconcile the actual bodies, dataflow, ownership, dtype/reduction,
copy and synchronization contracts, resources and complete timed window.
Use native evidence; unavailable NVIDIA dossier fields are not zero or a
failed PPU mechanism. A gap to the final performance target alone is not an
architecture defect. Do not repeat an already accepted audit for this segment.

Distinguish a contract deliberately scheduled for later tuning, a student
implementation defect, and a deficient milestone. Name the single most
foundational defect. R1 requires a measured price from a matched probe or
target-certified recipe. Revisit relevant PPU lessons where permitted.

## Output

    cause_class: OK | G1 | G2 | G3 | G4 | R1 | R2
    deficient_locus: <D id or KB interface; empty for OK>
    reopen_price: <required for R1, measured delta via probe or certified KB>
    phase_verdict: <when requested, close or continue:D id>
    locus_segment: <measured role.segment or none>
    patch_direction: <one change; for OK, state which structural checks reconciled>
