# BB1 Wiring Board v4 — Final Engineering Report (ADDENDUM v4)

**Deviations from ADDENDUM v4 / v3**: None.
- **J5 Buck-Boost Module Pin Order**: **CONFIRMED** by user (`pin 1 = VIN, pin 2 = GND, pin 3 = VOUT, pin 4 = EN`), parameterized via `J5_PIN_ORDER` in the schematic and PCB generators.
- **Project Location**: `hardware/bb1_wiring_board_v4/` (confirmed by user).

---

## 1. Board & Stackup Summary
- **Final Board Dimensions**: **`66.0 × 52.0 × 1.2 mm`** (`1.5 mm` corner radius), 2-layer FR-4, 1 oz copper, **HASL lead-free** (`HAL lead-free`).
- **ESP32 Sockets (`J2`, `J4`)**: `2 × PinSocket_1x19_P2.54mm_Vertical`, exact **`20.300 mm`** row spacing (`0.8"`).
- **Power Module Socket (`J5`)**: `PinSocket_1x04_P2.54mm_Vertical` inside a `12.0 × 8.8 mm` silkscreen keep-out (`16.55 mm` from ESP32 outline, `7.10 mm` from `J1` male pins, `34.00 mm` from `J3` male pins).
- **Mode Selector Jumper (`JP1`)**: `PinHeader_1x03_P2.54mm_Vertical` (+ 1 × 2.54 mm jumper shunt).
- **Schottky Diodes (`D1`, `D2`)**: `2 × 1N5819` (`Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal`).
- **Power Copper Width**: **`1.00 mm`** on all 6 power nets (`BAT_POS`, `SW_BACK`, `MOD_IN`, `V5_MOD`, `DIODE_IN`, `VIN`); **`0.30 mm`** on all 8 switch nets (`D1–D6`, `SPACE`, `SHIFT`).
- **GND Pours & Vias**: Dual-layer `F.Cu` + `B.Cu` GND pours (`0.45 mm` edge inset, `0.50 mm` thermal spoke, `0.30 mm` gap) stitched with **`27` GND vias** + `4` signal vias (**`31` vias total**), **`12` GND pins** connected.

---

## 2. Verification Results (Zero-Ignore ERC / DRC / Parity)
1. **ERC (`exports/erc_report.txt`)**: **`0 Errors, 0 Warnings`**, `Ignored checks: None`.
2. **DRC (`exports/drc_report.txt`, `--schematic-parity --severity-all`)**: **`0 DRC violations, 0 unconnected pads, 0 Footprint errors`**, `Ignored checks: None`.
3. **Programmatic Netlist-to-PCB Audit (`exports/verification_output.txt`)**:
   - **71 pins checked** (`41` connected, `30` NC), **`0` mismatches**.
   - **Active nets (`15`)**: `BAT_POS`, `D1`, `D2`, `D3`, `D4`, `D5`, `D6`, `DIODE_IN`, `GND`, `MOD_IN`, `SHIFT`, `SPACE`, `SW_BACK`, `V5_MOD`, `VIN`.
   - **`JP1`**: Pin 1 = `SW_BACK`, Pin 2 = `DIODE_IN`, Pin 3 = `V5_MOD` (mutually isolated; no two touch anywhere).
   - **`D2`**: Pin 2 (Anode) = `SW_BACK`, Pin 1 (Cathode, band) = `MOD_IN` (`MOD_IN` connects **only** `D2.1` and `J5.1`).
   - **`J5`**: Pin 1 (`VIN`) = `MOD_IN`, Pin 2 (`GND`) = `GND`, Pin 3 (`VOUT`) = `V5_MOD` (`V5_MOD` connects **only** `J5.3` and `JP1.3`), Pin 4 (`EN`) = `NC` (`no_connect`).
   - **`D1`**: Pin 2 (Anode) = `DIODE_IN`, Pin 1 (Cathode, band) = `VIN` (`VIN` connects **only** `D1.1` and `J2.19`).
   - **`GND`**: **Exactly `12` pins** (`J1` even pins 2..16, `J2.14`, `J3.4`, `J4.1`, `J5.2`).
   - **v3 Key Nets & ESP32 Pinout**: 100% unchanged (`D1–D6`, `SPACE`, `SHIFT`, `BAT_POS`).
4. **Short Check**: `0` copper clearance violations in DRC + programmatic 1:1 net-to-pad parity verified across all 71 pads.

---

## 3. Hand-Simulated Jumper Current Paths
- **Position 1 — Bypass (`JP1` shunt on pins `1-2`, `1-2 AA direct`, max `6.5 V`)**:
  `Battery (+)` → `J3.3 (BAT+)` → `J3.2 (BAT+>SW)` → off-board slide switch → `J3.1 (SW_BACK)` → `JP1.1` ==shunt== `JP1.2 (DIODE_IN)` → `D1` (Anode → Cathode) → `VIN` → `J2.19 (ESP32 V5)`, returning via `GND` pour to `J3.4 (BAT-)`. *(J5 module may be omitted; if present, its output `V5_MOD` is open-circuited at `JP1.3`.)*
- **Position 2 — Regulated (`JP1` shunt on pins `2-3`, `2-3 5V module`, `3–16 V` max)**:
  `Battery (+)` → `J3.3` → `J3.2` → slide switch → `J3.1 (SW_BACK)` → `D2` (reverse-battery guard) → `MOD_IN` → `J5.1 (VIN)` → `[Pololu S9V11F5 5V Buck-Boost]` → `J5.3 (VOUT / V5_MOD)` → `JP1.3` ==shunt== `JP1.2 (DIODE_IN)` → `D1` (USB back-feed guard) → `VIN` → `J2.19 (ESP32 V5)`, returning via `J5.2` & `GND` pour to `J3.4 (BAT-)`.
- **No Shunt Installed**: `DIODE_IN` is disconnected from both `SW_BACK` and `V5_MOD`; ESP32 receives no battery power (and the center-common layout prevents `SW_BACK` and `V5_MOD` from ever shorting).

---

## 4. Silkscreen Audit (All New Text >= 1.20 mm, Zero Overlap)
- `J5`: `5V module` (`1.25 mm`), `VIN`, `GND`, `VOUT`, `EN` (`1.20 mm`), pin 1 marker `1` + square pad, `12.0 × 8.8 mm` keep-out box.
- `D2`: `D2`, `1N5819`, `K` cathode mark, `band = to module` (`1.20 mm`).
- `JP1`: `JP1`, `1-2 AA direct`, `2-3 5V module`, pin 1 marker `1` + square pad (`1.20 mm`).
- Next to `J3`: `JP1 1-2: max 6.5V` and `module: 3-16V max` (`1.20 mm`, exact spelling).
- Preserved v3 markings: `braille bridge by solez-ai`, `solez.vercel.app`, `12* boot pin: no pull-up`, `D1`, `1N5819`, `band = to VIN`, `antenna`, `usb ->`, `J1` `S/G` & `D1..SHIFT`, `J3` `BAT-..SW BACK`.

---

## 5. Deliverables Generated
- KiCad 10 Project: `bb1_wiring_board_v4.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, `bb1_v4.kicad_sym`, `sym-lib-table`
- Manufacturing Archive: `bb1_wiring_board_v4_jlcpcb.zip` (strictly 8 files: `.gtl`, `.gbl`, `.gts`, `.gbs`, `.gto`, `.gbo`, `.gm1`, `.drl`) + `bb1_wiring_board_v4_deliverables.zip`
- Reports & Tables: `exports/erc_report.txt/.json`, `exports/drc_report.txt/.json`, `exports/verification_output.txt`, `exports/bb1_wiring_board_v4_bom.csv/.json`, `exports/bb1_wiring_board_v4_pins.csv/.json`
- Visuals & CAD: `exports/view_top_2d.png`, `exports/view_top_3d.png`, `exports/view_bottom_3d.png`, `exports/view_iso_3d.png`, `exports/view_iso_3d_esp32_clearance.png`, `exports/bb1_wiring_board_v4.svg`, `.step`, `.glb`
