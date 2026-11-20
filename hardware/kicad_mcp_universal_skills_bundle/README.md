# Universal KiCad MCP + PCB Engineering Skills Bundle

Drop-in AI engineering suite for designing, routing, verifying (zero-ignore ERC/DRC), rendering (2D/3D/GLB), and manufacturing KiCad 8/9/10 PCBs on **Windows** and **Linux**.

## Included Files
- `mcp.json` / `mcp.windows.json` / `mcp.linux.json` — `KiCAD-MCP-Server` configuration templates.
- `.agents/skills/kicad-pcb-engineering/SKILL.md` — **Main orchestrator skill** (+ `scripts/render_2d_composite.py` & `references/kicad_10_notes.md`).
- `.agents/skills/kicad-setup-python-uv/SKILL.md` — Online installation + Python & `uv` setup (Windows & Linux).
- `.agents/skills/kicad-mcp-and-cli/SKILL.md` — KiCad, `mixelpixx/KiCAD-MCP-Server`, `kicad-cli`, and common CLI commands (Windows & Linux).
- `.agents/skills/kicad-drc-clearances-subagents/SKILL.md` — Clearances, zero-ignore ERC/DRC, netlist parity, and subagent delegation.
- `.agents/skills/kicad-rendering-deliverables/SKILL.md` — 2D/3D PCB renders, silkscreen checks, schematic SVGs, JLCPCB Gerbers, STEP, and Web `.glb`.

## Quick Start
1. Extract this ZIP into the root of any project (places skills under `.agents/skills/`) or copy `.agents/skills/*` into `~/.gemini/config/skills/` for global use across all projects.
2. Pick `mcp.windows.json` or `mcp.linux.json`, replace `<YOUR_USER>` with your username, and merge into `~/.gemini/antigravity/mcp_config.json` (or your IDE `mcp.json`).
3. Ask your AI assistant to run `kicad-setup-python-uv` and `kicad-mcp-and-cli` if KiCad / MCP / `uv` are not yet installed.
