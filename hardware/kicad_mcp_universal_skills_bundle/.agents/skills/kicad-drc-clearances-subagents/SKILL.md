---
name: kicad-drc-clearances-subagents
description: >-
  Enforce zero-ignore ERC/DRC checks, clearances, power track widths, copper pours,
  netlist-to-PCB pin parity, and subagent task delegation for functional KiCad PCBs.
---

# PCB Clearances, Zero-Ignore DRC & Subagent Workflow

Use this skill to ensure every designed PCB is electrically sound, manufacturable, free of hidden rule ignores, and cleanly parallelized when your AI environment supports subagents.

---

## 1. Zero-Ignore ERC & DRC Policy
In `<project>.kicad_pro`:
- Set **every** key in `schematic.erc.rule_severities` and `board.design_settings.rule_severities` to `"error"` or `"warning"` — **never `"ignore"`**.
- Always run CLI checks with `--severity-all` and `--schematic-parity`:
  - `erc_report.txt`: require `0 Errors, 0 Warnings, Ignored checks: None`.
  - `drc_report.txt`: require `0 DRC violations, 0 unconnected pads, 0 Footprint errors, Ignored checks: None`.

---

## 2. Functional PCB Clearance & Layout Checklist
- **Unmodified Library Footprints**: Keep pad shapes, courtyards, and footprint silkscreen graphics unchanged (`0` `lib_footprint_mismatch`). Only hide `Value` or reposition `Reference` text.
- **Track Widths & Routing**:
  - Power rails (`BAT+`, `VIN`, `5V`, `3V3`, `SW_BACK`): `>= 1.0 mm` for currents up to ~1 A (adjust higher for >1 A).
  - Signal traces: `>= 0.25–0.30 mm`, 45-degree corners, zero acute acid traps, zero same-layer crossings.
- **Solder Mask & Board-Edge Rules**:
  - `pad_to_mask_clearance` (`ds.m_SolderMaskExpansion` in KiCad 10): `0.05 mm`.
  - `solder_mask_min_width` (`ds.m_SolderMaskMinWidth`): `0.10 mm` (prevents mask slivers).
  - `min_copper_edge_clearance`: `>= 0.40 mm` (`>= 0.50 mm` for tracks to edge).
- **Copper Pours & GND Stitching**:
  - Pour `GND` on both `F.Cu` and `B.Cu` with `0.5 mm` thermal spoke width and `0.3 mm` thermal gap (`>= 0.45 mm` edge inset).
  - Add mounting-hole keepouts (`zone.SetIsRuleArea(True)`, `SetDoNotAllowCopperPour(True)`, `SetDoNotAllowPads(False)`).
  - Place `0.8 / 0.4 mm` GND stitching vias every `5–8 mm`, checking distance to pads, tracks, keepouts, and `F.SilkS` text bounding boxes.
- **Mechanical & Silkscreen**:
  - Confirm `>= 3.0 mm` clearance from external connectors/headers to module outlines (e.g., ESP32 DevKit) and mounting holes.
  - Keep `F.SilkS` text height `>= 1.0 mm`, stroke thickness `>= 0.15 mm`, and `0` overlap with pads, vias, holes, or board edges.

---

## 3. Programmatic Verification Script (Mandatory Before Manufacturing)
Run a Python verification script (`pcbnew` + `exports/netlist.xml`) that asserts:
1. Every pin on every connector/component matches the expected net (including `NC` pins).
2. Zero mismatches between schematic netlist XML and PCB pads.
3. Exact count of active nets, `GND` pins, and power pins.
4. Minimum power track width (`>= 1.0 mm`), connector-to-module clearance (`>= 3.0 mm`), and hole-to-pin clearance (`>= 3.0 mm`).

---

## 4. Subagent Parallelization Pattern (When Supported by AI Host)
If your AI assistant supports spawning subagents (e.g., Antigravity `invoke_subagent`), parallelize **independent** read-only or isolated tasks — never let two agents edit `.kicad_pcb` or `.kicad_sch` concurrently:
- **Subagent A (`research`)**: Verify footprint names, pinouts, 3D model paths, and KiCad library dimensions before schematic capture.
- **Main Agent**: Owns `.kicad_sch`, `.kicad_pcb`, `pcbnew` routing script, and `kicad-cli` ERC/DRC gates sequentially.
- **Subagent B (`flash` / helper)**: Once `.kicad_pcb` passes 0-violation DRC, generate/verify BOM CSV, Pin Table CSV, JSON metadata, and web embed docs in parallel while main agent runs `kicad-cli pcb render`.
- **Subagent C (`research` / QA)**: Independently audit `erc_report.txt`, `drc_report.txt`, JLCPCB ZIP file list (no paste/`drl_map`/`.gbrjob`), and rendered PNGs.
