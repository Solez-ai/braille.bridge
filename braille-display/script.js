/* ============================================================
   BrailleBridge — Educational Platform
   script.js
   ============================================================ */

/* ============================================================
   BRAILLE DICTIONARY
   ============================================================ */
const brailleDict = [
  { chord: 0b000001, english: 'a', bangla: '\u0985' },
  { chord: 0b000011, english: 'b', bangla: '\u09AC' },
  { chord: 0b001001, english: 'c', bangla: '\u099A' },
  { chord: 0b011001, english: 'd', bangla: '\u09A6' },
  { chord: 0b010001, english: 'e', bangla: '\u098F' },
  { chord: 0b001011, english: 'f', bangla: null },
  { chord: 0b011011, english: 'g', bangla: '\u0997' },
  { chord: 0b010011, english: 'h', bangla: '\u09B9' },
  { chord: 0b001000, english: 'i', bangla: '\u09CD' },
  { chord: 0b011010, english: 'j', bangla: '\u099C' },
  { chord: 0b000101, english: 'k', bangla: '\u0995' },
  { chord: 0b000111, english: 'l', bangla: '\u09B2' },
  { chord: 0b001101, english: 'm', bangla: '\u09AE' },
  { chord: 0b011101, english: 'n', bangla: '\u09A8' },
  { chord: 0b010101, english: 'o', bangla: '\u0993' },
  { chord: 0b001111, english: 'p', bangla: '\u09AA' },
  { chord: 0b011111, english: 'q', bangla: '\u0995\u09CD\u09B7' },
  { chord: 0b010111, english: 'r', bangla: '\u09B0' },
  { chord: 0b001100, english: 's', bangla: '\u0990' },
  { chord: 0b011100, english: 't', bangla: '\u0986' },
  { chord: 0b100101, english: 'u', bangla: '\u0989' },
  { chord: 0b100111, english: 'v', bangla: '\u09CB' },
  { chord: 0b111010, english: 'w', bangla: null },
  { chord: 0b101101, english: 'x', bangla: '\u09DF' },
  { chord: 0b111101, english: 'y', bangla: '\u09AF' },
  { chord: 0b110101, english: 'z', bangla: '\u09DC' },
  { chord: 0b001010, english: null, bangla: '\u0987' },
  { chord: 0b010010, english: null, bangla: '\u099E' },
  { chord: 0b001110, english: null, bangla: '\u09B8' },
  { chord: 0b111111, english: null, bangla: '\u09A2' },
  { chord: 0b100001, english: null, bangla: '\u099B' },
  { chord: 0b100011, english: null, bangla: '\u0998' },
  { chord: 0b011000, english: null, bangla: '\u09AD' },
  { chord: 0b111001, english: null, bangla: '\u09A5' },
  { chord: 0b110110, english: null, bangla: '\u09A0' },
  { chord: 0b101010, english: null, bangla: '\u0994' },
  { chord: 0b010110, english: null, bangla: '\u09AB' },
  { chord: 0b110100, english: null, bangla: '\u099D' },
  { chord: 0b101011, english: null, bangla: '\u09A1' },
  { chord: 0b010100, english: null, bangla: '\u0988' },
  { chord: 0b011110, english: null, bangla: '\u09A4' },
  { chord: 0b101000, english: null, bangla: '\u0996' },
  { chord: 0b101100, english: null, bangla: '\u0999' },
  { chord: 0b111110, english: null, bangla: '\u099F' },
  { chord: 0b101110, english: null, bangla: '\u09A7' },
  { chord: 0b111100, english: null, bangla: '\u09A3' },
  { chord: 0b110011, english: null, bangla: '\u098A' },
  { chord: 0b101111, english: null, bangla: '\u09B7' },
  { chord: 0b110001, english: null, bangla: '\u09B6' },
  { chord: 0b110000, english: null, bangla: '\u0982' },
  { chord: 0b010000, english: null, bangla: '\u0981' },
  { chord: 0b100110, english: null, bangla: '\u09BF' },
  { chord: 0b110010, english: null, bangla: '\u09C2' },
  { chord: 0b100010, english: null, bangla: '\u09B8' },
];

const numberChords = [0b000001,0b000011,0b001001,0b011001,0b010001,0b001011,0b011011,0b010011,0b001000,0b011010];
const numberMap = ['1','2','3','4','5','6','7','8','9','0'];

const shiftSymbols = [
  { chord: 0b010110, symbol: '+' }, { chord: 0b100100, symbol: '-' },
  { chord: 0b100110, symbol: '\u00D7' }, { chord: 0b110110, symbol: '=' },
  { chord: 0b001100, symbol: '\u00F7' }, { chord: 0b000010, symbol: ',' },
  { chord: 0b000110, symbol: ';' }, { chord: 0b010010, symbol: ':' },
  { chord: 0b110010, symbol: '.' },
];

const banglaShiftMap = [
  { chord: 0b000001, kar: null }, { chord: 0b011100, kar: '\u09BE' },
  { chord: 0b001010, kar: '\u09BF' }, { chord: 0b010100, kar: '\u09C0' },
  { chord: 0b100101, kar: '\u09C1' }, { chord: 0b110011, kar: '\u09C2' },
  { chord: 0b010001, kar: '\u09C7' }, { chord: 0b001100, kar: '\u09C8' },
  { chord: 0b010101, kar: '\u09CB' }, { chord: 0b101010, kar: '\u09CC' },
];

function lookupChord(chord, bangla) {
  for (const e of brailleDict) if (e.chord === chord) return bangla && e.bangla ? e.bangla : !bangla && e.english ? e.english : null;
  return null;
}
function lookupNumber(chord) { const i = numberChords.indexOf(chord); return i >= 0 ? numberMap[i] : null; }
function lookupShiftSymbol(chord) { for (const s of shiftSymbols) if (s.chord === chord) return s.symbol; return null; }
function lookupBanglaShift(chord) { for (const s of banglaShiftMap) if (s.chord === chord) return s.kar; return null; }

const charToChord = new Map();
for (const e of brailleDict) { if (e.english) charToChord.set(e.english, e.chord); if (e.bangla) charToChord.set(e.bangla, e.chord); }
for (let i = 0; i < 10; i++) charToChord.set(numberMap[i], numberChords[i]);
for (const s of shiftSymbols) charToChord.set(s.symbol, s.chord);
for (const s of banglaShiftMap) if (s.kar) charToChord.set(s.kar, s.chord);
for (const e of brailleDict) if (e.english && e.english.length === 1 && e.english >= 'a' && e.english <= 'z') charToChord.set(e.english.toUpperCase(), e.chord);

/* ============================================================
   UI STATE
   ============================================================ */
let isBangla = false;
let shiftActive = false;
let isConnected = false;
const dotBtns = [0,1,2,3,4,5].map(i => document.getElementById('dot'+(i+1)));
const liveText = document.getElementById('liveText');
const historyScroll = document.getElementById('historyScroll');
const chordMapping = document.getElementById('chordMapping');
const langIndicator = document.getElementById('langIndicator');
const shiftIndicator = document.getElementById('shiftIndicator');
const statusDot = document.getElementById('statusDot');
const statusLabel = document.getElementById('statusLabel');
let historyChars = [];

let dotAnimationTimer = null;
function animateDotsForChar(char) {
  if (char === ' ') return;
  const chord = charToChord.get(char);
  if (chord === undefined) return;
  if (dotAnimationTimer) clearTimeout(dotAnimationTimer);
  dotBtns.forEach(b => b.classList.remove('active', 'pulse'));
  for (let i = 0; i < 6; i++) if (chord & (1 << i)) dotBtns[i].classList.add('active', 'pulse');
  const cv = document.querySelector('.chord-value');
  const cm = document.getElementById('chordMapping');
  const bin = chord.toString(2).padStart(6, '0');
  const dots = []; for (let i = 0; i < 6; i++) if (chord & (1 << i)) dots.push(i + 1);
  cv.innerHTML = `<i class="fa-regular fa-circle-dot" style="margin-right:4px;"></i> Chord 0b${bin} &mdash; Dots ${dots.join(',')}`;
  cm.innerHTML = `Received: <strong>${char}</strong>`;
  dotAnimationTimer = setTimeout(() => {
    dotBtns.forEach(b => b.classList.remove('active', 'pulse'));
    const v = document.querySelector('.chord-value');
    if (v) v.innerHTML = '<i class="fa-regular fa-hand-pointer" style="margin-right:4px;"></i> Click dots to compose a chord';
    const m = document.getElementById('chordMapping');
    if (m) m.textContent = '';
    dotAnimationTimer = null;
  }, 450);
}

dotBtns.forEach(btn => { btn.addEventListener('mousedown', e => { e.preventDefault(); btn.classList.toggle('active'); updateChordDisplay(); }); });

function getActiveChord() { let c = 0; for (let i = 0; i < 6; i++) if (dotBtns[i].classList.contains('active')) c |= (1 << i); return c; }

function updateChordDisplay() {
  const chord = getActiveChord();
  const cv = document.querySelector('.chord-value');
  const cm = document.getElementById('chordMapping');
  if (chord === 0) { cv.innerHTML = '<i class="fa-regular fa-hand-pointer" style="margin-right:4px;"></i> Click dots to compose a chord'; cm.textContent = ''; return; }
  const bin = chord.toString(2).padStart(6, '0');
  const dots = []; for (let i = 0; i < 6; i++) if (chord & (1 << i)) dots.push(i + 1);
  cv.innerHTML = `<i class="fa-regular fa-circle-dot" style="margin-right:4px;"></i> Chord 0b${bin} &mdash; Dots ${dots.join(',')}`;
  const en = lookupChord(chord, false), bn = lookupChord(chord, true);
  const sym = lookupShiftSymbol(chord), num = lookupNumber(chord), bnShift = lookupBanglaShift(chord);
  let parts = [];
  if (sym) parts.push(`<strong>${sym}</strong> <span style="font-size:10px;opacity:0.6;">math</span>`);
  if (num !== null) parts.push(`<strong>${num}</strong> <span style="font-size:10px;opacity:0.6;">number</span>`);
  if (en && !sym && num === null) parts.push(`English: <strong>${en}</strong>`);
  if (bn) parts.push(`\u09AC\u09BE\u0982\u09B2\u09BE: <strong>${bn}</strong>`);
  if (bnShift && !sym) parts.push(`Shift: <strong>${bnShift}</strong>`);
  if (parts.length === 0 && en === null && bn === null) cm.textContent = '(no mapping)';
  else cm.innerHTML = parts.join(' &nbsp;\u00B7&nbsp; ');
}

function resetDots() { dotBtns.forEach(b => b.classList.remove('active')); updateChordDisplay(); }

function updateIndicators() {
  langIndicator.innerHTML = `<i class="fa-solid fa-language"></i> ${isBangla ? '\u09AC\u09BE\u0982\u09B2\u09BE' : 'English'}`;
  langIndicator.className = 'indicator ' + (isBangla ? 'bangla' : 'english');
  shiftIndicator.innerHTML = `<i class="fa-solid fa-up-long"></i> ${shiftActive ? 'Shift ON' : 'Shift'}`;
  shiftIndicator.className = 'indicator ' + (shiftActive ? 'shift-on' : 'shift-off');
}

function appendChar(char, targetElement) {
  const target = targetElement || liveText;
  const ph = target.querySelector('.placeholder'); if (ph) ph.remove();
  const oc = target.querySelector('.cursor-blink'); if (oc) oc.remove();
  if (target === liveText) target.classList.add('has-content');

  if (char === ' ') {
    const sp = document.createElement('span'); sp.textContent = ' '; sp.style.display = 'inline-block'; sp.style.width = '0.35em'; sp.className = 'live-char'; target.appendChild(sp);
  } else {
    const span = document.createElement('span'); span.textContent = char; span.className = 'live-char';
    if (/[\u0980-\u09FF]/.test(char)) span.style.fontFamily = 'var(--font-bangla)';
    target.appendChild(span);
  }
  const cursor = document.createElement('span'); cursor.className = 'cursor-blink'; target.appendChild(cursor);
  target.scrollTop = target.scrollHeight;
  if (target === liveText) addToHistory(char);
}

function addToHistory(char) {
  if (char === ' ') {
    const s = document.createElement('span'); s.className = 'history-char space-char'; historyScroll.appendChild(s);
  } else if (/[\u0980-\u09FF]/.test(char)) {
    const s = document.createElement('span'); s.className = 'history-char'; s.textContent = char; s.style.fontFamily = 'var(--font-bangla)'; historyScroll.appendChild(s);
  } else if (/[+\-\u00D7\u00F7=,;:.]/.test(char)) {
    const s = document.createElement('span'); s.className = 'history-char special'; s.textContent = char; historyScroll.appendChild(s);
  } else {
    const s = document.createElement('span'); s.className = 'history-char'; s.textContent = char; historyScroll.appendChild(s);
  }
  const init = historyScroll.querySelector('[data-placeholder]'); if (init) init.remove();
  historyChars.push(char);
  while (historyChars.length > 80) { historyChars.shift(); if (historyScroll.firstChild) historyScroll.firstChild.remove(); }
  historyScroll.scrollTop = historyScroll.scrollHeight;
}

function clearDisplay() {
  liveText.innerHTML = '<span class="placeholder"><i class="fa-solid fa-braille" style="margin-right:6px;"></i> Braille output will appear here</span><span class="cursor-blink"></span>';
  liveText.classList.remove('has-content');
  historyScroll.innerHTML = '<span data-placeholder style="color:var(--text-muted);font-size:12px;"><i class="fa-regular fa-rectangle-list" style="margin-right:4px;"></i> No characters yet</span>';
  historyChars = []; resetDots();
}

document.addEventListener('keydown', (e) => {
  const n = parseInt(e.key);
  if (n >= 1 && n <= 6) { if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return; e.preventDefault(); dotBtns[n-1].classList.toggle('active'); updateChordDisplay(); return; }
  if (e.key === ' ' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'SELECT') { e.preventDefault(); appendChar(' '); return; }
  if (e.key === 'Enter' && !e.shiftKey && e.target.tagName !== 'INPUT') {
    const chord = getActiveChord(); if (chord > 0) {
      let ch = null;
      if (shiftActive) { ch = lookupNumber(chord) || lookupShiftSymbol(chord); if (!ch && !isBangla) { const b = lookupChord(chord, false); if (b && b >= 'a' && b <= 'z') ch = b.toUpperCase(); } if (!ch && isBangla) { ch = lookupBanglaShift(chord) || lookupChord(chord, true); } shiftActive = false; updateIndicators(); }
      else ch = lookupChord(chord, isBangla);
      if (ch) appendChar(ch); resetDots();
    } return;
  }
  if ((e.key === 'l' || e.key === 'L') && !e.ctrlKey && !e.metaKey) { if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return; isBangla = !isBangla; updateIndicators(); return; }
  if ((e.key === 's' || e.key === 'S') && !e.ctrlKey && !e.metaKey) { if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return; shiftActive = !shiftActive; updateIndicators(); return; }
  if (e.key === 'Backspace' && e.target.tagName !== 'INPUT') {
    if (liveText.querySelector('.placeholder')) return;
    for (let i = liveText.children.length - 1; i >= 0; i--) { if (!liveText.children[i].classList.contains('cursor-blink')) { liveText.children[i].remove(); break; } }
    if (historyChars.length > 0) { historyChars.pop(); if (historyScroll.lastChild) historyScroll.lastChild.remove(); }
  }
});

/* ============================================================
   DESKTOP RELAY TRANSPORT (pywebview)
   When running inside braille-desktop (Python + pywebview), the Python relay
   owns the COM ports. The UI connects through window.pywebview.api and Python
   pushes serial data in via the __relayOn* callbacks below. In a plain
   browser, RELAY stays false and the original Web Serial path is used.
   ============================================================ */
let RELAY = false;
let relayApi = null;
let relayStudentPort = null;          // student-view port currently open via relay
const relayFeeds = new Map();         // port -> feed (student view)
const relayStudentFeeds = new Map();  // port -> feed (teacher-mode student)
let relayAssignments = {};            // student name -> port (persisted by Python)
let currentPorts = [];

// ESP32 ROM boot preamble — printed on serial every reset BEFORE the
// firmware runs (e.g. 'ets Jul 29 2019 12:21:46', 'rst:0x1 ...', 'entry 0x...').
// It is not user text; the filters below drop it so it never pollutes the
// live output. Mirrors the suppression in braille-desktop/relay.py.
const BOOT_PREFIXES = ['ets ', 'rst:0x', 'boot:0x', 'configSPIWP', 'clk_drv:',
                       'q_drv:', 'd_drv:', 'cs0_drv:', 'hd_drv:', 'wp_drv:',
                       'mode:DIO', 'load:0x', 'entry 0x'];

function isBootLine(line) { return BOOT_PREFIXES.some(p => line.startsWith(p)); }

// Stateful suppressor: once 'ets ' is seen (chip boot starts), everything is
// dropped until 'entry 0x' or the firmware's own 'SYSTEM:' banner appears.
function makeBootFilter() {
  let suppress = false;
  return {
    dropLine(line) {
      if (line.startsWith('ets ')) { suppress = true; return true; }
      if (suppress) {
        if (line.startsWith('entry 0x') || line.startsWith('SYSTEM:')) suppress = false;
        else return true;
      }
      return isBootLine(line);
    },
    dropChunk(chunk) {
      if (chunk.startsWith('ets ')) { suppress = true; return true; }
      return suppress || isBootLine(chunk);
    }
  };
}

// Chunk -> line splitter that mirrors the original readLoop buffering:
// complete newline-terminated lines go to onLine(), trailing partial chunks
// are treated as immediate characters (firmware prints chars without \n).
function makeSerialFeed(onLine, onChars) {
  let buffer = '';
  const boot = makeBootFilter();
  return function feed(chunk) {
    buffer += chunk;
    let nl = buffer.indexOf('\n');
    while (nl >= 0) {
      const line = buffer.slice(0, nl).trim();
      buffer = buffer.slice(nl + 1);
      if (line && !boot.dropLine(line)) onLine(line);
      nl = buffer.indexOf('\n');
    }
    if (buffer.length > 0) {
      const rest = buffer;
      buffer = '';
      if (!boot.dropChunk(rest)) onChars(rest);
    }
  };
}

// --- Shared line handlers (used by BOTH the Web Serial and relay paths) ---
function handleLineForStudentView(line) {
  if (line.startsWith('SYSTEM:')) { if (line === 'SYSTEM:BKSP') handleBackspace(); return; }
  if (line === 'LANG:en') { isBangla = false; updateIndicators(); return; }
  if (line === 'LANG:bn') { isBangla = true; updateIndicators(); return; }
  if (line === 'Invalid' || line === 'SHIFT') return;
  handleCharsForStudentView(line);
}
function handleCharsForStudentView(chunk) {
  for (const ch of chunk) if (ch !== '\r') handleIncomingChar(ch);
}
function handleLineForTeacherStudent(student, line) {
  if (line.startsWith('SYSTEM:')) { if (line === 'SYSTEM:BKSP') handleStudentBackspace(student); return; }
  if (line === 'Invalid' || line === 'SHIFT' || line.startsWith('LANG:')) return;
  handleCharsForTeacherStudent(student, line);
}
function handleCharsForTeacherStudent(student, chunk) {
  for (const ch of chunk) if (ch !== '\r') handleStudentChar(student, ch);
}

// --- Callbacks invoked by the Python relay (main.py) ---
window.__relayOnData = (portName, chunk) => {
  const sf = relayFeeds.get(portName);
  if (sf) { sf(chunk); return; }
  const tf = relayStudentFeeds.get(portName);
  if (tf) tf(chunk);
};

window.__relayOnEvent = (portName, event) => {
  if (portName === relayStudentPort) {
    if (event === 'close') {
      updateSerialUI(false);
      serialInfo.innerHTML = '<i class="fa-solid fa-plug" style="margin-right:4px;"></i> Device disconnected — waiting for it to return&hellip;';
    } else if (event === 'reconnect') {
      updateSerialUI(true);
      serialInfo.innerHTML = '<i class="fa-regular fa-circle-check text-green" style="margin-right:4px;"></i> Reconnected automatically by the relay.';
    }
  }
  for (const s of students) {
    if (s.portName && s.portName === portName) {
      if (event === 'close' && s.connected) { s.connected = false; renderRoster(); renderFeedGrid(); }
      if (event === 'reconnect' && !s.connected) { s.connected = true; renderRoster(); renderFeedGrid(); }
    }
  }
};

window.__relayOnPorts = (ports) => { currentPorts = ports || []; populatePortSelects(); };

function populatePortSelects() {
  const sel = document.getElementById('relayPortSelect');
  const sel2 = document.getElementById('studentPortInput');
  if (!sel || !sel2) return;
  const keep1 = sel.value, keep2 = sel2.value;
  sel.innerHTML = ''; sel2.innerHTML = '';
  if (!currentPorts.length) {
    const o = document.createElement('option'); o.value = ''; o.textContent = '(no ports detected)'; sel.appendChild(o);
    const o2 = document.createElement('option'); o2.value = ''; o2.textContent = '(no ports detected)'; sel2.appendChild(o2);
  } else {
    for (const p of currentPorts) {
      const o = document.createElement('option'); o.value = p.name; o.textContent = `${p.name} — ${p.description}`; sel.appendChild(o);
      const o2 = document.createElement('option'); o2.value = p.name; o2.textContent = p.name; sel2.appendChild(o2);
    }
  }
  if (keep1 && [...sel.options].some(o => o.value === keep1)) sel.value = keep1;
  if (keep2 && [...sel2.options].some(o => o.value === keep2)) sel2.value = keep2;
}

let relayToastTimer = null;
function showToast(msg) {
  let t = document.getElementById('relayToast');
  if (!t) { t = document.createElement('div'); t.id = 'relayToast'; t.className = 'relay-toast'; document.body.appendChild(t); }
  t.textContent = msg;
  t.classList.add('visible');
  clearTimeout(relayToastTimer);
  relayToastTimer = setTimeout(() => t.classList.remove('visible'), 3200);
}

function initRelayUI() {
  document.getElementById('relayChip').style.display = 'inline-flex';
  document.getElementById('relayPortRow').style.display = 'flex';
  document.getElementById('studentPortRow').style.display = 'flex';
  const saveBtn = document.getElementById('btnSaveLogs');
  saveBtn.style.display = 'inline-flex';
  saveBtn.onclick = async () => {
    try { showToast(await relayApi.save_all_logs()); } catch (e) { showToast('Save failed: ' + e.message); }
  };
  relayApi.get_assignments().then(a => { relayAssignments = a || {}; });
  relayApi.list_ports().then(ports => { currentPorts = ports || []; populatePortSelects(); });
}

window.addEventListener('pywebviewready', () => {
  if (window.pywebview && window.pywebview.api) {
    RELAY = true;
    relayApi = window.pywebview.api;
    initRelayUI();
  }
});

/* ============================================================
   SERIAL (Student View)
   ============================================================ */
let port = null, reader = null;
const btnConnect = document.getElementById('btnConnect');
const btnIcon = document.getElementById('btnIcon');
const btnText = document.getElementById('btnText');
const serialInfo = document.getElementById('serialInfo');
const baudSelect = document.getElementById('baudSelect');

document.getElementById('btnClear').addEventListener('click', clearDisplay);
// In relay mode the Web Serial `port` stays null, so the toggle must also
// check relayStudentPort — otherwise Disconnect silently re-opens instead.
btnConnect.addEventListener('click', async () => { if (port || relayStudentPort) { await disconnectSerial(); return; } await connectSerial(); });

async function connectSerial() {
  if (RELAY) return connectSerialRelay();
  try {
    serialInfo.innerHTML = '<i class="fa-solid fa-magnifying-glass" style="margin-right:4px;"></i> Select <span class="highlight">COM6</span> from the browser dialog&hellip;';
    port = await navigator.serial.requestPort();
    const baudRate = parseInt(baudSelect.value);
    serialInfo.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="margin-right:4px;"></i> Opening <span class="highlight">${baudRate}</span> baud&hellip;`;
    let openSuccess = false, lastError = null;
    for (let attempt = 0; attempt < 3; attempt++) {
      try { await port.open({ baudRate }); openSuccess = true; break; }
      catch (err) { lastError = err; if (attempt < 2) { serialInfo.innerHTML = `<i class="fa-solid fa-rotate fa-spin" style="margin-right:4px;"></i> Retrying (attempt ${attempt+2}/3)&hellip;`; await new Promise(r => setTimeout(r, 800)); } }
    }
    if (!openSuccess) throw lastError || new Error('Failed to open port after retries');
    updateSerialUI(true);
    serialInfo.innerHTML = `<i class="fa-regular fa-circle-check text-green" style="margin-right:4px;"></i> Connected to <span class="highlight">ESP32</span><br>Baud: <span class="highlight">${baudRate}</span> | Reading live&hellip;`;
    readLoop();
  } catch (err) {
    if (err.name === 'NotFoundError') serialInfo.innerHTML = '<i class="fa-solid fa-triangle-exclamation" style="color:var(--accent-red);margin-right:4px;"></i> No port selected. Click <b>Connect</b> to try again.';
    else serialInfo.innerHTML = getTroubleshootingHTML(err.message);
    if (port) { try { await port.close(); } catch(e) {} port = null; }
  }
}

async function connectSerialRelay() {
  const sel = document.getElementById('relayPortSelect');
  const portName = sel ? sel.value : '';
  if (!portName) {
    serialInfo.innerHTML = '<i class="fa-solid fa-triangle-exclamation" style="color:var(--accent-red);margin-right:4px;"></i> No COM port selected. Pick one above, then connect.';
    return;
  }
  const baudRate = parseInt(baudSelect.value);
  serialInfo.innerHTML = `<i class="fa-solid fa-spinner fa-spin" style="margin-right:4px;"></i> Opening <span class="highlight">${portName}</span> via desktop relay&hellip;`;
  const ok = await relayApi.open_port(portName, baudRate);
  if (!ok) {
    serialInfo.innerHTML = getTroubleshootingHTML('The relay could not open ' + portName);
    return;
  }
  relayStudentPort = portName;
  relayFeeds.set(portName, makeSerialFeed(handleLineForStudentView, handleCharsForStudentView));
  updateSerialUI(true);
  serialInfo.innerHTML = `<i class="fa-regular fa-circle-check text-green" style="margin-right:4px;"></i> Connected to <span class="highlight">${portName}</span> (relay)<br>Baud: <span class="highlight">${baudRate}</span> | Reading live&hellip;`;
}

async function disconnectSerial() {
  if (RELAY) {
    if (relayStudentPort) {
      await relayApi.close_port(relayStudentPort);
      relayFeeds.delete(relayStudentPort);
      relayStudentPort = null;
    }
    updateSerialUI(false);
    serialInfo.innerHTML = '<i class="fa-solid fa-plug" style="margin-right:4px;"></i> Disconnected.';
    return;
  }
  if (reader) { await reader.cancel(); reader = null; }
  if (port) { try { await port.close(); } catch(e) {} port = null; }
  updateSerialUI(false);
  serialInfo.innerHTML = '<i class="fa-solid fa-plug" style="margin-right:4px;"></i> Disconnected.';
}

function updateSerialUI(connected) {
  isConnected = connected;
  btnConnect.classList.toggle('connected', connected);
  btnIcon.className = connected ? 'fa-solid fa-plug' : 'fa-solid fa-bolt';
  btnText.textContent = connected ? 'Disconnect' : 'Connect to COM6';
  statusDot.className = 'status-dot ' + (connected ? 'connected' : 'disconnected');
  statusLabel.textContent = connected ? 'Connected' : 'Disconnected';
  baudSelect.disabled = connected;
  const sendBtn = document.getElementById('btnSendToTeacher');
  if (sendBtn) sendBtn.style.display = connected ? 'flex' : 'none';
  // Keep any mirrored teacher student in sync with the live connection state
  if (connected) setMirrorOnline(); else setMirrorOffline();
}

/* ============================================================
   SEND TO TEACHER (mirror the student-view connection into the
   teacher roster — one connection, two views)
   ============================================================ */
let mirrorStudentId = null;

function openSendModal() {
  document.getElementById('sendBaudInput').value = baudSelect.value;
  document.getElementById('sendNameInput').value = '';
  document.getElementById('sendModal').classList.add('visible');
  document.body.style.overflow = 'hidden';
  setTimeout(() => document.getElementById('sendNameInput').focus(), 50);
}
function closeSendModal() {
  document.getElementById('sendModal').classList.remove('visible');
  document.body.style.overflow = '';
}

function confirmSendToTeacher() {
  const name = document.getElementById('sendNameInput').value.trim();
  if (!name) {
    const inp = document.getElementById('sendNameInput');
    inp.focus(); inp.style.borderColor = 'var(--accent-red)';
    setTimeout(() => inp.style.borderColor = '', 1500);
    return;
  }
  if (mirrorStudentId !== null && students.find(s => s.id === mirrorStudentId)) {
    showToast('This device is already mirrored to the teacher roster.');
    closeSendModal();
    return;
  }
  const connType = document.getElementById('sendConnInput').value;
  const baud = parseInt(document.getElementById('sendBaudInput').value);
  const student = addStudent(name, connType, baud, null, true);
  student.connected = true;
  mirrorStudentId = student.id;
  renderRoster(); renderFeedGrid();
  closeSendModal();
  showToast(`"${name}" added to Teacher Mode — switch to the Teacher view to watch.`);
  setMode('teacher');
  const card = document.getElementById(`feed-${student.id}`);
  if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function setMirrorOnline() {
  if (mirrorStudentId === null) return;
  const ms = students.find(s => s.id === mirrorStudentId);
  if (ms && !ms.connected) { ms.connected = true; renderRoster(); renderFeedGrid(); }
}
function setMirrorOffline() {
  if (mirrorStudentId === null) return;
  const ms = students.find(s => s.id === mirrorStudentId);
  if (ms && ms.connected) { ms.connected = false; renderRoster(); renderFeedGrid(); }
}

document.getElementById('btnSendToTeacher').addEventListener('click', () => {
  if (!isConnected) { showToast('Connect the device first, then send it to the teacher.'); return; }
  openSendModal();
});
document.getElementById('sendConfirmBtn').addEventListener('click', confirmSendToTeacher);
document.getElementById('sendCancelBtn').addEventListener('click', closeSendModal);
document.getElementById('sendModalClose').addEventListener('click', closeSendModal);
document.getElementById('sendModal').addEventListener('click', e => { if (e.target === e.currentTarget) closeSendModal(); });
document.getElementById('sendNameInput').addEventListener('keydown', e => { if (e.key === 'Enter') confirmSendToTeacher(); });
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && document.getElementById('sendModal').classList.contains('visible')) closeSendModal();
});

function getTroubleshootingHTML(msg) {
  if (msg.includes('open') || msg.includes('serial port')) {
    return '<i class="fa-solid fa-circle-xmark" style="color:var(--accent-red);margin-right:4px;"></i> <b style="color:var(--accent-red);">COM6 might be in use!</b><br>&rarr; Close the <b>Arduino IDE Serial Monitor</b><br>&rarr; Press RESET on the ESP32<br>&rarr; Unplug and re-plug the USB';
  }
  return '<i class="fa-solid fa-circle-xmark" style="color:var(--accent-red);margin-right:4px;"></i> <b>Connection failed:</b><br><span style="font-size:10px;">'+msg+'</span>';
}

async function readLoop() {
  const decoder = new TextDecoder();
  const feed = makeSerialFeed(handleLineForStudentView, handleCharsForStudentView);
  try {
    while (port && port.readable) {
      reader = port.readable.getReader();
      try {
        while (true) {
          const { value, done } = await reader.read(); if (done) break;
          feed(decoder.decode(value, { stream: true }));
        }
      } finally { reader.releaseLock(); reader = null; }
    }
  } catch (err) { if (err.name !== 'CancelError') serialInfo.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="color:var(--accent-red);margin-right:4px;"></i> Read error: ${err.message}`; }
  if (port) await disconnectSerial();
}

function handleIncomingChar(ch) {
  if (/[\u0980-\u09FF]/.test(ch)) { if (!isBangla) { isBangla = true; updateIndicators(); } }
  else if (/[a-zA-Z]/.test(ch)) { if (isBangla) { isBangla = false; updateIndicators(); } }
  appendChar(ch); animateDotsForChar(ch);
  // Mirror to the teacher roster while "Send to Teacher" is active. Wrapped so
  // a rendering hiccup on one character can never cascade into the teacher UI.
  if (mirrorStudentId !== null) {
    try {
      const ms = students.find(s => s.id === mirrorStudentId);
      if (ms) handleStudentChar(ms, ch);
    } catch (err) { console.error('Mirror char failed:', err); }
  }
}

// Remove the last character from the student view's live display (triggered by SYSTEM:BKSP)
function handleBackspace() {
  if (liveText.querySelector('.placeholder')) return;
  // Remove the last non-cursor child from liveText
  for (let i = liveText.children.length - 1; i >= 0; i--) {
    if (!liveText.children[i].classList.contains('cursor-blink')) {
      liveText.children[i].remove();
      break;
    }
  }
  // Remove the last char from history
  if (historyChars.length > 0) {
    historyChars.pop();
    if (historyScroll.lastChild) historyScroll.lastChild.remove();
  }
  // If display is now empty, restore placeholder
  if (liveText.children.length <= 1) {
    liveText.classList.remove('has-content');
    liveText.innerHTML = '<span class="placeholder"><i class="fa-solid fa-braille" style="margin-right:6px;"></i> Braille output will appear here</span><span class="cursor-blink"></span>';
  }
  // Keep the mirrored teacher student in sync with the correction
  if (mirrorStudentId !== null) {
    const ms = students.find(s => s.id === mirrorStudentId);
    if (ms) handleStudentBackspace(ms);
  }
}

/* ============================================================
   TEACHER MODE — Multi-Port Serial
   ============================================================ */
const STUDENT_COLORS = ['#5a8ae0','#d45a5a','#5ab85a','#c49a4a','#8a6ad4','#4ac8b8','#e08a5a','#5ab8b8'];
let students = [], studentIdCounter = 0, totalCharsAllStudents = 0;

function getColorForIndex(i) { return STUDENT_COLORS[i % STUDENT_COLORS.length]; }
function getInitials(name) { return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2); }

function setMode(mode) {
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  const app = document.getElementById('app');
  app.classList.remove('mode-teacher', 'mode-exam');
  if (mode === 'student') {
    document.getElementById('modeStudent').classList.add('active');
  } else if (mode === 'teacher') {
    document.getElementById('modeTeacher').classList.add('active');
    app.classList.add('mode-teacher');
  } else if (mode === 'exam') {
    document.getElementById('modeExam').classList.add('active');
    app.classList.add('mode-exam');
    renderExamGrid();
    updateExamStats();
  }
}
document.getElementById('modeStudent').addEventListener('click', () => setMode('student'));
document.getElementById('modeTeacher').addEventListener('click', () => setMode('teacher'));
document.getElementById('modeExam').addEventListener('click', () => setMode('exam'));

document.getElementById('btnAddStudent').addEventListener('click', () => {
  document.getElementById('addStudentForm').classList.toggle('visible');
  if (document.getElementById('addStudentForm').classList.contains('visible')) document.getElementById('studentNameInput').focus();
});
document.getElementById('btnCancelAdd').addEventListener('click', () => {
  document.getElementById('addStudentForm').classList.remove('visible');
  document.getElementById('studentNameInput').value = '';
});
document.getElementById('btnConfirmAdd').addEventListener('click', () => {
  const name = document.getElementById('studentNameInput').value.trim();
  const connType = document.getElementById('studentConnInput').value;
  const baud = parseInt(document.getElementById('studentBaudInput').value);
  const portName = RELAY ? document.getElementById('studentPortInput').value : '';
  if (!name) { document.getElementById('studentNameInput').focus(); document.getElementById('studentNameInput').style.borderColor = 'var(--accent-red)'; setTimeout(() => document.getElementById('studentNameInput').style.borderColor = '', 1500); return; }
  addStudent(name, connType, baud, portName);
  if (RELAY && portName) { relayAssignments[name] = portName; relayApi.set_assignment(name, portName); }
  document.getElementById('studentNameInput').value = '';
  document.getElementById('addStudentForm').classList.remove('visible');
});
document.getElementById('studentNameInput').addEventListener('keydown', e => { if (e.key === 'Enter') document.getElementById('btnConfirmAdd').click(); });

function addStudent(name, connType, baud, portName, mirror) {
  const id = studentIdCounter++;
  const student = { id, name, connType, baud, color: getColorForIndex(students.length), chars: [], connected: false, serialPort: null, serialReader: null, readLoopActive: false, portName: portName || null, mirror: !!mirror };
  students.push(student);
  renderRoster(); renderFeedGrid(); updateStudentStats();
  return student;
}

function removeStudent(id) {
  if (expandStudentId === id) closeExpandView();
  if (mirrorStudentId === id) mirrorStudentId = null;
  const s = students.find(st => st.id === id);
  if (s) { disconnectStudentSerial(s, true); totalCharsAllStudents -= s.chars.length; if (RELAY && relayAssignments[s.name]) { delete relayAssignments[s.name]; relayApi.set_assignment(s.name, ''); } }
  students = students.filter(st => st.id !== id);
  renderRoster(); renderFeedGrid(); updateStudentStats();
}

function clearStudentFeed(id) {
  const s = students.find(st => st.id === id);
  if (s) {
    totalCharsAllStudents -= s.chars.length;
    s.chars = [];
    updateStudentFeed(s);
    rebuildExamFeed(s);
    if (expandStudentId === s.id) updateExpandView();
    updateStudentStats();
  }
}

function clearAllFeeds() {
  for (const s of students) {
    totalCharsAllStudents -= s.chars.length;
    s.chars = [];
    updateStudentFeed(s);
    rebuildExamFeed(s);
  }
  if (expandStudentId !== null) updateExpandView();
  updateStudentStats();
  updateExamStats();
}

/* -- Export -- */
function formatCharTimestamp(ts) {
  const d = new Date(ts);
  return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// Group characters into readable wrapped lines. Each line is prefixed with the
// timestamp of the first character typed on it, so the log reads like prose
// instead of one character per line.
function buildReadableLog(chars) {
  const lines = [];
  let words = [], lineLen = 0, cur = '', curTime = null;
  // Keep wrapped lines under ~64 chars even after the [HH:MM:SS] prefix is added.
  const MAX_LINE = 52;

  const flushWord = () => {
    if (cur === '') return;
    const add = cur.length + (words.length ? 1 : 0);
    if (lineLen + add > MAX_LINE) flushLine();
    words.push({ text: cur, time: curTime });
    lineLen += add;
    cur = ''; curTime = null;
  };
  const flushLine = () => {
    if (!words.length) return;
    lines.push({ time: words[0].time, text: words.map(w => w.text).join(' ') });
    words = []; lineLen = 0;
  };

  for (const entry of chars) {
    const isObj = entry && typeof entry === 'object';
    const ch = isObj ? entry.char : entry;
    if (ch === ' ') { flushWord(); continue; }
    if (ch === '\n' || ch === '\r') { flushWord(); flushLine(); continue; }
    if (cur === '') curTime = (isObj && entry.time) || Date.now();
    cur += ch;
  }
  flushWord(); flushLine();
  return lines;
}

function formatReadableLine(line) {
  return `[${formatCharTimestamp(line.time)}] ${line.text}`;
}

function exportStudentLog(student) {
  const header = [
    'BrailleBridge Student Log',
    '=======================',
    `Student: ${student.name}`,
    `Connection: ${student.connType.toUpperCase()} @ ${student.baud} baud`,
    `Exported: ${new Date().toLocaleString()}`,
    `Characters: ${student.chars.length}`,
    '=======================',
    ''
  ].join('\n');

  const body = buildReadableLog(student.chars).map(formatReadableLine).join('\n');
  const footer = '\n=======================\nEnd of log.';
  const content = header + body + footer;

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${student.name.replace(/\s+/g, '_')}_braille_log.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function exportAllLogs() {
  if (students.length === 0) return;
  if (students.length === 1) { exportStudentLog(students[0]); return; }

  const parts = [];
  for (const s of students) {
    parts.push(
      `*** ${s.name} ***`,
      `Connection: ${s.connType.toUpperCase()} @ ${s.baud} baud`,
      `Chars: ${s.chars.length}`,
      '---',
      buildReadableLog(s.chars).map(formatReadableLine).join('\n')
    );
  }
  const content = [
    'BrailleBridge — Class Export',
    '=======================',
    `Exported: ${new Date().toLocaleString()}`,
    `Students: ${students.length}`,
    `Total Characters: ${totalCharsAllStudents}`,
    '=======================',
    '',
    ...parts,
    '=======================',
    'End of class log.'
  ].join('\n');

  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `braille_class_log_${new Date().toISOString().slice(0,10)}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

document.getElementById('btnExportAll').addEventListener('click', exportAllLogs);
document.getElementById('btnClearAllFeeds').addEventListener('click', clearAllFeeds);
document.getElementById('btnExamExport').addEventListener('click', exportAllLogs);

/* -- Per-Student Serial Connection -- */
async function connectStudentSerial(student) {
  if (RELAY) return connectStudentSerialRelay(student);
  try {
    student.connected = false;
    renderRoster(); renderFeedGrid();

    const port = await navigator.serial.requestPort();
    await port.open({ baudRate: student.baud });

    student.serialPort = port;
    student.connected = true;
    student.readLoopActive = true;

    renderRoster(); renderFeedGrid();
    startStudentReadLoop(student);
  } catch (err) {
    if (err.name !== 'NotFoundError') {
      console.error(`Failed to connect ${student.name}:`, err);
    }
    student.connected = false;
    renderRoster(); renderFeedGrid();
  }
}

async function connectStudentSerialRelay(student) {
  if (!student.portName) {
    if (relayAssignments[student.name]) student.portName = relayAssignments[student.name];
    else {
      showToast(`Assign a COM port to "${student.name}" in the Add Student form first.`);
      return;
    }
  }
  const ok = await relayApi.open_port(student.portName, student.baud);
  if (!ok) {
    showToast(`The relay could not open ${student.portName}. Is it in use elsewhere?`);
    renderRoster(); renderFeedGrid();
    return;
  }
  student.connected = true;
  relayStudentFeeds.set(student.portName, makeSerialFeed(
    l => handleLineForTeacherStudent(student, l),
    c => handleCharsForTeacherStudent(student, c)));
  relayApi.set_assignment(student.name, student.portName);
  relayAssignments[student.name] = student.portName;
  renderRoster(); renderFeedGrid();
}

async function disconnectStudentSerial(student, quiet = false) {
  if (RELAY) {
    if (student.portName) {
      await relayApi.close_port(student.portName);
      relayStudentFeeds.delete(student.portName);
    }
    student.connected = false;
    if (!quiet) { renderRoster(); renderFeedGrid(); }
    return;
  }
  student.readLoopActive = false;
  if (student.serialReader) { try { await student.serialReader.cancel(); } catch(e) {} student.serialReader = null; }
  if (student.serialPort) { try { await student.serialPort.close(); } catch(e) {} student.serialPort = null; }
  student.connected = false;
  if (!quiet) { renderRoster(); renderFeedGrid(); }
}

async function startStudentReadLoop(student) {
  const decoder = new TextDecoder();
  const feed = makeSerialFeed(
    l => handleLineForTeacherStudent(student, l),
    c => handleCharsForTeacherStudent(student, c));

  try {
    while (student.serialPort && student.serialPort.readable && student.readLoopActive) {
      student.serialReader = student.serialPort.readable.getReader();
      try {
        while (true) {
          const { value, done } = await student.serialReader.read(); if (done) break;
          feed(decoder.decode(value, { stream: true }));
        }
      } finally {
        if (student.serialReader) { student.serialReader.releaseLock(); student.serialReader = null; }
      }
    }
  } catch (err) {
    if (err.name !== 'CancelError' && err.name !== 'AbortError') {
      console.error(`Read error for ${student.name}:`, err);
    }
  }
  if (student.connected) await disconnectStudentSerial(student, true);
}

// Remove the last character from a teacher-mode student's data and all feeds
function handleStudentBackspace(student) {
  if (student.chars.length === 0) return;
  const removed = student.chars.pop();
  if (removed) totalCharsAllStudents--;
  updateStudentFeed(student);
  const examText = document.getElementById(`examText-${student.id}`);
  if (examText) rebuildExamFeed(student);
  updateStudentStats();
  updateExamStats();
  updateCharCount(student);
  if (expandStudentId === student.id) updateExpandView();
}

function handleStudentChar(student, ch) {
  try {
    student.chars.push({ char: ch, time: Date.now() });
    totalCharsAllStudents++;
    console.log(`[${student.name}] char: '${ch}' (total chars: ${student.chars.length})`);
    // Rebuild feed from full chars array — always accurate
    updateStudentFeed(student);
    // Also update exam feed if exam mode is active
    const examText = document.getElementById(`examText-${student.id}`);
    if (examText) rebuildExamFeed(student);
    updateMiniDots(student, ch);
    updateStudentStats();
    updateExamStats();
    updateCharCount(student);
    // Update expand modal if open for this student
    if (expandStudentId === student.id) updateExpandView();
  } catch (err) {
    console.error(`[${student.name}] Error handling char '${ch}':`, err);
  }
}

function updateCharCount(student) {
  const el = document.getElementById(`feedCount-${student.id}`);
  if (el) el.textContent = student.chars.length;
  updateExamCount(student.id);
}

function updateMiniDots(student, lastChar) {
  const chord = charToChord.get(lastChar);
  const dots = document.querySelectorAll(`#feedBar-${student.id} .mini-dot`);
  const chordEl = document.getElementById(`feedChord-${student.id}`);
  dots.forEach(d => d.classList.remove('active'));
  if (chord !== undefined) {
    for (let i = 0; i < 6; i++) if (chord & (1 << i)) dots[i].classList.add('active');
    if (chordEl) chordEl.textContent = `0b${chord.toString(2).padStart(6, '0')}`;
  }
  updateExamMiniDots(student.id, lastChar);
}

/* -- Rendering -- */
function renderRoster() {
  const list = document.getElementById('rosterList');
  const empty = document.getElementById('rosterEmpty');
  list.querySelectorAll('.student-item').forEach(el => el.remove());
  if (students.length === 0) { empty.style.display = 'block'; return; }
  empty.style.display = 'none';

  for (const s of students) {
    const item = document.createElement('div');
    item.className = 'student-item';
    const connIcon = s.connType === 'usb' ? 'fa-solid fa-cable' : 'fa-brands fa-bluetooth';
    const connLabel = s.connType === 'usb' ? 'USB' : 'BT';

    item.innerHTML = `
      <div class="student-avatar" style="background:${s.color}">${getInitials(s.name)}</div>
      <div class="student-info">
        <div class="student-name">${s.name}</div>
        <div class="student-meta">
          <span class="conn-badge ${s.connType}"><i class="${connIcon}"></i> ${connLabel}</span>
          ${s.baud} baud${s.portName ? ' · ' + s.portName : ''}
        </div>
      </div>
      <div class="student-status ${s.connected ? 'online' : 'offline'}"></div>
    `;

    if (s.mirror) {
      // Mirrored students share the live student-view connection — they are
      // not independently connectable, so show a badge instead of a button.
      const badge = document.createElement('span');
      badge.className = 'conn-badge mirror';
      badge.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Mirrored';
      badge.title = 'Mirrored from Student View — data comes from the live connection';
      item.appendChild(badge);
    } else {
      const connectBtn = document.createElement('button');
      connectBtn.className = `btn btn-icon ${s.connected ? 'btn-danger' : 'btn-secondary'}`;
      connectBtn.style.cssText = 'width:auto;padding:4px 10px;font-size:10px;gap:4px;';
      connectBtn.innerHTML = s.connected
        ? '<i class="fa-solid fa-plug" style="color:var(--accent-red);"></i>'
        : '<i class="fa-solid fa-bolt"></i>';
      connectBtn.title = s.connected ? 'Disconnect' : 'Connect serial port';
      connectBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        if (s.connected) await disconnectStudentSerial(s);
        else await connectStudentSerial(s);
      });
      item.appendChild(connectBtn);
    }

    item.addEventListener('click', () => {
      document.querySelectorAll('.student-item').forEach(el => el.classList.remove('active'));
      item.classList.add('active');
      const card = document.getElementById(`feed-${s.id}`);
      if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });

    list.appendChild(item);
  }
}

function renderFeedGrid() {
  const grid = document.getElementById('feedGrid');
  const empty = document.getElementById('feedEmpty');
  grid.querySelectorAll('.student-feed-card').forEach(el => el.remove());
  if (students.length === 0) { empty.style.display = 'block'; return; }
  empty.style.display = 'none';

  for (const s of students) {
    const card = document.createElement('div');
    card.className = 'student-feed-card'; card.id = `feed-${s.id}`;
    const connIcon = s.connType === 'usb' ? 'fa-solid fa-cable' : 'fa-brands fa-bluetooth';
    const connLabel = s.connType === 'usb' ? 'USB' : 'BT';
    const statusColor = s.connected ? 'var(--accent-green)' : 'var(--text-muted)';
    const statusIcon = s.connected ? 'fa-solid fa-circle' : 'fa-regular fa-circle';
    const statusText = s.connected ? 'Online' : 'Offline';

    card.innerHTML = `
      <div class="feed-card-header" style="border-left: 3px solid ${s.color};">
        <div class="feed-card-avatar" style="background:${s.color}">${getInitials(s.name)}</div>
        <div class="feed-card-info">
          <div class="feed-card-name">${s.name}</div>
          <div class="feed-card-sub">
            <span class="conn-badge ${s.connType}"><i class="${connIcon}"></i> ${connLabel}</span>
            ${s.mirror ? '<span class="conn-badge mirror"><i class="fa-solid fa-paper-plane"></i> Mirrored</span>' : ''}
            <span style="opacity:0.5;">${s.baud} baud${s.portName ? ' · ' + s.portName : ''}</span>
            <span style="margin-left:auto;display:flex;align-items:center;gap:3px;">
              <i class="${statusIcon}" style="font-size:7px;color:${statusColor};"></i>
              ${statusText}
            </span>
          </div>
        </div>
        <div class="feed-card-actions">
          <button class="btn btn-icon btn-secondary" title="Preview as prose" data-action="preview" style="width:26px;height:26px;font-size:11px;"><i class="fa-solid fa-file-lines"></i></button>
          <button class="btn btn-icon btn-secondary" title="Enlarge view" data-action="expand" style="width:26px;height:26px;font-size:11px;"><i class="fa-solid fa-expand"></i></button>
          <button class="btn btn-icon btn-secondary" title="Test — simulate typing" data-action="test" style="width:26px;height:26px;font-size:11px;"><i class="fa-solid fa-flask"></i></button>
          <button class="btn btn-icon btn-secondary" title="Export as .txt" data-action="export" style="width:26px;height:26px;font-size:11px;"><i class="fa-solid fa-file-export"></i></button>
          <button class="btn btn-icon btn-secondary" title="Clear feed" data-action="clear" style="width:26px;height:26px;font-size:11px;"><i class="fa-solid fa-eraser"></i></button>
          <button class="btn btn-icon btn-danger" title="Remove student" data-action="remove" style="width:26px;height:26px;font-size:11px;"><i class="fa-solid fa-xmark"></i></button>
        </div>
      </div>
      <div class="feed-card-body">
        <div class="feed-text" id="feedText-${s.id}">
          <span class="placeholder"><i class="fa-regular fa-keyboard" style="margin-right:4px;"></i> Waiting for input&hellip;</span>
          <span class="cursor-blink"></span>
        </div>
        <div class="feed-chord-bar" id="feedBar-${s.id}">
          <span class="mini-dots">${'<span class="mini-dot"></span>'.repeat(6)}</span>
          <span id="feedChord-${s.id}" style="font-size:10px;color:var(--text-muted);">No chord</span>
          <span class="count"><i class="fa-regular fa-keyboard"></i> <span id="feedCount-${s.id}">0</span></span>
        </div>
      </div>
    `;

    card.querySelector('[data-action="preview"]').addEventListener('click', e => { e.stopPropagation(); openLogPreview(s); });
    card.querySelector('[data-action="expand"]').addEventListener('click', e => { e.stopPropagation(); openExpandView(s); });
    card.querySelector('[data-action="test"]').addEventListener('click', e => { e.stopPropagation(); simulateStudentTyping(s); });
    card.querySelector('[data-action="export"]').addEventListener('click', e => { e.stopPropagation(); exportStudentLog(s); });
    card.querySelector('[data-action="clear"]').addEventListener('click', e => { e.stopPropagation(); clearStudentFeed(s.id); });
    card.querySelector('[data-action="remove"]').addEventListener('click', e => { e.stopPropagation(); removeStudent(s.id); });

    grid.appendChild(card);
  }
}

/* -- Shared render helper -- */
function renderCharsInto(container, chars) {
  const ph = container.querySelector('.placeholder'); if (ph) ph.remove();
  const oc = container.querySelector('.cursor-blink'); if (oc) oc.remove();
  container.innerHTML = '';
  if (chars.length === 0) {
    container.innerHTML = '<span class="placeholder"><i class="fa-regular fa-keyboard"></i> Waiting for input&hellip;</span><span class="cursor-blink"></span>';
    container.scrollTop = 0;
    return;
  }
  for (const entry of chars) {
    const ch = entry.char ?? entry;
    if (ch === ' ') {
      const sp = document.createElement('span');
      sp.textContent = ' '; sp.style.display = 'inline-block'; sp.style.width = '0.35em'; sp.className = 'live-char';
      container.appendChild(sp);
    } else {
      const span = document.createElement('span');
      span.textContent = ch; span.className = 'live-char';
      if (/[\u0980-\u09FF]/.test(ch)) span.style.fontFamily = 'var(--font-bangla)';
      container.appendChild(span);
    }
  }
  const cursor = document.createElement('span'); cursor.className = 'cursor-blink';
  container.appendChild(cursor);
  container.scrollTop = container.scrollHeight;
}

function updateStudentFeed(student) {
  const feedText = document.getElementById(`feedText-${student.id}`);
  if (!feedText) return;
  renderCharsInto(feedText, student.chars);
}

function rebuildExamFeed(student) {
  const examText = document.getElementById(`examText-${student.id}`);
  if (!examText) return;
  renderCharsInto(examText, student.chars);
}

/* ============================================================
   LOG PREVIEW MODAL (Readable Prose)
   ============================================================ */
let previewStudentId = null;

function openLogPreview(student) {
  previewStudentId = student.id;
  const modal = document.getElementById('previewModal');
  const title = document.getElementById('previewModalTitle');
  const sub = document.getElementById('previewModalSub');
  const body = document.getElementById('previewModalBody');
  const info = document.getElementById('previewModalInfo');
  const exportBtn = document.getElementById('previewModalExport');

  title.textContent = student.name;
  sub.innerHTML = `<i class="fa-regular fa-circle-dot" style="margin-right:2px;"></i> ${student.connType.toUpperCase()} &mdash; ${student.baud} baud &mdash; ${student.chars.length} chars`;

  // Build readable prose
  const lines = buildReadableLog(student.chars);
  body.innerHTML = '';
  if (lines.length === 0) {
    body.innerHTML = '<div class="preview-empty"><i class="fa-regular fa-keyboard" style="font-size:28px;opacity:0.3;display:block;margin-bottom:12px;"></i>No characters yet</div>';
  } else {
    for (const line of lines) {
      const lineEl = document.createElement('div');
      lineEl.className = 'preview-line';
      const ts = document.createElement('span');
      ts.className = 'preview-ts';
      ts.textContent = `[${formatCharTimestamp(line.time)}]`;
      const txt = document.createElement('span');
      txt.className = 'preview-text';
      txt.textContent = line.text;
      lineEl.appendChild(ts);
      lineEl.appendChild(txt);
      body.appendChild(lineEl);
    }
  }

  info.textContent = `${student.chars.length} character(s) — ${lines.length} line(s)`;

  // Wire the Export button to export this student's log
  exportBtn.onclick = () => exportStudentLog(student);

  modal.classList.add('visible');
  document.body.style.overflow = 'hidden';
}

function closeLogPreview() {
  previewStudentId = null;
  document.getElementById('previewModal').classList.remove('visible');
  document.body.style.overflow = '';
}

document.getElementById('previewModalClose').addEventListener('click', closeLogPreview);
document.getElementById('previewModal').addEventListener('click', e => {
  if (e.target === e.currentTarget) closeLogPreview();
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && document.getElementById('previewModal').classList.contains('visible')) {
    closeLogPreview();
  }
});

/* ============================================================
   EXPANDED VIEW (Per-Student Modal)
   ============================================================ */
let expandStudentId = null;

function openExpandView(student) {
  expandStudentId = student.id;
  const modal = document.getElementById('expandModal');
  const avatar = document.getElementById('expandModalAvatar');
  const name = document.getElementById('expandModalName');
  const sub = document.getElementById('expandModalSub');
  const count = document.getElementById('expandModalCount');
  const body = document.getElementById('expandModalBody');

  avatar.textContent = getInitials(student.name);
  avatar.style.background = student.color;
  name.textContent = student.name;
  const connLabel = student.connType === 'usb' ? 'USB' : 'Bluetooth';
  sub.innerHTML = `<i class="fa-regular fa-circle-dot" style="margin-right:2px;"></i> ${connLabel} &mdash; ${student.baud} baud`;
  count.innerHTML = `<i class="fa-regular fa-keyboard"></i> ${student.chars.length} chars`;

  renderCharsInto(body, student.chars);

  modal.classList.add('visible');
  document.body.style.overflow = 'hidden';
  // Check scroll indicator after browser paints the modal
  requestAnimationFrame(() => requestAnimationFrame(checkExpandScroll));
}

function closeExpandView() {
  expandStudentId = null;
  document.getElementById('expandModal').classList.remove('visible');
  document.body.style.overflow = '';
}

function updateExpandView() {
  const modal = document.getElementById('expandModal');
  if (!modal.classList.contains('visible')) return;
  const student = students.find(s => s.id === expandStudentId);
  if (!student) { closeExpandView(); return; }

  document.getElementById('expandModalCount').innerHTML = `<i class="fa-regular fa-keyboard"></i> ${student.chars.length} chars`;
  const body = document.getElementById('expandModalBody');
  renderCharsInto(body, student.chars);
}

// Wire modal close events
document.getElementById('expandModalClose').addEventListener('click', closeExpandView);
document.getElementById('expandModalPreviewBtn').addEventListener('click', () => {
  const student = students.find(s => s.id === expandStudentId);
  if (student) { closeExpandView(); setTimeout(() => openLogPreview(student), 200); }
});
document.getElementById('expandModal').addEventListener('click', e => {
  if (e.target === e.currentTarget) closeExpandView();
});
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && expandStudentId !== null) closeExpandView();
  if (e.ctrlKey && e.key === 'Enter' && expandStudentId !== null) {
    e.preventDefault();
    clearStudentFeed(expandStudentId);
  }
});

/* -- Expand modal scroll indicator -- */
const expandBody = document.getElementById('expandModalBody');
const expandScrollBtn = document.getElementById('expandScrollBtn');

function checkExpandScroll() {
  if (!expandBody) return;
  const atBottom = expandBody.scrollHeight - expandBody.scrollTop - expandBody.clientHeight < 30;
  expandBody.classList.toggle('scrollable', expandBody.scrollHeight > expandBody.clientHeight + 10);
  expandScrollBtn.classList.toggle('visible', !atBottom);
}

expandBody.addEventListener('scroll', checkExpandScroll);
expandScrollBtn.addEventListener('click', () => {
  expandBody.scrollTo({ top: expandBody.scrollHeight, behavior: 'smooth' });
});

// Check after content updates (via renderCharsInto)
// MutationObserver detects when renderCharsInto populates the body
const expandObserver = new MutationObserver(checkExpandScroll);
expandObserver.observe(expandBody, { childList: true, subtree: true });

/* -- Periodic failsafe refresh -- */
setInterval(() => {
  for (const s of students) {
    if (s.chars.length > 0) {
      updateStudentFeed(s);
      const et = document.getElementById(`examText-${s.id}`);
      if (et) renderCharsInto(et, s.chars);
    }
  }
  if (expandStudentId !== null) updateExpandView();
}, 500);

/* -- Manual test — simulate receiving characters -- */
function simulateStudentTyping(student) {
  const testChars = ['h','e','l','l','o',' ','\u09AC','\u09BE','\u0982','\u09B2','\u09BE'];
  let i = 0;
  const interval = setInterval(() => {
    if (i >= testChars.length || !students.find(s => s.id === student.id)) {
      clearInterval(interval);
      return;
    }
    handleStudentChar(student, testChars[i]);
    i++;
  }, 200);
}

function updateStudentStats() {
  document.getElementById('studentCount').innerHTML = `<i class="fa-regular fa-user"></i> <strong>${students.length}</strong> students`;
  document.getElementById('totalCharCount').textContent = totalCharsAllStudents;
}

/* -- Exam Mode Rendering -- */
function renderExamGrid() {
  const grid = document.getElementById('examGrid');
  const empty = document.getElementById('examEmpty');
  grid.querySelectorAll('.exam-card').forEach(el => el.remove());
  if (students.length === 0) { empty.style.display = 'block'; return; }
  empty.style.display = 'none';

  for (const s of students) {
    const card = document.createElement('div');
    card.className = 'exam-card'; card.id = `exam-${s.id}`;
    const connIcon = s.connType === 'usb' ? 'fa-solid fa-cable' : 'fa-brands fa-bluetooth';
    const connLabel = s.connType === 'usb' ? 'USB' : 'BT';

    card.innerHTML = `
      <div class="exam-card-header" style="border-left: 3px solid ${s.color};">
        <div class="exam-card-avatar" style="background:${s.color}">${getInitials(s.name)}</div>
        <div class="exam-card-info">
          <div class="exam-card-name">${s.name}</div>
          <div class="exam-card-sub">
            <span class="conn-badge ${s.connType}"><i class="${connIcon}"></i> ${connLabel}</span>
            <span style="opacity:0.5;">${s.baud} baud</span>
            ${s.connected
              ? '<span style="display:inline-flex;align-items:center;gap:3px;color:var(--accent-green);"><i class="fa-solid fa-circle" style="font-size:6px;"></i> Online</span>'
              : '<span style="display:inline-flex;align-items:center;gap:3px;opacity:0.5;"><i class="fa-regular fa-circle" style="font-size:6px;"></i> Offline</span>'}
          </div>
        </div>
      </div>
      <div class="exam-card-body">
        <div class="exam-text" id="examText-${s.id}">
          <span class="placeholder"><i class="fa-regular fa-keyboard"></i> Waiting for input&hellip;</span>
          <span class="cursor-blink"></span>
        </div>
      </div>
      <div class="exam-card-footer" id="examBar-${s.id}">
        <span class="mini-dots">${'<span class="mini-dot"></span>'.repeat(6)}</span>
        <span id="examChord-${s.id}">No chord</span>
        <span class="count" id="examCount-${s.id}">0</span>
      </div>
    `;

    grid.appendChild(card);
  }

  // Fill in existing data using shared helper
  for (const s of students) {
    if (s.chars.length > 0) {
      const et = document.getElementById(`examText-${s.id}`);
      if (et) renderCharsInto(et, s.chars);
      updateExamCount(s.id);
      const lastEntry = s.chars[s.chars.length - 1];
      const lastChar = lastEntry.char ?? lastEntry;
      updateExamMiniDots(s.id, lastChar);
    }
  }
}

function updateExamStats() {
  const count = document.getElementById('examStudentCount');
  const chars = document.getElementById('examCharCount');
  if (count) count.innerHTML = `<i class="fa-regular fa-user"></i> <strong>${students.length}</strong>`;
  if (chars) chars.innerHTML = `<i class="fa-regular fa-keyboard"></i> <strong>${totalCharsAllStudents}</strong>`;
}

function updateExamCount(studentId) {
  const el = document.getElementById(`examCount-${studentId}`);
  if (el) {
    const s = students.find(st => st.id === studentId);
    if (s) el.textContent = s.chars.length;
  }
}

function updateExamMiniDots(studentId, lastChar) {
  const chord = charToChord.get(lastChar);
  const dots = document.querySelectorAll(`#examBar-${studentId} .mini-dot`);
  const chordEl = document.getElementById(`examChord-${studentId}`);
  dots.forEach(d => d.classList.remove('active'));
  if (chord !== undefined) {
    for (let i = 0; i < 6; i++) if (chord & (1 << i)) dots[i].classList.add('active');
    if (chordEl) chordEl.textContent = `0b${chord.toString(2).padStart(6, '0')}`;
  }
}

/* ============================================================
   THEME (Light / Dark Mode)
   ============================================================ */
const themeToggle = document.getElementById('themeToggle');

function applyTheme(light) {
  const app = document.getElementById('app');
  app.classList.toggle('light-mode', light);
  document.body.classList.toggle('light-mode', light);
  themeToggle.innerHTML = light
    ? '<i class="fa-solid fa-sun"></i>'
    : '<i class="fa-solid fa-moon"></i>';
  themeToggle.title = light ? 'Switch to dark mode' : 'Switch to light mode';
  try { localStorage.setItem('braillebridge-theme', light ? 'light' : 'dark'); } catch(e) {}
}

themeToggle.addEventListener('click', () => {
  const isLight = document.getElementById('app').classList.contains('light-mode');
  applyTheme(!isLight);
});

document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.shiftKey && (e.key === 'T' || e.key === 't')) {
    e.preventDefault();
    const isLight = document.getElementById('app').classList.contains('light-mode');
    applyTheme(!isLight);
  }
});

// Load saved theme
(function() {
  try {
    const saved = localStorage.getItem('braillebridge-theme');
    if (saved === 'light') applyTheme(true);
  } catch(e) {}
})();

/* ============================================================
   INIT
   ============================================================ */
updateIndicators();
console.log('BrailleBridge Platform ready.');
console.log('Shortcuts: 1-6=toggle dots, Enter=send chord, L=toggle language, S=toggle shift, Space=space');
console.log('Teacher Mode: add students and click the connect button to link their ESP-32.');
