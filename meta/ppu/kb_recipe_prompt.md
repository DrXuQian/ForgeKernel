# Certify a PPU hardware recipe

## Inputs

- KB root: {KB_DIR}; target generation: {KB_ARCH}
- Permitted oracle: {ORACLE}; policy: {META_MILESTONE_PATH}
- Probe workspace: {WORKSPACE}; human provenance: {PROVENANCE_DIR}

Write an operator-agnostic hardware-interface recipe following the KB
TEMPLATE.md. It may contain a minimal native C++ example, actual SDK API
symbols and official documentation links. Keep the reference's optimized
body, internal symbols, operator structure and narrated history in the human
provenance archive, outside the student-readable recipe.

Certify the mechanism with a self-contained notes/<name>.py using the card's
PPU builder and target. Exercise known inputs and independently check the
contract. Print PROBE PASS max_diff=<finite norm> or PROBE FAIL max_diff=<norm>.
A compile/launch-only check uses max_diff=n/a and cannot certify arithmetic.
State SDK/backend, native target, actual device and evidence scope.

Write the recipe and probe, then submit:

    PROBE_REQUEST: notes/<name>.py

Fix failed probes from their actual logs. NO VERDICT establishes nothing.
After a valid target-device PASS, register the recipe and its limited
certification in the architecture index, then output:

    RECIPE_CERTIFIED: hw_kb/ppu/{KB_ARCH}/<interface>.md

Imported historical measurements or another generation's result cannot
certify this recipe. A mechanism's measured benefit remains conditional on
the tested workload structure and complete timing scope.
