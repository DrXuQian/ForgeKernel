# Harvest PPU mechanisms from this run

## Inputs

- KB root: {KB_DIR}; target generation: {KB_ARCH}
- Probe workspace: {WORKSPACE}; policy: {META_MILESTONE_PATH}
- The driver appends actual probe battles and accepted changes below.

Harvest only operator-agnostic hardware-interface lessons supported by this
run's native evidence. Follow TEMPLATE.md, keep optimized operator bodies and
provenance narratives outside the readable KB, and retain SDK/target and
correctness/performance scope. An existing verified recipe gets a focused
gotcha or condition update, rather than a duplicate.

A failed candidate, uncertain instruction mapping, unrun historical lesson
or merely successful build is not a verified hardware-performance recipe.
Store unresolved work in the run's evidence, not as a certified KB placeholder.
For a native-ISA change, cite the actual before/after footprints, correctness
result and matched time; label the structural conditions of the measured gain.

After writing the files and index rows, output one line per recipe:

    RECIPE_RECORDED: hw_kb/ppu/{KB_ARCH}/<interface>.md

If no generalizable certified mechanism was established:

    NO_RECIPE: <reason>
