# Use PPU experience in ForgeKernel

This collection supplies scoped prior knowledge to a source-mode teacher.
It follows ForgeKernel's reconnaissance, candidates, milestone, student,
correctness/performance gate and teacher-revision loop. Imported operator
history is kept outside hw_kb: that library admits operator-agnostic mechanisms
certified by a probe on the stated target.

## When to read the history

After identifying the task's actual PPU generation and implementation, read
the architecture and relevant operator references before proposing M0. Choose
additional pages by the observed issue: operand delivery, memory traffic,
numerical mismatch, synchronization, resource pressure or measurement scope.
Use the topic router in SKILL.md; do not preload the entire collection.

In the recon report and candidates table, connect each useful lesson to:

- Its local reference path/section and original hardware/backend.
- Its evidence level: source, layout, native compile, simulator, correctness
  or measured device performance.
- What transfers to the current task and what must be rederived.
- A candidate decision and the experiment that can confirm or reject it.

Revisit the relevant pages after new profiles, a failed numerical check or an
unexpected performance result. The history helps choose experiments; current
device evidence decides which decisions survive. A lack of a matching lesson
does not prevent working from the current source and measurements.

## Milestones and knowledge certification

The teacher settles the architecture and orchestration in M0: public semantics,
dataflow, layouts, resource allocation, synchronization and measurement scope.
After its gate passes, later milestones tune within that structure. A profile
showing a structural limit calls for an M0 revision, not an unrecorded change
to the student's contract.

Keep source identities, measurements and experiment narratives in the run's
recon/candidate records. Give the student decisions, parameters and contracts,
not historical implementation bodies. New hw_kb recipes need an
operator-agnostic example and a probe on the actual target; retain the SDK,
generation, device and correctness/performance scope. A PPU1.0 result cannot
certify a PPU1.5 or PPU1.7 recipe, and compiler acceptance is not device timing.

ForgeKernel mirrors these two PPU history packs for source-mode teachers
and for native PPU reference generation before an oracle has been accepted.
The generator retains its restrictions on reference sources and sealed keys.
It removes them before a student or restricted/blackbox teacher turn and
denies those roles access to the repository copies. In that mode, hardware
knowledge continues to come through the normal certified-KB channel. This
preserves the reference-source boundary while permitting explicit use of
prior operator experience in source-mode work.

## Target and build selection

Record the runtime-reported model, SDK/runtime, dependency revision and the
native target. Public PPU1.0 products use `ppu001` and HGCC `ppu_10`; documented
M890/PPU1.5 uses `ppu0015` and `ppu_15`. Confirm a locally named ZW890 against
the actual device identity. CUDA-compatible compute capability alone is not
a PPU-generation identifier. PPU1.7 history has its own source/model scope.

Use the task's working PPU build and official dependencies. Match its actlize
architecture tags, atom traits, AIU/copy interfaces and fragment layouts to the
actual generation. Inspect native code with the selected SDK's hgobjdump when
lowering or resource use matters. Keep accuracy and timing gates on the actual
PPU and compare the same input, cache and complete-operation scope.

The repository's `scripts/inspect_ppu.py` is a setup-time host runtime query;
it records identity and tools without selecting an ISA or launching a kernel.
It requires the installed SDK headers/libraries and a compatible host C++
compiler. Successful inspection does not establish a working kernel backend.

See [official documentation](official-docs.md) for source versions and gaps,
and [profiler access](../../ppu-profiling/references/tool-access.md) for native
collection. Neither skill changes ForgeKernel's execution backend by itself.
