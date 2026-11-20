---
name: kicad-rendering-deliverables
description: >-
  Generate high-resolution 2D copper/silkscreen PCB composites, 3D raytraced renders,
  3D clearance stand-in views, schematic SVGs, JLCPCB Gerber ZIPs, STEP, and Web GLB packages.
---

# KiCad Rendering, Previews & Deliverable Packaging

Use this skill to produce publication-grade 2D/3D PCB visuals, clean JLCPCB manufacturing archives, and interactive web viewer bundles.

---

## 1. High-Resolution 3D Renders (`>= 1600 px`)
Run KiCad's built-in raytracer via `kicad-cli pcb render`:
```bash
kicad-cli pcb render --side top    --width 1920 --height 1440 --background opaque --quality high --output exports/view_top_3d.png board.kicad_pcb
kicad-cli pcb render --side bottom --width 1920 --height 1440 --background opaque --quality high --output exports/view_bottom_3d.png board.kicad_pcb
kicad-cli pcb render --rotate "-48,0,28" --zoom 1.0 --width 1920 --height 1440 --background opaque --quality high --output exports/view_iso_3d.png board.kicad_pcb
```

### 3D Mechanical Clearance Stand-In Render
To visually verify daughterboard/module clearance (e.g., ESP32 DevKit plugged into female sockets):
1. Generate a temporary VRML 2.0 (`.wrl`) translucent box (`#VRML V2.0 utf8`) with dimensions divided by `2.54` (`1 VRML unit = 0.1 in = 2.54 mm` in KiCad).
2. Attach it to a dummy footprint on a **temporary copy** of `.kicad_pcb`.
3. Render `view_iso_3d_clearance.png` with `kicad-cli pcb render` (never modify the deliverable `.kicad_pcb`).

---

## 2. Crisp Light-Background 2D Composite (`view_top_2d.png`)
Do not render solid overlapping copper pours with opaque colors — tracks inside pours become unreadable. Instead, use `scripts/render_2d_composite.py` from `kicad-pcb-engineering`:
- Separates filled GND pours (subtle translucent red/blue tint) from tracks & pads (vivid red `F.Cu`, vivid blue `B.Cu`, plum plated through-hole pads/vias).
- Draws razor-sharp dark `F.Silkscreen`, `Edge.Cuts`, and white drill centers on a `#F8F9FB` light background at `2000 px` width with a color legend.

---

## 3. Schematic, Silkscreen & Gerber Outputs
- **Schematic SVG**: `kicad-cli sch export svg --output exports/ board.kicad_sch`
- **Gerbers + Excellon Drill**:
  ```bash
  kicad-cli pcb export gerbers --layers "F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" --output gerbers/ board.kicad_pcb
  kicad-cli pcb export drill --format excellon --excellon-units mm --generate-map --map-format gerberx2 --output gerbers/ board.kicad_pcb
  ```
- **JLCPCB ZIP Rules**:
  - Include ONLY: `.gtl`, `.gbl`, `.gts`, `.gbs`, `.gto`, `.gbo`, `.gm1`, `.drl`.
  - **Exclude**: `F_Paste`, `B_Paste` (on THT-only boards), `-drl_map.gbr`, and `-job.gbrjob`.

---

## 4. Web Interactive Package (`.glb` + KiCanvas)
For interactive browser inspection (3D orbit/zoom/pan + live schematic + 2D PCB + BOM):
- Export binary glTF:
  ```bash
  kicad-cli pcb export glb --subst-models --include-tracks --include-pads --include-zones --include-silkscreen --include-soldermask --cut-vias-in-body --grid-origin --output exports/board.glb board.kicad_pcb
  ```
- Bundle `.glb` alongside `.kicad_sch`, `.kicad_sym`, `sym-lib-table`, `.kicad_pcb`, `.kicad_pro`, `.svg`, `bom.csv/.json`, and `pins.csv/.json` for `<model-viewer>` + `<kicanvas-embed>`.

---

## 5. Mandatory Visual Inspection Gate
Before delivering any ZIP or report, open **every** rendered PNG (`view_top_3d.png`, `view_bottom_3d.png`, `view_iso_3d.png`, `view_top_2d.png`, and any clearance render) and verify:
- Zero overlapping or clipped silkscreen text.
- Polarity/diode band markings (`K`, `band = to VIN`) match copper nets.
- Routing shows zero unintended overlaps and clean thermal reliefs.
