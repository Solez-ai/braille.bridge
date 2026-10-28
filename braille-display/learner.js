/* BrailleBridge — Learner update
   Freeplay Playground (device + keyboard input, speech feedback)
   See What Codes You Need (chord-sequence trainer tool). */
(function () {
  'use strict';

  /* CHORD TABLES — mirror braile/braile.ino exactly. Any change there is a
     change here. Entries are matched in array order, same as the firmware. */
  var DICT = [
    { chord: 0x01, english: 'a', bangla: 'অ' },
    { chord: 0x03, english: 'b', bangla: 'ব' },
    { chord: 0x09, english: 'c', bangla: 'চ' },
    { chord: 0x19, english: 'd', bangla: 'দ' },
    { chord: 0x11, english: 'e', bangla: 'এ' },
    { chord: 0x0b, english: 'f', bangla: null },
    { chord: 0x1b, english: 'g', bangla: 'গ' },
    { chord: 0x13, english: 'h', bangla: 'হ' },
    { chord: 0x08, english: 'i', bangla: '্' },
    { chord: 0x1a, english: 'j', bangla: 'জ' },
    { chord: 0x05, english: 'k', bangla: 'ক' },
    { chord: 0x07, english: 'l', bangla: 'ল' },
    { chord: 0x0d, english: 'm', bangla: 'ম' },
    { chord: 0x1d, english: 'n', bangla: 'ন' },
    { chord: 0x15, english: 'o', bangla: 'ও' },
    { chord: 0x0f, english: 'p', bangla: 'প' },
    { chord: 0x1f, english: 'q', bangla: 'ক্ষ' },
    { chord: 0x17, english: 'r', bangla: 'র' },
    { chord: 0x0c, english: 's', bangla: 'ঐ' },
    { chord: 0x1c, english: 't', bangla: 'আ' },
    { chord: 0x25, english: 'u', bangla: 'উ' },
    { chord: 0x27, english: 'v', bangla: 'ৱ' },
    { chord: 0x3a, english: 'w', bangla: null },
    { chord: 0x2d, english: 'x', bangla: 'য' },
    { chord: 0x3d, english: 'y', bangla: 'য' },
    { chord: 0x35, english: 'z', bangla: 'ড়' },
    { chord: 0x0a, english: null, bangla: 'ই' },
    { chord: 0x12, english: null, bangla: 'ঞ' },
    { chord: 0x0e, english: null, bangla: 'স' },
    { chord: 0x3f, english: null, bangla: 'ঢ' },
    { chord: 0x21, english: null, bangla: 'ছ' },
    { chord: 0x23, english: null, bangla: 'ঘ' },
    { chord: 0x18, english: null, bangla: 'ভ' },
    { chord: 0x39, english: null, bangla: 'থ' },
    { chord: 0x36, english: null, bangla: 'ঠ' },
    { chord: 0x2a, english: null, bangla: 'ঔ' },
    { chord: 0x16, english: null, bangla: 'ফ' },
    { chord: 0x34, english: null, bangla: 'ঝ' },
    { chord: 0x2b, english: null, bangla: 'ড' },
    { chord: 0x14, english: null, bangla: 'ঈ' },
    { chord: 0x1e, english: null, bangla: 'ত' },
    { chord: 0x28, english: null, bangla: 'খ' },
    { chord: 0x2c, english: null, bangla: 'ঙ' },
    { chord: 0x3e, english: null, bangla: 'ট' },
    { chord: 0x2e, english: null, bangla: 'ধ' },
    { chord: 0x3c, english: null, bangla: 'ণ' },
    { chord: 0x33, english: null, bangla: 'ঊ' },
    { chord: 0x2f, english: null, bangla: 'ষ' },
    { chord: 0x31, english: null, bangla: 'শ' },
    { chord: 0x30, english: null, bangla: 'ং' },
    { chord: 0x10, english: null, bangla: 'ঁ' },
    { chord: 0x26, english: null, bangla: 'ি' },
    { chord: 0x32, english: null, bangla: 'ূ' },
    { chord: 0x22, english: null, bangla: 'স' },
  ];

  var NUMBER_CHORDS = [0x01, 0x03, 0x09, 0x19, 0x11, 0x0b, 0x1b, 0x13, 0x08, 0x1a];
  var NUMBER_MAP = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'];

  var SHIFT_SYMBOLS = [
    { chord: 0x16, symbol: '+' }, { chord: 0x24, symbol: '-' },
    { chord: 0x26, symbol: '×' }, { chord: 0x36, symbol: '=' },
    { chord: 0x0c, symbol: '÷' }, { chord: 0x02, symbol: ',' },
    { chord: 0x06, symbol: ';' }, { chord: 0x12, symbol: ':' },
    { chord: 0x32, symbol: '.' },
  ];

  var BANGLA_SHIFT_MAP = [
    { chord: 0x01, kar: null }, { chord: 0x1c, kar: 'া' },
    { chord: 0x0a, kar: 'ি' }, { chord: 0x14, kar: 'ী' },
    { chord: 0x25, kar: 'ু' }, { chord: 0x33, kar: 'ূ' },
    { chord: 0x11, kar: 'ে' }, { chord: 0x0c, kar: 'ৈ' },
    { chord: 0x15, kar: 'ো' }, { chord: 0x2a, kar: 'ৌ' },
  ];

  /* REVERSE MAPS — char -> { chord, shift:bool }. Built to reproduce the
     firmware's own priority so the trainer never teaches a wrong keypress:
     Bangla unshifted dict first, then shift-only kar signs. */
  var REVERSE = { en: {}, bn: {} };

  function put(map, ch, chord, shift) { if (!(ch in map)) map[ch] = { chord: chord, shift: shift }; }

  DICT.forEach(function (e) {
    if (e.english) put(REVERSE.en, e.english, e.chord, false);
    if (e.bangla) put(REVERSE.bn, e.bangla, e.chord, false);
  });
  NUMBER_MAP.forEach(function (d, i) { put(REVERSE.en, d, NUMBER_CHORDS[i], true); });
  for (var i = 0; i < 26; i++) {
    var lc = String.fromCharCode(97 + i);
    if (lc in REVERSE.en) put(REVERSE.en, lc.toUpperCase(), REVERSE.en[lc].chord, true);
  }
  SHIFT_SYMBOLS.forEach(function (s) { put(REVERSE.en, s.symbol, s.chord, true); });
  BANGLA_SHIFT_MAP.forEach(function (s) { if (s.kar) put(REVERSE.bn, s.kar, s.chord, true); });

  // Multi-character Bangla strings (e.g. ক্ষ) matched greedily so the trainer
  // recommends the single chord the firmware offers instead of three presses.
  var BANGLA_MULTI = DICT.filter(function (e) { return e.bangla && e.bangla.length > 1; })
    .map(function (e) { return { text: e.bangla, chord: e.chord }; })
    .sort(function (a, b) { return b.text.length - a.text.length; });

  function chordDotsList(chord) {
    var dots = [];
    for (var d = 0; d < 6; d++) if (chord & (1 << d)) dots.push(d + 1);
    return dots;
  }

  /* decodeText(text, lang) -> [{ type:'chord'|'space'|'newline'|'unknown',
     char, chord, shift, dots, text? }] */
  function decodeText(text, lang) {
    var steps = [];
    var map = lang === 'bn' ? REVERSE.bn : REVERSE.en;
    var chars = Array.from(text);
    var p = 0;
    while (p < chars.length) {
      var c = chars[p];
      if (c === ' ') { steps.push({ type: 'space' }); p++; continue; }
      if (c === '\n' || c === '\r' || c === '\t') { steps.push({ type: 'newline' }); p++; continue; }
      if (lang === 'bn') {
        // Greedy multi-character match first, so conjuncts like ক্ষ decode to
        // the one chord the firmware provides instead of three presses.
        var hit = null;
        for (var m = 0; m < BANGLA_MULTI.length; m++) {
          var n = Array.from(BANGLA_MULTI[m].text);
          if (n.length > 1 && n.every(function (nc, k) { return chars[p + k] === nc; })) { hit = BANGLA_MULTI[m]; break; }
        }
        if (hit) {
          steps.push({ type: 'chord', char: hit.text, chord: hit.chord, shift: false, dots: chordDotsList(hit.chord) });
          p += Array.from(hit.text).length; continue;
        }
      }
      var direct = map[c];
      if (direct) {
        steps.push({ type: 'chord', char: c, chord: direct.chord, shift: direct.shift, dots: chordDotsList(direct.chord) });
        p++; continue;
      }
      steps.push({ type: 'unknown', char: c });
      p++;
    }
    return steps;
  }

  /* SPEECH — produce what the synthesizer should say for one character. */
  var SYMBOL_NAMES = { '+': 'plus', '-': 'minus', '×': 'times', '÷': 'divided by', '=': 'equals', ',': 'comma', ';': 'semicolon', ':': 'colon', '.': 'period' };
  function speechTextFor(ch) {
    if (/[A-Z]/.test(ch)) return 'capital ' + ch.toLowerCase();
    return SYMBOL_NAMES[ch] || ch;
  }

  // Node test export (browser wiring below needs no DOM-independent pieces).
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { decodeText: decodeText, chordDotsList: chordDotsList, speechTextFor: speechTextFor, REVERSE: REVERSE };
    return;
  }

  /* ================================================================
     BROWSER WIRING — everything below touches the DOM.
     ================================================================ */
  var view = document.getElementById('viewLearn');
  if (!view) return;

  var $ = function (id) { return document.getElementById(id); };
  var store = {
    get: function (k, fallback) {
      try { var v = localStorage.getItem(k); return v === null ? fallback : v; } catch (e) { return fallback; }
    },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  };
  var input = $('learnerInput'), wordsBox = $('learnerWords'), voiceChip = $('voiceChip');
  var deviceLangChip = $('deviceLangChip');
  var decoderInput = $('decoderInput'), decoderSequence = $('decoderSequence');
  var decoderLang = 'en', learnerLang = 'en';
  var lastWord = '';
  var lastValue = '';

  /* Speech */
  var voices = [];
  var onlineBanglaAudio = new Audio();
  function refreshVoices() { if ('speechSynthesis' in window) voices = window.speechSynthesis.getVoices() || []; updateVoiceChip(); }
  function pickVoice(lang) {
    var prefs = lang === 'bn' ? ['bn-bd', 'bn_bd', 'bn-in', 'bn_in', 'bn'] : ['en-us', 'en_us', 'en-gb', 'en_gb', 'en'];
    for (var i = 0; i < prefs.length; i++) {
      for (var j = 0; j < voices.length; j++) {
        if (String(voices[j].lang || '').toLowerCase().indexOf(prefs[i]) === 0) return voices[j];
      }
    }
    return null;
  }
  function updateVoiceChip() {
    if (!('speechSynthesis' in window)) return;
    var bn = pickVoice('bn'), en = pickVoice('en');
    if (bn) {
      voiceChip.innerHTML = '<i class="fa-solid fa-volume-high"></i> English + বাংলা (Windows Voice)';
      voiceChip.title = 'Offline Windows Bengali voice installed (' + bn.name + ')';
    } else {
      voiceChip.innerHTML = '<i class="fa-solid fa-volume-high"></i> English + বাংলা (Online Voice)';
      voiceChip.title = 'Online Bengali voice active. Install Windows Bangla speech in Settings for offline use.';
    }
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.onvoiceschanged = refreshVoices;
    refreshVoices();
  }

  function utterBanglaOnline(text) {
    if (!text) return;
    try {
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
      var clean = String(text).trim();
      if (!clean) return;
      var url = 'https://translate.google.com/translate_tts?ie=UTF-8&tl=bn&client=tw-ob&q=' + encodeURIComponent(clean);
      onlineBanglaAudio.pause();
      onlineBanglaAudio.currentTime = 0;
      onlineBanglaAudio.src = url;
      onlineBanglaAudio.play().catch(function (e) {
        if ('speechSynthesis' in window) {
          var u = new SpeechSynthesisUtterance(clean);
          u.lang = 'bn-BD';
          window.speechSynthesis.speak(u);
        }
      });
    } catch (err) {
      console.warn('Bangla speech error:', err);
    }
  }

  function utter(text, lang) {
    if (!text) return;
    var v = pickVoice(lang);
    if (lang === 'bn' && !v) {
      utterBanglaOnline(text);
      return;
    }
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text);
    if (v) { u.voice = v; u.lang = v.lang; } else u.lang = lang === 'bn' ? 'bn-BD' : 'en-US';
    window.speechSynthesis.speak(u);
  }
  window.BBUtter = utter;
  function langOfChar(ch) { return /[\u0980-\u09FF]/.test(ch) ? 'bn' : learnerLang; }

  /* Playground */
  var wordHistory = [];
  try { wordHistory = JSON.parse(store.get('braillebridge-learner-words', '[]')) || []; } catch (e) { wordHistory = []; }
  if (!Array.isArray(wordHistory)) wordHistory = [];
  function saveWords() { store.set('braillebridge-learner-words', JSON.stringify(wordHistory.slice(-60))); }
  function makeChip(word) {
    var chip = document.createElement('span');
    chip.className = 'learn-word-chip';
    chip.textContent = word;
    if (/[\u0980-\u09FF]/.test(word)) chip.style.fontFamily = 'var(--font-bangla)';
    return chip;
  }
  function addWordChip(word) {
    if (!word) return;
    lastWord = word;
    var empty = wordsBox.querySelector('.learn-words-empty');
    if (empty) empty.remove();
    wordHistory.push(word);
    if (wordHistory.length > 60) wordHistory.shift();
    saveWords();
    var chip = makeChip(word);
    wordsBox.appendChild(chip);
    wordsBox.scrollTop = wordsBox.scrollHeight;
  }
  // Restore the word history from the previous session (chips only — nothing spoken).
  function restoreWords() {
    if (!wordHistory.length) return;
    var empty = wordsBox.querySelector('.learn-words-empty');
    if (empty) empty.remove();
    wordHistory.slice(-30).forEach(function (w) { wordsBox.appendChild(makeChip(w)); });
    lastWord = wordHistory[wordHistory.length - 1];
    wordsBox.scrollTop = wordsBox.scrollHeight;
  }
  function speakWordIfComplete(value) {
    var trimmed = value.replace(/^\s+/, '');
    if (/ $/.test(value)) {
      var parts = trimmed.split(/\s+/).filter(Boolean);
      var w = parts[parts.length - 1] || '';
      if (w) { addWordChip(w); utter(w, /[\u0980-\u09FF]/.test(w) ? 'bn' : learnerLang); }
    }
  }
  function applyExternalChars(chunk) {
    for (var ch of chunk) {
      if (ch === '\r' || ch === '\n') continue;
      input.value += ch;
      if (ch !== ' ') utter(speechTextFor(ch), langOfChar(ch));
      speakWordIfComplete(input.value);
      lastValue = input.value;
    }
  }

  input.addEventListener('input', function () {
    var prev = lastValue, now = input.value;
    // Speak only the characters added at the end (device + typing updates).
    if (now.length > prev.length && now.indexOf(prev) === 0) {
      var added = now.slice(prev.length);
      var wasWord = /\s$/.test(added);
      for (var ch of added) {
        if (ch === ' ' || ch === '\n') continue;
        utter(speechTextFor(ch), langOfChar(ch));
      }
      if (wasWord) speakWordIfComplete(now);
    }
    lastValue = now;
  });
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      var w = input.value.trim().split(/\s+/).filter(Boolean).pop();
      if (w) { addWordChip(w); utter(w, /[\u0980-\u09FF]/.test(w) ? 'bn' : learnerLang); }
    }
  });
  $('learnerRepeatBtn').addEventListener('click', function () {
    if (lastWord) utter(lastWord, /[\u0980-\u09FF]/.test(lastWord) ? 'bn' : learnerLang);
  });
  $('learnerClearBtn').addEventListener('click', function () {
    input.value = ''; lastValue = '';
    wordsBox.innerHTML = '<span class="learn-words-empty">Spoken words appear here</span>';
    wordHistory = []; saveWords();
  });
  // Progress log: every word the student has spoken, oldest first, plus a
  // frequency list — saved as a plain .txt file.
  $('learnerExportBtn').addEventListener('click', function () {
    if (!wordHistory.length) {
      try { if (typeof showToast === 'function') showToast('Nothing to export yet — speak a word first.'); } catch (e) {}
      return;
    }
    var lines = ['BrailleBridge — Learner Progress', '=======================',
      'Exported: ' + new Date().toLocaleString(),
      'Words practiced: ' + wordHistory.length,
      '=======================', ''];
    var counts = {};
    for (var i = 0; i < wordHistory.length; i++) {
      lines.push((i + 1) + '. ' + wordHistory[i]);
      counts[wordHistory[i]] = (counts[wordHistory[i]] || 0) + 1;
    }
    lines.push('', '--- Word frequency ---');
    Object.keys(counts).sort(function (a, b) { return counts[b] - counts[a]; })
      .forEach(function (w) { lines.push(counts[w] + '× ' + w); });
    lines.push('', '=======================', 'End of progress log.');
    var blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'BrailleBridge_Learner_Progress_' + new Date().toISOString().slice(0, 10) + '.txt';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });

  // Language toggle: controls which language the keyboard fallback speaks for
  // ASCII input; Bangla speech follows the actual characters typed.
  var learnerLangBtns = $('learnerLangToggle').querySelectorAll('.learn-lang-btn');
  learnerLangBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      learnerLangBtns.forEach(function (x) { x.classList.remove('active'); });
      b.classList.add('active');
      learnerLang = b.dataset.lang;
      store.set('braillebridge-learner-lang', learnerLang);
      input.focus();
    });
  });
  // Restore the playground language toggle.
  var savedLearnerLang = store.get('braillebridge-learner-lang', '');
  if (savedLearnerLang === 'en' || savedLearnerLang === 'bn') {
    learnerLangBtns.forEach(function (x) { x.classList.toggle('active', x.dataset.lang === savedLearnerLang); });
    learnerLang = savedLearnerLang;
  }

  /* Serial connection — mirrors the Student view transports.
     Relay mode (desktop app): wrap the Python relay callbacks so learner
     feeds receive their port's data without disturbing other views.
     Browser: a private Web Serial connection. */
  var learnerFeeds = new Map();
  var learnerRelayPort = null;
  var learnerSerialPort = null, learnerSerialReader = null;

  function handleLine(line) {
    if (line === 'SYSTEM:BKSP') {
      if (input.value.length) {
        input.value = input.value.slice(0, -1);
        lastValue = input.value;
        input.focus();
      }
      return;
    }
    if (line === 'LANG:en' || line === 'LANG:bn') {
      deviceLangChip.style.display = 'inline-flex';
      deviceLangChip.innerHTML = line === 'LANG:bn'
        ? 'Device: <strong style="font-family:var(--font-bangla);">বাংলা</strong>'
        : 'Device: English';
      return;
    }
  }
  function handleChars(chunk) { applyExternalChars(chunk); }

  function getRelay() { try { return (typeof RELAY !== 'undefined' && RELAY && relayApi) ? true : false; } catch (e) { return false; } }
  function getPorts() { try { return (typeof currentPorts !== 'undefined' && currentPorts) || []; } catch (e) { return []; } }
  function getSerialFeed() { try { return (typeof makeSerialFeed === 'function') ? makeSerialFeed : null; } catch (e) { return null; } }

  function populateLearnerPorts() {
    var sel = $('learnerPortSelect');
    if (!sel) return;
    var ports = getPorts();
    var keep = sel.value;
    sel.innerHTML = '';
    if (!ports.length) {
      var o = document.createElement('option'); o.value = ''; o.textContent = '(no ports detected)'; sel.appendChild(o);
    } else {
      for (var p of ports) {
        var op = document.createElement('option'); op.value = p.name; op.textContent = p.name + ' — ' + p.description; sel.appendChild(op);
      }
    }
    if (keep && Array.prototype.some.call(sel.options, function (x) { return x.value === keep; })) sel.value = keep;
  }
  $('learnerPortRow').style.display = getRelay() ? 'flex' : 'none';

  if (typeof window.__relayOnData === 'function') {
    var prevOnData = window.__relayOnData;
    window.__relayOnData = function (portName, chunk) {
      var f = learnerFeeds.get(portName);
      if (f) { f(chunk); return; }
      prevOnData(portName, chunk);
    };
  }
  if (typeof window.__relayOnPorts === 'function') {
    var prevOnPorts = window.__relayOnPorts;
    window.__relayOnPorts = function (ports) { prevOnPorts(ports); populateLearnerPorts(); };
  }

  function setLearnerConnectedUI(connected, msg) {
    var btn = $('learnerConnect');
    btn.classList.toggle('connected', connected);
    btn.innerHTML = connected
      ? '<i class="fa-solid fa-plug"></i> Disconnect'
      : '<i class="fa-solid fa-bolt"></i> Connect BrailleBridge';
    if (msg) deviceLangChip.style.display = 'inline-flex', deviceLangChip.textContent = msg;
    if (!connected && msg === undefined) deviceLangChip.style.display = 'none';
  }

  $('learnerConnect').addEventListener('click', async function () {
    if (getRelay()) {
      if (learnerRelayPort) {
        await relayApi.close_port(learnerRelayPort);
        learnerFeeds.delete(learnerRelayPort);
        learnerRelayPort = null;
        setLearnerConnectedUI(false);
        return;
      }
      var portName = $('learnerPortSelect').value;
      if (!portName) { setLearnerConnectedUI(false, 'No COM port selected — pick one above, then connect.'); return; }
      var ok = await relayApi.open_port(portName, 115200);
      if (!ok) { setLearnerConnectedUI(false, 'Could not open ' + portName + ' — is it in use?'); return; }
      learnerRelayPort = portName;
      var mk = getSerialFeed();
      learnerFeeds.set(portName, mk(handleLine, handleChars));
      setLearnerConnectedUI(true);
      input.focus();
      return;
    }
    if (learnerSerialPort) {
      try { if (learnerSerialReader) await learnerSerialReader.cancel(); } catch (e) {}
      try { await learnerSerialPort.close(); } catch (e) {}
      learnerSerialPort = null; learnerSerialReader = null;
      setLearnerConnectedUI(false);
      return;
    }
    if (!navigator.serial) { setLearnerConnectedUI(false, 'This browser has no Web Serial — use the desktop app.'); return; }
    try {
      learnerSerialPort = await navigator.serial.requestPort();
      await learnerSerialPort.open({ baudRate: 115200 });
      setLearnerConnectedUI(true);
      input.focus();
      var decoder = new TextDecoder();
      var mk2 = getSerialFeed();
      var lf = mk2 ? mk2(handleLine, handleChars) : null;
      (async function readLoop() {
        try {
          while (learnerSerialPort && learnerSerialPort.readable) {
            learnerSerialReader = learnerSerialPort.readable.getReader();
            while (true) {
              var res = await learnerSerialReader.read();
              if (res.done) break;
              if (lf) lf(decoder.decode(res.value, { stream: true }));
            }
            try { learnerSerialReader.releaseLock(); } catch (e) {}
            learnerSerialReader = null;
          }
        } catch (err) { /* canceled or unplugged */ }
      })();
    } catch (err) {
      if (err.name !== 'NotFoundError') setLearnerConnectedUI(false, 'Connection failed: ' + err.message);
      else setLearnerConnectedUI(false);
      if (learnerSerialPort) { try { await learnerSerialPort.close(); } catch (e) {} learnerSerialPort = null; }
    }
  });

  /* Decode tool */
  function renderDecoder() {
    var text = decoderInput.value;
    var steps = decodeText(text, decoderLang);
    decoderSequence.innerHTML = '';
    if (!text.trim()) {
      decoderSequence.innerHTML = '<div class="decode-empty">Type a word above to see its chords.</div>';
      return;
    }
    var seq = 0;
    for (var s of steps) {
      if (s.type === 'chord') {
        seq++;
        var cell = document.createElement('div');
        cell.className = 'decode-chip';
        var dots = '';
        for (var d = 1; d <= 6; d++) {
          dots += '<span class="mini-dot' + (s.dots.indexOf(d) >= 0 ? ' active' : '') + '"></span>';
        }
        cell.innerHTML =
          '<span class="decode-step">' + seq + '</span>' +
          '<span class="decode-char" data-bangla="' + (/[\u0980-\u09FF]/.test(s.char) ? '1' : '0') + '">' + escapeHTML(s.char) + '</span>' +
          '<span class="mini-dots">' + dots + '</span>' +
          '<span class="decode-dots">Dots ' + s.dots.join(',') + '</span>' +
          (s.shift ? '<span class="decode-shift">Shift</span>' : '');
        decoderSequence.appendChild(cell);
      } else if (s.type === 'space') {
        seq++;
        var sp = document.createElement('div');
        sp.className = 'decode-chip decode-space';
        sp.innerHTML = '<span class="decode-step">' + seq + '</span><span class="decode-dots">SPACE key</span>';
        decoderSequence.appendChild(sp);
      } else if (s.type === 'newline') {
        // no newline chord on the device — skip silently
      } else {
        var un = document.createElement('div');
        un.className = 'decode-chip decode-unknown';
        un.innerHTML = '<span class="decode-char" data-bangla="' + (/[\u0980-\u09FF]/.test(s.char) ? '1' : '0') + '">' + escapeHTML(s.char) + '</span><span class="decode-dots">not on this keyboard</span>';
        decoderSequence.appendChild(un);
      }
    }
    if (seq === 0) {
      decoderSequence.innerHTML = '<div class="decode-empty">Nothing in this text can be typed on the device.</div>';
    }
  }
  function escapeHTML(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  $('decoderGenerate').addEventListener('click', renderDecoder);
  decoderInput.addEventListener('keydown', function (e) { if (e.key === 'Enter') renderDecoder(); });
  var decoderBtns = $('decoderLangToggle').querySelectorAll('.learn-lang-btn');
  decoderBtns.forEach(function (b) {
    b.addEventListener('click', function () {
      decoderBtns.forEach(function (x) { x.classList.remove('active'); });
      b.classList.add('active');
      decoderLang = b.dataset.lang;
      store.set('braillebridge-decoder-lang', decoderLang);
      renderDecoder();
    });
  });
  // Restore the trainer language toggle before the first render.
  var savedDecoderLang = store.get('braillebridge-decoder-lang', '');
  if (savedDecoderLang === 'en' || savedDecoderLang === 'bn') {
    decoderBtns.forEach(function (x) { x.classList.toggle('active', x.dataset.lang === savedDecoderLang); });
    decoderLang = savedDecoderLang;
  }
  restoreWords();
  renderDecoder();
})();
