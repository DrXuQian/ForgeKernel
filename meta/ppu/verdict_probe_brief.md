## Native PPU verdict experiments

Up to {MAX_VERDICT_PROBE_ROUNDS} driver-submitted rounds may resolve competing
mechanisms before diagnosis. Write a self-contained notes/<name>.py, using the
card's PPU builder, SDK/runtime and approved source access. Change one causal
factor, compare matched conditions in the same job, and preserve native
report identities and clean timing. State compile/layout checks separately
from numerical and performance evidence.

Submit:

    PROBE_REQUEST: notes/<name>.py

Print PROBE PASS max_diff=<finite error norm> or PROBE FAIL max_diff=<error>;
for a non-numerical contract use max_diff=n/a and separately print measured
latencies/counters. Do not put a timing ratio into an error-norm field.
The NVIDIA frozen JSON/SASS pricing recipe is not a PPU probe. These probes
measure a hypothesis, not deliver a replacement operator or disclose a
withheld implementation. The driver restores the workspace after diagnosis.
