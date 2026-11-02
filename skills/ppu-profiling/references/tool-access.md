<!-- SPDX-License-Identifier: Apache-2.0 -->

# Native PPU profiler access

Use ACU to answer a kernel-counter or native-instruction question and Asys to
attribute time across launches, transfers and waits. The selected PPU SDK and
its runtime/driver must agree. Shell access to their CLI tools is sufficient;
an MCP is an optional transport and does not grant access to a device.

## Evidence contract

Keep the actual device/model, SDK/tool version, source/binary identity, selected
launch or range, input shape/layout and cache/replay policy with every report.
Preserve original metric names, units, aggregation and raw reports. Missing
metrics are unavailable, not zero. A model result, ACU replay time, clean event
timing and Asys activity duration are different evidence.

Use [collection](collection.md), [metrics](metrics.md), [timeline](timeline.md)
and [analysis](analysis.md) according to the current question. Verify installed
help and schemas before adapting commands across SDK versions. PPU counters
are not NVIDIA metric names with a renamed prefix; NVIDIA SASS, PM-sampling
and NCU helper scripts require their original input formats.

## MCP access

The official Asight2.2.0 documentation describes Asys GUI/CLI MCP access and
an ACU Python report interface. Inspect the interfaces present on the target
installation; their documentation does not establish that a different SDK
contains them. See the [official map](../../ppu-kernel-knowledge/references/official-docs.md).

In an orchestrated ForgeKernel run, use the driver's existing probe/submission
channel rather than launching an unrecorded job. A standalone local coding
agent may invoke tools within the allocated device and task scope. Keep
profiling separate from the clean benchmark used for a candidate's promotion.
