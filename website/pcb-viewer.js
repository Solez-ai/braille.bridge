(function () {
  'use strict';

  const PCB_3D_VIEWS = {
    iso: {
      src: 'assets/pcb/view_iso_3d.png',
      alt: 'KiCad 3D raytraced isometric render of BrailleBridge BB1 Wiring Board v4 with plug-in 5V buck-boost socket J5 and JP1 jumper',
      status: 'Isometric 3D · J2/J4 ESP32, J1 8× switch, J3 power, J5 5V buck-boost socket, JP1 selector, D1/D2 1N5819'
    },
    top: {
      src: 'assets/pcb/view_top_3d.png',
      alt: 'KiCad 3D raytraced top view of BrailleBridge BB1 Wiring Board v4',
      status: 'Top (Z) · F.Cu silkscreen, J5 5V module keep-out, JP1 1-2 AA / 2-3 5V module, D1/D2 1N5819 polarity'
    },
    bottom: {
      src: 'assets/pcb/view_bottom_3d.png',
      alt: 'KiCad 3D raytraced bottom view of BrailleBridge BB1 Wiring Board v4',
      status: 'Bottom (-Z) · B.Cu copper tracks, 1.00 mm V5_MOD & DIODE_IN power rails, 27 GND stitching vias'
    },
    esp32: {
      src: 'assets/pcb/view_esp32_3d.png',
      alt: 'KiCad 3D mechanical clearance render of ESP32 DevKit and Pololu S9V11F5 5V buck-boost module on BB1 Wiring Board v4',
      status: 'ESP32 + 5V Module Clearance · 38-pin DevKit on J2/J4 + Pololu S9V11F5 on J5 (16.55 mm keep-out clearance)'
    }
  };

  function initPcb3dGallery() {
    const img = document.getElementById('pcb3dRenderImg');
    const statusEl = document.getElementById('pcb3dStatus');
    const buttons = document.querySelectorAll('[data-pcb3d-angle]');
    if (!img || !buttons.length) return;

    // Preload all 4 KiCad 3D renders for instant switching
    Object.values(PCB_3D_VIEWS).forEach((v) => {
      const pre = new Image();
      pre.src = v.src;
    });

    buttons.forEach((btn) => {
      btn.addEventListener('click', () => {
        const key = btn.getAttribute('data-pcb3d-angle');
        const view = PCB_3D_VIEWS[key];
        if (!view) return;
        buttons.forEach((b) => {
          b.classList.toggle('active', b.getAttribute('data-pcb3d-angle') === key);
        });
        img.src = view.src;
        img.alt = view.alt;
        if (statusEl) statusEl.textContent = view.status;
      });
    });
  }

  function initPcb2dViewer() {
    const viewport = document.getElementById('pcb2dViewport');
    const stage = document.getElementById('pcb2dStage');
    const statusEl = document.getElementById('pcb2dStatus');
    const coordEl = document.getElementById('pcb2dCoord');
    if (!viewport || !stage) return;

    const layers = {
      all: document.getElementById('pcb2dImgAll'),
      fcu: document.getElementById('pcb2dImgFcu'),
      bcu: document.getElementById('pcb2dImgBcu'),
      silk: document.getElementById('pcb2dImgSilk')
    };

    const layerLabels = {
      all: 'All Layers',
      fcu: 'F.Cu (Top Copper)',
      bcu: 'B.Cu (Bottom Copper)',
      silk: 'Silkscreen & Edge.Cuts'
    };

    let activeLayer = 'all';
    let scale = 1;
    let panX = 0;
    let panY = 0;
    let dragging = false;
    let startX = 0;
    let startY = 0;

    function applyTransform() {
      stage.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
      if (statusEl) {
        statusEl.textContent = `Layer: ${layerLabels[activeLayer]} · Zoom: ${Math.round(scale * 100)}%`;
      }
    }

    const layerBtns = document.querySelectorAll('[data-pcb2d-layer]');
    layerBtns.forEach((btn) => {
      btn.addEventListener('click', () => {
        const mode = btn.getAttribute('data-pcb2d-layer');
        if (!layers[mode]) return;
        activeLayer = mode;
        layerBtns.forEach((b) => b.classList.toggle('active', b === btn));
        Object.entries(layers).forEach(([k, img]) => {
          if (img) img.hidden = k !== mode;
        });
        applyTransform();
      });
    });

    viewport.addEventListener('pointerdown', (e) => {
      dragging = true;
      startX = e.clientX - panX;
      startY = e.clientY - panY;
      viewport.setPointerCapture(e.pointerId);
    });

    viewport.addEventListener('pointermove', (e) => {
      if (coordEl) {
        const rect = viewport.getBoundingClientRect();
        const nx = (e.clientX - rect.left) / Math.max(rect.width, 1);
        const ny = (e.clientY - rect.top) / Math.max(rect.height, 1);
        coordEl.textContent = `X: ${(nx * 66.0).toFixed(2)} mm   Y: ${(ny * 52.0).toFixed(2)} mm`;
      }
      if (!dragging) return;
      panX = e.clientX - startX;
      panY = e.clientY - startY;
      applyTransform();
    });

    viewport.addEventListener('pointerup', (e) => {
      dragging = false;
      try { viewport.releasePointerCapture(e.pointerId); } catch (_) {}
    });

    viewport.addEventListener(
      'wheel',
      (e) => {
        if (!e.ctrlKey && !e.metaKey) return;
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.15 : 0.87;
        scale = Math.min(4.5, Math.max(0.65, scale * factor));
        applyTransform();
      },
      { passive: false }
    );

    document.getElementById('pcb2dZoomIn')?.addEventListener('click', () => {
      scale = Math.min(4.5, scale * 1.25);
      applyTransform();
    });

    document.getElementById('pcb2dZoomOut')?.addEventListener('click', () => {
      scale = Math.max(0.65, scale * 0.8);
      applyTransform();
    });

    document.getElementById('pcb2dReset')?.addEventListener('click', () => {
      scale = 1;
      panX = 0;
      panY = 0;
      applyTransform();
    });

    applyTransform();
  }

  initPcb3dGallery();
  initPcb2dViewer();
})();
