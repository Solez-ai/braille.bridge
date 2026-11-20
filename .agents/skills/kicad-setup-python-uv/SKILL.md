---
name: kicad-setup-python-uv
description: >-
  Install prerequisites online and configure Python, uv, Node.js, and KiCad Python
  bindings on both Windows and Linux for automated PCB design, verification, and rendering.
---

# Online Prerequisites, Python & `uv` Setup (Windows & Linux)

Use this skill when bootstrapping a fresh Windows or Linux machine so AI agents and scripts can run `uv`, Python imaging/PDF libraries (`pymupdf`, `pillow`, `numpy`), Node.js (for KiCad MCP), and KiCad's `pcbnew` module.

---

## 1. Windows Setup (PowerShell)

1. **Install `uv` (Astral Python & venv manager)**:
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   Verify: `uv --version`

2. **Install Python 3.11+ & Node.js 20+ LTS & Git**:
   ```powershell
   winget install --id Python.Python.3.12 -e
   winget install --id OpenJS.NodeJS.LTS -e
   winget install --id Git.Git -e
   ```
   *(Or use `uv python install 3.12` if Python is not yet installed.)*

3. **Create a project `uv` environment for rendering, verification & ZIP tooling**:
   ```powershell
   uv venv .venv
   .\.venv\Scripts\Activate.ps1
   uv pip install pymupdf pillow numpy
   ```
   *Note*: Keep KiCad `pcbnew` scripts running under **KiCad's bundled Python**:
   `C:\Users\<USER>\AppData\Local\Programs\KiCad\10.0\bin\python.exe`
   and run PDF/PNG rendering scripts (`pymupdf`, `PIL`) under `.venv\Scripts\python.exe` (or `uv run python ...`).

4. **Optional (Freerouting autorouter)**:
   ```powershell
   winget install --id EclipseAdoptium.Temurin.21.JRE -e
   ```

---

## 2. Linux Setup (Ubuntu / Debian / Arch / Fedora)

1. **Install `uv`**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.bashrc   # or ~/.zshrc
   uv --version
   ```

2. **Install Node.js 20+, Git, and system Python + `pcbnew` bindings**:
   - **Ubuntu / Debian**:
     ```bash
     sudo apt update
     sudo apt install -y git curl nodejs npm python3 python3-pip python3-venv python3-pcbnew
     ```
     *(If distro `nodejs` is older than v20, install Node 20 LTS via NodeSource or `nvm install 20`.)*
   - **Fedora**:
     ```bash
     sudo dnf install -y git curl nodejs npm python3 python3-pip kicad
     ```
   - **Arch**:
     ```bash
     sudo pacman -S --needed git curl nodejs npm python python-pip kicad
     ```

3. **Create a `uv` environment for rendering & verification tools**:
   ```bash
   uv venv .venv --system-site-packages
   source .venv/bin/activate
   uv pip install pymupdf pillow numpy
   ```
   *Tip*: Passing `--system-site-packages` on Linux lets the `.venv` import system `pcbnew` directly alongside `pymupdf`, `pillow`, and `numpy`!

---

## 3. Verification Checklist
Run these commands to confirm the environment is ready:
```text
uv --version
node -v          # >= v20.x
npm -v
git --version
```
- **Windows KiCad Python check**:
  `& "$env:LOCALAPPDATA\Programs\KiCad\10.0\bin\python.exe" -c "import pcbnew; print(pcbnew.Version())"`
- **Linux KiCad Python check**:
  `python3 -c "import pcbnew; print(pcbnew.Version())"`
- **Rendering stack check (`uv` venv)**:
  `uv run python -c "import pymupdf, PIL, numpy; print('RENDER_DEPS_OK')"`
