# PPU teacher diagnosis

## Inputs

- Milestone: {MILESTONE_PATH}; trajectory: {TRAJECTORY_PATH}
- Meta trajectory: {META_TRAJECTORY_PATH}; candidates: {CANDIDATES_PATH}
- Permitted oracle: {ORACLE}
- Policy: {META_MILESTONE_PATH}; template: {MILESTONES_TEMPLATE_PATH}

{VERDICT_PROBE_BRIEF}

Read the objective trajectory and native profile evidence. Revisit relevant
PPU history in source mode when measurements contradict a candidate premise.
Use the actual metric definition, units, target and window; compare effective
work and latency along with utilization. Distinguish an implementation defect,
a missing hardware recipe, an unmeasured mechanism and a structural limit.
Name one most foundational deficient decision. Price structural reopens with
a controlled target-device experiment; an unsupported peak is not a floor.
The existing G1/G2/G3/G4/G5/R1/R2/INFEASIBLE taxonomy and patch rules apply.

## Output

    target: <metric and declared value>
    achieved: <best reading and iteration>
    gap_pct: <gap>
    reachability: <measured/estimated floor with premises, or unmeasured>
    curve_shape: <observed trajectory shape>
    cause_class: G1 | G2 | G3 | G4 | G5 | R1 | R2 | INFEASIBLE
    evidence: <iterations, native metric names/units, probes and counterexamples>
    deficient_locus: <D id or KB interface>
    locus_depth: foundation | upper | n/a
    patch_kind: additive | structural | split | kb-example | none(student-noise)
    reopen_price: <required for structural/R1, measured delta via probe or certified KB>
    phase_verdict: <when requested by the driver, close or continue:D id>
    locus_segment: <when measured, role.segment; otherwise none>
    patch_direction: <one concrete change>
    confidence: <level and reason>
