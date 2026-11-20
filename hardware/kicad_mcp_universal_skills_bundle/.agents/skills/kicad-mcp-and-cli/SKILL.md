---
name: kicad-mcp-and-cli
description: >-
  Install KiCad 8/9/10, KiCAD-MCP-Server, KiCad CLI, and Freerouting on Windows and
  Linux, configure mcp.json, and run common kicad-cli commands for ERC, DRC, and exports.
---

# KiCad, KiCad MCP & `kicad-cli` Setup & Reference

Use this skill to install KiCad and `KiCAD-MCP-Server`, wire up `mcp.json`, and run `kicad-cli` commands reliably on Windows and Linux.

---

## 1. Installing KiCad & `kicad-cli`

### Windows
```powershell
winget install --id KiCad.KiCad -e
```
Default binaries (KiCad 10.0; adjust version folder if using 8.0/9.0):
- `kicad-cli.exe`: `%LOCALAPPDATA%\Programs\KiCad\10.0\bin\kicad-cli.exe`
- `python.exe`: `%LOCALAPPDATA%\Programs\KiCad\10.0\bin\python.exe`
- `site-packages`: `%LOCALAPPDATA%\Programs\KiCad\10.0\bin\Lib\site-packages`

Add `%LOCALAPPDATA%\Programs\KiCad\10.0\bin` to your user `PATH`, then verify:
```powershell
kicad-cli --version
```

### Linux (Ubuntu / Debian)
```bash
sudo add-apt-repository --yes ppa:kicad/kicad-9.0-releases   # or kicad-8.0-releases / distro repo
sudo apt update
sudo apt install -y kicad kicad-libraries
kicad-cli --version
```
*(If using Flatpak KiCad, invoke CLI via `flatpak run --command=kicad-cli org.kicad.KiCad`.)*

---

## 2. Installing `KiCAD-MCP-Server`

Clone and build the MCP server (`mixelpixx/KiCAD-MCP-Server`):

### Windows (PowerShell)
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.gemini\tools" | Out-Null
git clone https://github.com/mixelpixx/KiCAD-MCP-Server.git "$env:USERPROFILE\.gemini\tools\KiCAD-MCP-Server"
Set-Location "$env:USERPROFILE\.gemini\tools\KiCAD-MCP-Server"
npm install
npm run build
```

### Linux (Bash)
```bash
mkdir -p ~/.gemini/tools
git clone https://github.com/mixelpixx/KiCAD-MCP-Server.git ~/.gemini/tools/KiCAD-MCP-Server
cd ~/.gemini/tools/KiCAD-MCP-Server
npm install
npm run build
```

*(Optional)* Download `freerouting.jar` from `https://github.com/freerouting/freerouting/releases` into `~/.kicad-mcp/freerouting.jar` (`%USERPROFILE%\.kicad-mcp\freerouting.jar` on Windows) for autorouting support.

---

## 3. Wiring `mcp.json` / `mcp_config.json`
Use the included `mcp.windows.json` or `mcp.linux.json` templates in this bundle and replace `<USER>` / home paths with your exact user directory.
- **Antigravity global config**: `~/.gemini/antigravity/mcp_config.json` (Windows: `%USERPROFILE%\.gemini\antigravity\mcp_config.json`)
- **Workspace / IDE `mcp.json`**: `.vscode/mcp.json` or `<project>/mcp.json` depending on your AI client.

---

## 4. Common `kicad-cli` Commands (Windows & Linux)

### Schematic ERC & Netlist
```bash
kicad-cli sch erc --severity-all --format report --output exports/erc_report.txt board.kicad_sch
kicad-cli sch erc --severity-all --format json   --output exports/erc_report.json board.kicad_sch
kicad-cli sch export netlist --format kicadxml --output exports/netlist.xml board.kicad_sch
kicad-cli sch export svg --output exports/ board.kicad_sch
```

### PCB DRC (Strict Schematic Parity)
```bash
kicad-cli pcb drc --schematic-parity --severity-all --format report --output exports/drc_report.txt board.kicad_pcb
kicad-cli pcb drc --schematic-parity --severity-all --format json   --output exports/drc_report.json board.kicad_pcb
```

### Fabrication Exports (JLCPCB)
```bash
# Omit F.Paste / B.Paste on through-hole-only boards
kicad-cli pcb export gerbers --layers "F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts" --output gerbers/ board.kicad_pcb
kicad-cli pcb export drill --format excellon --excellon-units mm --generate-map --map-format gerberx2 --output gerbers/ board.kicad_pcb
```

### 3D CAD, Web GLB & Renders
```bash
kicad-cli pcb export step --subst-models --output exports/board.step board.kicad_pcb
kicad-cli pcb export glb --subst-models --include-tracks --include-pads --include-zones --include-silkscreen --include-soldermask --cut-vias-in-body --grid-origin --output exports/board.glb board.kicad_pcb
kicad-cli pcb render --side top    --width 1920 --height 1440 --background opaque --quality high --output exports/view_top_3d.png board.kicad_pcb
kicad-cli pcb render --side bottom --width 1920 --height 1440 --background opaque --quality high --output exports/view_bottom_3d.png board.kicad_pcb
kicad-cli pcb render --rotate "-48,0,28" --zoom 1.0 --width 1920 --height 1440 --background opaque --quality high --output exports/view_iso_3d.png board.kicad_pcb
```
