# KiCad 10 Engineering Notes & Gotchas

1. **`m_SolderMaskExpansion` (KiCad 10 API)**:
   - KiCad 10 renamed `BOARD_DESIGN_SETTINGS.m_SolderMaskMargin` to `m_SolderMaskExpansion`.
   - Set `ds.m_SolderMaskExpansion = pcbnew.FromMM(0.05)` and `ds.m_SolderMaskMinWidth = pcbnew.FromMM(0.10)`.

2. **Board Finish (`HAL lead-free`) in `.kicad_pcb`**:
   - When generating a board via `pcbnew` from scratch, `.kicad_pcb` `(setup ...)` may omit the `(stackup ...)` block.
   - Inject `(stackup ... (layer "dielectric 1" (type "core") (thickness <core_mm>) (material "FR4") ...) ... (copper_finish "HAL lead-free") ...)` inside `(setup ...)` for explicit 1.2 mm / 1.6 mm stackup and finish documentation.

3. **Zero `lib_footprint_mismatch` DRC**:
   - Never alter footprint pads, silk lines, or courtyard shapes inside a loaded PCB footprint. Only move `fp.Reference()` / toggle `fp.Value().SetVisible(False)`, and place custom board silkscreen as board-level `PCB_TEXT` / `PCB_SHAPE` on `F.SilkS`.

4. **PDF Export Flags for 2D Layer Compositing**:
   - `kicad-cli pcb export pdf` does not have `--page-size-mode`. Use `--mode-single --scale 1 --black-and-white --drill-shape-opt 2` and crop tightly to the `Edge.Cuts` pixel bounding box.
   - Always separate tracks+pads (from a temporary zone-stripped `.kicad_pcb` copy) from filled GND zones so `F.Cu` (red) and `B.Cu` (blue) traces remain vividly readable over opposite-layer copper pours.

5. **3D Stand-In Mockups in VRML (`.wrl`)**:
   - KiCad interprets VRML 2.0 (`#VRML V2.0 utf8`) coordinates in `0.1 inch` units (`1 VRML unit = 2.54 mm`). Divide all millimeter dimensions and translations by `2.54` when generating temporary clearance-check `.wrl` stand-in boxes for `kicad-cli pcb render`.
