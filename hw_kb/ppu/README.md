# PPU hardware knowledge base

The native PPU mode reads one architecture tree: ppu10 or ppu15.
These trees start with no newly certified recipes. Their indexes select the
target and provide a place for actual run-backed certifications; an empty
index does not claim hardware support or measured performance.

Use TEMPLATE.md for operator-agnostic interface recipes. Keep minimal native
examples, public API symbols and actual certification scope here. Put source
identities and operator narratives in docs/kb-provenance/ppu/, for human review.
The source-mode teacher may consult the separate PPU history skills to choose
experiments. Historical operator experience does not enter this KB unchanged.

Only actual target-device evidence admits a verified recipe. Distinguish
layout, compile, launch, arithmetic and performance checks. Keep SDK/backend
and generation explicit, and retain failures or conditions that limit reuse.
NVIDIA recipes remain in their original trees.
