## Native PPU audit experiments

Use up to {MAX_VERDICT_PROBE_ROUNDS} driver-submitted experiments when the
structural verdict cannot be resolved from the existing evidence.
Write notes/<name>.py and end the turn with:

    PROBE_REQUEST: notes/<name>.py

Use the card's native PPU build and compare one controlled difference within
the same job. Print a truthful PROBE PASS/FAIL max_diff=<error norm>, or
max_diff=n/a for a non-numerical contract, with latency and ACU/ISA evidence
reported separately. Keep accuracy, lowering and timing claims distinct.
The NVIDIA JSON/SASS pricing recipe is inapplicable; do not infer a reopen
price from static instruction position or another device's peak.
