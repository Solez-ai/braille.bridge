---
name: kicad-pcb-engineering
description: >-
  End-to-end KiCad 8/9/10 PCB engineering workflow using KiCad CLI, KiCad Python (pcbnew),
  and KiCad MCP tools. Use when designing schematics and PCBs, fixing ERC/DRC violations,
  routing 2-layer boards, verifying pin/netlist parity, exporting JLCPCB manufacturing
  packages (Gerbers, Excellon drill, BOM, STEP, GLB), or rendering 2D/3D PCB previews.
---

# KiCad PCB Engineering Workflow

Use this runbook to design, verify, render, and package complete KiCad 10+ PCB projects with **zero ERC/DRC ignores** and verified netlist-to-PCB parity.

## Tooling & Environment (Windows)
- **KiCad CLI**: `C:\Users\<user>\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe` (or `kicad-cli` on `PATH`)
- **KiCad Python (`pcbnew`)**: `C:\Users\<user>\AppData\Local\Programs\KiCad\10.0\bin\python.exe`
  *(Use system Python for `pymupdf` / `PIL` / `numpy`, and KiCad's bundled `python.exe` for `import pcbnew`.)*
- **KiCad MCP**: Prefer KiCad MCP tools when inspecting/modifying project state interactively; use scripted KiCad Python (`pcbnew`) + `kicad-cli` for deterministic routing, zone fills, batch DRC/ERC, and rendering.

---

## Phase 1: Project Setup & Zero-Ignore Rules
1. **Enable ALL ERC and DRC rules** in `<project>.kicad_pro`:
   - Never set any `rule_severities` key to `"ignore"` — set all checks to `"error"` or `"warning"`.
   - Set board constraints explicitly in `board.design_settings.rules` (e.g., `min_copper_edge_clearance`, `min_via_diameter`, `solder_mask_min_width`, `pad_to_mask_clearance`).
2. **Custom Symbols**:
   - Store project-specific schematic symbols (e.g., dev-board pinout headers) in `<project>.kicad_sym` and register via `sym-lib-table`.
   - Set `ki_fp_filters` to match the target footprint and mark every unused pin with schematic `no_connect` (`×`) markers.

---

## Phase 2: Schematic Capture & ERC Gate
1. Wire every active net with explicit global/local labels and power flags (`#FLG01..`) where needed.
2. Export netlist XML and run strict ERC:
   ```powershell
   kicad-cli sch export netlist --format kicadxml --output exports/netlist.xml <project>.kicad_sch
   kicad-cli sch erc --severity-all --format report --output exports/erc_report.txt <project>.kicad_sch
   ```
3. **Gate**: Confirm `ERC messages: 0  Errors 0  Warnings 0` and `Ignored checks: None`.

---

## Phase 3: PCB Layout, Routing & Stackup (`pcbnew`)
1. **Sync Schematic -> PCB** without modifying library footprint shapes (`0` `lib_footprint_mismatch`). You may reposition `Reference` text or hide `Value` text, but keep pad geometries and footprint silk/courtyard primitives intact.
2. **Design Settings (KiCad 10 Python)**:
   - Use `ds.m_SolderMaskExpansion` (renamed from `m_SolderMaskMargin` in KiCad 10; see [references/kicad_10_notes.md](./references/kicad_10_notes.md)).
   - Inject `(stackup ... (copper_finish "HAL lead-free"))` into `.kicad_pcb` `(setup ...)` when HASL lead-free is required.
3. **Routing & Pours**:
   - Use 45-degree bends, zero layer-same-net crossings, and power traces sized for current margin (e.g., `>= 1.0 mm` for power rails).
   - Add `F.Cu` and `B.Cu` copper pours (`GND`) with `0.5 mm` thermal spokes, `0.3 mm` gap, and `>= 0.4 mm` board-edge inset.
   - Add mounting-hole rule-area keepouts (`zone.SetIsRuleArea(True)`, `SetDoNotAllowPads(False)`, `SetDoNotAllowCopperPour(True)`).
   - Stitch top and bottom `GND` pours with `0.8 / 0.4 mm` vias placed clear of pads, tracks, keepouts, and `F.SilkS` text bounding boxes.
   - Run `pcbnew.ZONE_FILLER(board).Fill(board.Zones())` before saving.

---

## Phase 4: Zero-Ignore DRC & Programmatic Verification
1. Run full schematic-parity DRC:
   ```powershell
   kicad-cli pcb drc --schematic-parity --severity-all --format json --output exports/drc_report.json <project>.kicad_pcb
   kicad-cli pcb drc --schematic-parity --severity-all --format report --output exports/drc_report.txt <project>.kicad_pcb
   ```
2. **Gate**: Confirm `0` violations, `0` unconnected pads, `0` footprint errors, `0` parity issues, and `Ignored checks: None`.
3. **Programmatic Verification Script** (via KiCad Python `pcbnew` + `exports/netlist.xml`):
   - Assert every pin of every connector/component matches the expected net (including `NC` pins).
   - Assert total active net count, `GND` pin count, minimum power/signal track widths, connector-to-keepout clearances, and export complete BOM CSV + Pin Table CSV.

---

## Phase 5: Exports, Previews & Deliverables
1. **Schematic SVG**: `kicad-cli sch export svg --output exports/ <project>.kicad_sch`
2. **Gerbers & Drill (JLCPCB)**:
   - Plot ONLY required fabrication layers (omit `F.Paste`/`B.Paste` on THT-only boards):
     ```powershell
     kicad-cli pcb export gerbers --layers "F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" --output gerbers/ <project>.kicad_pcb
     kicad-cli pcb export drill --format excellon --excellon-units mm --generate-map --map-format gerberx2 --output gerbers/ <project>.kicad_pcb
     ```
   - Build `<project>_jlcpcb.zip` containing **ONLY** `.gtl`, `.gbl`, `.gts`, `.gbs`, `.gto`, `.gbo`, `.gm1`, `.drl` (exclude `-drl_map.gbr`, `.gbrjob`, and paste layers).
3. **3D Models**:
   - **STEP** (mechanical CAD): `kicad-cli pcb export step --subst-models --output exports/<project>.step <project>.kicad_pcb`
   - **GLB** (interactive web 3D viewer): `kicad-cli pcb export glb --subst-models --include-tracks --include-pads --include-zones --include-silkscreen --include-soldermask --cut-vias-in-body --grid-origin --output exports/<project>.glb <project>.kicad_pcb`
4. **High-Res Preview Renders (`>= 1600 px`)**:
   - Top, Bottom, and Isometric 3D raytraced PNGs:
     ```powershell
     kicad-cli pcb render --side top --width 1920 --height 1440 --background opaque --quality high --output exports/view_top_3d.png <project>.kicad_pcb
     kicad-cli pcb render --side bottom --width 1920 --height 1440 --background opaque --quality high --output exports/view_bottom_3d.png <project>.kicad_pcb
     kicad-cli pcb render --rotate "-48,0,28" --zoom 1.0 --width 1920 --height 1440 --background opaque --quality high --output exports/view_iso_3d.png <project>.kicad_pcb
     ```
   - Light-background 2D composite (`F.Cu` red, `B.Cu` blue, silkscreen, drills): run [scripts/render_2d_composite.py](./scripts/render_2d_composite.py).
5. **Visual Inspection Gate**: Open EVERY generated PNG via `read_file` and verify silkscreen legibility, zero colliding labels, correct polarity/band markings, and clean clearances before packaging the final ZIP.
