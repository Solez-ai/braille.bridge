import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const PART_SPECS = {
  board: {
    label: '66.0 × 41.0 × 1.2 mm · 2-layer FR-4 · 38 vias · 12 nets · 0 DRC/ERC errors',
    cam: [0.068, 0.056, 0.072],
    target: [0, 0, 0]
  },
  esp32: {
    label: 'J2 / J4 · Dual 1×19 2.54 mm female sockets (20.300 mm row spacing) for 38-pin ESP32',
    cam: [0.0, 0.058, 0.048],
    target: [-0.004, 0.006, -0.004]
  },
  switches: {
    label: 'J1 · 1×16 vertical male header (8× SIG+GND pairs: D1–D6, SPACE, SHIFT)',
    cam: [0.0, 0.044, 0.056],
    target: [-0.004, 0.005, 0.015]
  },
  power: {
    label: 'J3 · 1×4 power & switch header (BAT−, BAT+, BAT+>SW, SW BACK) · 1.00 mm power traces',
    cam: [0.048, 0.040, 0.046],
    target: [0.018, 0.004, 0.012]
  },
  diode: {
    label: 'D1 · 1N5819 40 V 1 A Schottky barrier diode (reverse-polarity / VIN protection)',
    cam: [0.042, 0.044, 0.036],
    target: [0.018, 0.004, 0.002]
  },
  mounts: {
    label: 'H1 / H2 · 2× M2 unplated mounting holes (2.2 mm drill, 5.0 mm copper keepout)',
    cam: [-0.056, 0.048, 0.044],
    target: [-0.025, 0.0, -0.012]
  }
};

function initPcb3dViewer() {
  const container = document.getElementById('pcb3dViewport');
  const loadingEl = document.getElementById('pcb3dLoading');
  const statusEl = document.getElementById('pcb3dStatus');
  if (!container) return;

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  } catch (err) {
    if (loadingEl) loadingEl.textContent = 'WebGL is unavailable in this browser.';
    return;
  }

  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.02;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0b1222);

  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.28;

  const hemi = new THREE.HemisphereLight(0xeef4ff, 0x091224, 0.35);
  scene.add(hemi);

  const keyLight = new THREE.DirectionalLight(0xfffaf0, 1.85);
  keyLight.position.set(0.08, 0.14, 0.09);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(1024, 1024);
  keyLight.shadow.camera.near = 0.01;
  keyLight.shadow.camera.far = 0.4;
  const d = 0.06;
  keyLight.shadow.camera.left = -d;
  keyLight.shadow.camera.right = d;
  keyLight.shadow.camera.top = d;
  keyLight.shadow.camera.bottom = -d;
  keyLight.shadow.bias = -0.0005;
  scene.add(keyLight);

  const fillLight = new THREE.DirectionalLight(0x9ec5ff, 0.55);
  fillLight.position.set(-0.10, 0.06, -0.08);
  scene.add(fillLight);

  const rimLight = new THREE.DirectionalLight(0xff9f5a, 0.38);
  rimLight.position.set(-0.06, 0.04, 0.12);
  scene.add(rimLight);

  const camera = new THREE.PerspectiveCamera(
    36,
    container.clientWidth / Math.max(container.clientHeight, 1),
    0.001,
    2.0
  );
  camera.position.set(...PART_SPECS.board.cam);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.07;
  controls.enablePan = true;
  controls.enableZoom = true;
  controls.minDistance = 0.032;
  controls.maxDistance = 0.28;
  controls.autoRotate = false;
  controls.autoRotateSpeed = 1.6;

  // Subtle dark engineering grid under the PCB
  const grid = new THREE.GridHelper(0.18, 18, 0x1e335c, 0x13203d);
  grid.position.y = -0.006;
  scene.add(grid);

  let boardRoot = null;
  let boardSize = new THREE.Vector3(0.066, 0.012, 0.041);
  let highlightedMesh = null;
  let highlightRestoreHex = null;
  let animGoal = null;

  const loader = new GLTFLoader();
  loader.load(
    'assets/pcb/bb1_wiring_board_v2.glb',
    (gltf) => {
      boardRoot = gltf.scene;

      // Center the PCB at origin
      const box = new THREE.Box3().setFromObject(boardRoot);
      const center = box.getCenter(new THREE.Vector3());
      boardSize = box.getSize(new THREE.Vector3());
      boardRoot.position.sub(center);

      // Enhance KiCad GLB materials for deep solder-mask green, crisp gold pads & real shadows
      boardRoot.traverse((obj) => {
        if (!obj.isMesh) return;
        obj.castShadow = true;
        obj.receiveShadow = true;
        const m = obj.material;
        if (!m) return;
        m.side = THREE.DoubleSide;
        const name = (m.name || '').toLowerCase();

        if (name === 'mat_9' || name === 'mat_10') {
          // Deep, rich emerald/bright PCB solder mask
          m.color.setHex(0x0a6b24);
          m.roughness = 0.28;
          m.metalness = 0.04;
          m.opacity = 0.90;
          m.transparent = true;
          m.envMapIntensity = 0.55;
        } else if (name === 'mat_11') {
          // FR-4 fiberglass core (dark olive-green so it doesn't bleach the mask)
          m.color.setHex(0x163818);
          m.roughness = 0.72;
          m.metalness = 0.0;
          m.envMapIntensity = 0.2;
        } else if (name === 'mat_6') {
          // ENIG gold pads & copper features
          m.color.setHex(0xd8b23c);
          m.metalness = 0.92;
          m.roughness = 0.24;
          m.envMapIntensity = 1.25;
        } else if (name === 'mat_1' || name === 'mat_3') {
          // Gold-plated header pins
          m.color.setHex(0xdfb646);
          m.metalness = 0.9;
          m.roughness = 0.22;
          m.envMapIntensity = 1.3;
        } else if (name === 'mat_0' || name === 'mat_2') {
          // Matte-satin black plastic header housings & diode body
          m.color.setHex(0x17191e);
          m.roughness = 0.42;
          m.metalness = 0.04;
          m.envMapIntensity = 0.5;
        } else if (name === 'mat_8') {
          // Crisp white silkscreen
          m.color.setHex(0xf4f6f8);
          m.roughness = 0.6;
          m.envMapIntensity = 0.25;
        }
        m.needsUpdate = true;
      });

      scene.add(boardRoot);
      grid.position.y = -(boardSize.y * 0.5) - 0.002;
      if (loadingEl) loadingEl.hidden = true;
    },
    undefined,
    () => {
      if (loadingEl) {
        loadingEl.textContent = 'Could not load 3D GLB model. Try refreshing the page.';
      }
    }
  );

  function animateCameraTo(pos, target) {
    animGoal = {
      pos: new THREE.Vector3(...pos),
      target: new THREE.Vector3(...target),
      progress: 0
    };
  }

  // Camera preset buttons
  const viewButtons = document.querySelectorAll('[data-pcb3d-view]');
  viewButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const mode = btn.getAttribute('data-pcb3d-view');
      viewButtons.forEach((b) => b.classList.toggle('active', b === btn));
      if (mode === 'iso' || mode === 'reset') {
        if (mode === 'reset') {
          controls.autoRotate = false;
          const autoBtn = document.getElementById('pcb3dAutoBtn');
          if (autoBtn) {
            autoBtn.classList.remove('active');
            autoBtn.setAttribute('aria-pressed', 'false');
          }
        }
        animateCameraTo(PART_SPECS.board.cam, PART_SPECS.board.target);
        if (statusEl) statusEl.textContent = PART_SPECS.board.label;
      } else if (mode === 'top') {
        animateCameraTo([0, 0.095, 0.001], [0, 0, 0]);
        if (statusEl) statusEl.textContent = 'Top view · F.Cu, ESP32 sockets (J2/J4), switch header (J1), D1';
      } else if (mode === 'bottom') {
        animateCameraTo([0, -0.095, 0.001], [0, 0, 0]);
        if (statusEl) statusEl.textContent = 'Bottom view · B.Cu ground pour, 34 GND stitching vias, solder joints';
      }
    });
  });

  // Auto-rotate toggle
  const autoBtn = document.getElementById('pcb3dAutoBtn');
  if (autoBtn) {
    autoBtn.addEventListener('click', () => {
      controls.autoRotate = !controls.autoRotate;
      autoBtn.classList.toggle('active', controls.autoRotate);
      autoBtn.setAttribute('aria-pressed', String(controls.autoRotate));
    });
  }

  // Zoom buttons
  const zoomBy = (factor) => {
    const offset = camera.position.clone().sub(controls.target);
    const nextLen = THREE.MathUtils.clamp(
      offset.length() * factor,
      controls.minDistance,
      controls.maxDistance
    );
    offset.setLength(nextLen);
    camera.position.copy(controls.target).add(offset);
  };
  document.getElementById('pcb3dZoomIn')?.addEventListener('click', () => zoomBy(0.8));
  document.getElementById('pcb3dZoomOut')?.addEventListener('click', () => zoomBy(1.25));

  // Component quick-inspect chips
  const chips = document.querySelectorAll('[data-pcb-part]');
  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      const key = chip.getAttribute('data-pcb-part');
      const spec = PART_SPECS[key];
      if (!spec) return;
      chips.forEach((c) => c.classList.toggle('active', c === chip));
      animateCameraTo(spec.cam, spec.target);
      if (statusEl) statusEl.textContent = spec.label;
    });
  });

  // Click-to-inspect raycasting on the 3D PCB
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let downPos = null;

  renderer.domElement.addEventListener('pointerdown', (e) => {
    downPos = { x: e.clientX, y: e.clientY };
    animGoal = null; // user took manual control
  });

  renderer.domElement.addEventListener('pointerup', (e) => {
    if (!downPos || !boardRoot) return;
    const dist = Math.hypot(e.clientX - downPos.x, e.clientY - downPos.y);
    downPos = null;
    if (dist > 5) return; // ignore drags

    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObject(boardRoot, true);
    if (!hits.length) return;

    const hit = hits[0];
    const mesh = hit.object;

    if (highlightedMesh && highlightedMesh.material && highlightedMesh.material.emissive && highlightRestoreHex !== null) {
      highlightedMesh.material.emissive.setHex(highlightRestoreHex);
    }

    if (mesh.material && mesh.material.emissive) {
      if (!mesh.userData.clonedMat) {
        mesh.material = mesh.material.clone();
        mesh.userData.clonedMat = true;
      }
      highlightRestoreHex = mesh.material.emissive.getHex();
      mesh.material.emissive.setHex(0xff7315);
      highlightedMesh = mesh;
      setTimeout(() => {
        if (highlightedMesh === mesh && mesh.material?.emissive) {
          mesh.material.emissive.setHex(highlightRestoreHex || 0x000000);
          highlightedMesh = null;
        }
      }, 900);
    }

    const xMm = ((hit.point.x + boardSize.x * 0.5) * 1000).toFixed(1);
    const yMm = ((hit.point.z + boardSize.z * 0.5) * 1000).toFixed(1);
    const rawName = (mesh.name || 'PCB Assembly').replace(/_/g, ' ');
    if (statusEl) {
      statusEl.textContent = `Inspected: ${rawName} · Board pos (${xMm} mm, ${yMm} mm)`;
    }
  });

  // ResizeObserver for responsive canvas
  const ro = new ResizeObserver(() => {
    const w = container.clientWidth;
    const h = Math.max(container.clientHeight, 1);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  });
  ro.observe(container);

  function tick() {
    requestAnimationFrame(tick);
    if (animGoal) {
      animGoal.progress += 0.08;
      camera.position.lerp(animGoal.pos, 0.14);
      controls.target.lerp(animGoal.target, 0.14);
      if (animGoal.progress >= 1.2) animGoal = null;
    }
    controls.update();
    renderer.render(scene, camera);
  }
  tick();
}

function initPcb2dViewer() {
  const viewport = document.getElementById('pcb2dViewport');
  const stage = document.getElementById('pcb2dStage');
  const statusEl = document.getElementById('pcb2dStatus');
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

  // Layer switch buttons
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

  // Drag to pan
  viewport.addEventListener('pointerdown', (e) => {
    dragging = true;
    startX = e.clientX - panX;
    startY = e.clientY - panY;
    viewport.setPointerCapture(e.pointerId);
  });

  viewport.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    panX = e.clientX - startX;
    panY = e.clientY - startY;
    applyTransform();
  });

  viewport.addEventListener('pointerup', (e) => {
    dragging = false;
    try { viewport.releasePointerCapture(e.pointerId); } catch (_) {}
  });

  // Ctrl+Wheel zoom (avoids trapping normal page scroll)
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

initPcb3dViewer();
initPcb2dViewer();
