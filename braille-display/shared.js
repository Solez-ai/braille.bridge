/* ============================================================
   BrailleBridge — shared.js
   Teacher Account UI · Google Translate bridge · Log Auto-Formatter
   · Exports library (saved + reviewable exports)

   Loaded by BOTH apps:
     - braille-desktop / braille-display  (teacher platform)
     - website                            (showcase site, demo exports)

   Exposes globals: BBTranslate, BBAutoFormat, BBExports, BBAccount
   Everything is self-contained — no dependencies on script.js.
   ============================================================ */
(function () {
  'use strict';

  /* ============================================================
     1. GOOGLE TRANSLATE BRIDGE - ALL LANGUAGES
     Uses the public translate_a/single endpoint (gtx client) with a
     v2 fallback. Source language is auto-detected by the API (sl=auto)
     and reported back so the UI can show "Bangla -> Spanish" etc.
     The full Google Translate catalogue is supported: every language
     Google Translate offers (~110+ codes).
     ============================================================ */
  const BBTranslate = {
    cache: new Map(),

    // Full Google Translate catalogue: [code, English name, flag country code].
    // Flag emoji are generated from the 2-letter country code at runtime.
    // 'auto' first, then English + Bangla (primary audience), then the rest.
    LANGUAGES: [
      ['auto', 'Detect language', ''],
      ['en', 'English', 'GB'],
      ['bn', 'Bangla', 'BD'],
      ['af', 'Afrikaans', 'ZA'],
      ['sq', 'Albanian', 'AL'],
      ['am', 'Amharic', 'ET'],
      ['ar', 'Arabic', 'SA'],
      ['hy', 'Armenian', 'AM'],
      ['as', 'Assamese', 'IN'],
      ['ay', 'Aymara', 'BO'],
      ['az', 'Azerbaijani', 'AZ'],
      ['bm', 'Bambara', 'ML'],
      ['eu', 'Basque', 'ES'],
      ['be', 'Belarusian', 'BY'],
      ['bho', 'Bhojpuri', 'IN'],
      ['bs', 'Bosnian', 'BA'],
      ['bg', 'Bulgarian', 'BG'],
      ['ca', 'Catalan', 'ES'],
      ['ceb', 'Cebuano', 'PH'],
      ['ny', 'Chichewa', 'MW'],
      ['zh-CN', 'Chinese (Simplified)', 'CN'],
      ['zh-TW', 'Chinese (Traditional)', 'TW'],
      ['co', 'Corsican', 'FR'],
      ['hr', 'Croatian', 'HR'],
      ['cs', 'Czech', 'CZ'],
      ['da', 'Danish', 'DK'],
      ['dv', 'Dhivehi', 'MV'],
      ['nl', 'Dutch', 'NL'],
      ['eo', 'Esperanto', ''],
      ['et', 'Estonian', 'EE'],
      ['ee', 'Ewe', 'GH'],
      ['fil', 'Filipino', 'PH'],
      ['fi', 'Finnish', 'FI'],
      ['fr', 'French', 'FR'],
      ['fy', 'Frisian', 'NL'],
      ['gl', 'Galician', 'ES'],
      ['ka', 'Georgian', 'GE'],
      ['de', 'German', 'DE'],
      ['el', 'Greek', 'GR'],
      ['gn', 'Guarani', 'PY'],
      ['gu', 'Gujarati', 'IN'],
      ['ht', 'Haitian Creole', 'HT'],
      ['ha', 'Hausa', 'NG'],
      ['haw', 'Hawaiian', ''],
      ['iw', 'Hebrew', 'IL'],
      ['hi', 'Hindi', 'IN'],
      ['hmn', 'Hmong', ''],
      ['hu', 'Hungarian', 'HU'],
      ['is', 'Icelandic', 'IS'],
      ['ig', 'Igbo', 'NG'],
      ['id', 'Indonesian', 'ID'],
      ['ga', 'Irish', 'IE'],
      ['it', 'Italian', 'IT'],
      ['ja', 'Japanese', 'JP'],
      ['jv', 'Javanese', 'ID'],
      ['kn', 'Kannada', 'IN'],
      ['kk', 'Kazakh', 'KZ'],
      ['km', 'Khmer', 'KH'],
      ['rw', 'Kinyarwanda', 'RW'],
      ['gom', 'Konkani', 'IN'],
      ['ko', 'Korean', 'KR'],
      ['krio', 'Krio', 'SL'],
      ['ku', 'Kurdish (Kurmanji)', 'TR'],
      ['ckb', 'Kurdish (Sorani)', 'IQ'],
      ['ky', 'Kyrgyz', 'KG'],
      ['lo', 'Lao', 'LA'],
      ['la', 'Latin', ''],
      ['lv', 'Latvian', 'LV'],
      ['ln', 'Lingala', 'CD'],
      ['lt', 'Lithuanian', 'LT'],
      ['lg', 'Luganda', 'UG'],
      ['lb', 'Luxembourgish', 'LU'],
      ['mk', 'Macedonian', 'MK'],
      ['mg', 'Malagasy', 'MG'],
      ['ms', 'Malay', 'MY'],
      ['ml', 'Malayalam', 'IN'],
      ['mt', 'Maltese', 'MT'],
      ['mi', 'Maori', 'NZ'],
      ['mr', 'Marathi', 'IN'],
      ['mn', 'Mongolian', 'MN'],
      ['my', 'Myanmar (Burmese)', 'MM'],
      ['ne', 'Nepali', 'NP'],
      ['no', 'Norwegian', 'NO'],
      ['or', 'Odia (Oriya)', 'IN'],
      ['om', 'Oromo', 'ET'],
      ['ps', 'Pashto', 'AF'],
      ['fa', 'Persian', 'IR'],
      ['pl', 'Polish', 'PL'],
      ['pt', 'Portuguese', 'PT'],
      ['pa', 'Punjabi', 'IN'],
      ['ro', 'Romanian', 'RO'],
      ['ru', 'Russian', 'RU'],
      ['sm', 'Samoan', 'WS'],
      ['sa', 'Sanskrit', 'IN'],
      ['gd', 'Scots Gaelic', 'GB'],
      ['nso', 'Sepedi', 'ZA'],
      ['sr', 'Serbian', 'RS'],
      ['st', 'Sesotho', 'ZA'],
      ['sn', 'Shona', 'ZW'],
      ['sd', 'Sindhi', 'PK'],
      ['si', 'Sinhala', 'LK'],
      ['sk', 'Slovak', 'SK'],
      ['sl', 'Slovenian', 'SI'],
      ['so', 'Somali', 'SO'],
      ['es', 'Spanish', 'ES'],
      ['su', 'Sundanese', 'ID'],
      ['sw', 'Swahili', 'KE'],
      ['sv', 'Swedish', 'SE'],
      ['tg', 'Tajik', 'TJ'],
      ['ta', 'Tamil', 'IN'],
      ['tt', 'Tatar', 'RU'],
      ['te', 'Telugu', 'IN'],
      ['th', 'Thai', 'TH'],
      ['ti', 'Tigrinya', 'ET'],
      ['ts', 'Tsonga', 'ZA'],
      ['tr', 'Turkish', 'TR'],
      ['tk', 'Turkmen', 'TM'],
      ['ak', 'Twi', 'GH'],
      ['uk', 'Ukrainian', 'UA'],
      ['ur', 'Urdu', 'PK'],
      ['ug', 'Uyghur', 'CN'],
      ['uz', 'Uzbek', 'UZ'],
      ['vi', 'Vietnamese', 'VN'],
      ['cy', 'Welsh', 'GB'],
      ['xh', 'Xhosa', 'ZA'],
      ['yi', 'Yiddish', ''],
      ['yo', 'Yoruba', 'NG'],
      ['zu', 'Zulu', 'ZA']
    ],

    // Regional-indicator flag emoji from a 2-letter country code
    flag(cc) {
      if (!cc || cc.length !== 2) return '\uD83C\uDF10'; // globe for world languages
      const A = 0x1F1E6;
      const up = cc.toUpperCase();
      return String.fromCodePoint(A + up.charCodeAt(0) - 65, A + up.charCodeAt(1) - 65);
    },

    name(code) {
      const l = this.LANGUAGES.find(x => x[0] === code);
      return l ? l[1] : code;
    },

    label(code) {
      const l = this.LANGUAGES.find(x => x[0] === code);
      return l ? (l[2] ? this.flag(l[2]) + ' ' + l[1] : l[1]) : code;
    },

    // innerHTML for a <select> that picks a target language
    optionsHTML(selected) {
      return this.LANGUAGES.map(l =>
        '<option value="' + l[0] + '"' + (l[0] === selected ? ' selected' : '') + '>' +
        (l[2] ? this.flag(l[2]) + ' ' : '') + l[1] +
        '</option>').join('');
    },

    hasBengali(text) {
      return /[\u0980-\u09FF]/.test(text);
    },

    // Best-effort local source-language guess (Google's own detection,
    // returned as res.detected, always takes precedence when available).
    detectLanguage(text) {
      if (!text) return null;
      if (this.hasBengali(text)) return 'bn';
      if (/[\u0400-\u04FF]/.test(text)) return 'ru';
      if (/[\u0600-\u06FF]/.test(text)) return 'ar';
      if (/[\u4E00-\u9FFF]/.test(text)) return 'zh-CN';
      if (/[\u3040-\u30FF]/.test(text)) return 'ja';
      if (/[\uAC00-\uD7AF]/.test(text)) return 'ko';
      if (/[\u0900-\u097F]/.test(text)) return 'hi';
      if (/[\u0E00-\u0E7F]/.test(text)) return 'th';
      if (/[\u0590-\u05FF]/.test(text)) return 'he';
      if (/[\u0370-\u03FF]/.test(text)) return 'el';
      return 'en';
    },

    // translate(text, target[, source]) -> { ok, text, detected } |
    //                                        { ok: false, error }
    // source 'auto' (default) lets Google detect; the detected code comes
    // back in .detected so the UI can show "Bangla -> French".
    // Results are cached per (source, target, text).
    async translate(text, target, source) {
      const trimmed = (text || '').trim();
      if (!trimmed) return { ok: false, text: '', error: 'nothing to translate' };
      const src = source || 'auto';
      const key = src + '>' + target + '::' + trimmed;
      if (this.cache.has(key)) return this.cache.get(key);

      const done = (out, detected) => {
        const r = { ok: true, text: out, detected: detected || null };
        this.cache.set(key, r);
        return r;
      };

      // Primary: gtx single endpoint (no key needed, generous limits).
      // data[2] is the detected source language code when sl=auto.
      try {
        const url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=' +
          encodeURIComponent(src) + '&tl=' + encodeURIComponent(target) +
          '&dt=t&q=' + encodeURIComponent(trimmed);
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && Array.isArray(data[0])) {
            const out = data[0].map(seg => (seg && seg[0]) || '').join('');
            if (out) return done(out, typeof data[2] === 'string' ? data[2] : null);
          }
        }
      } catch (e) { /* fall through to v2 */ }

      // Fallback: simple v2 endpoint
      try {
        const url2 = 'https://translate.googleapis.com/language/translate/v2?target=' +
          encodeURIComponent(target) +
          (src !== 'auto' ? '&source=' + encodeURIComponent(src) : '') +
          '&q=' + encodeURIComponent(trimmed);
        const res2 = await fetch(url2);
        if (res2.ok) {
          const j = await res2.json();
          const t = j && j.data && j.data.translations && j.data.translations[0];
          if (t && t.translatedText) return done(t.translatedText, t.detectedSourceLanguage || null);
        }
      } catch (e) { /* ignore */ }

      return { ok: false, text: '', error: 'Translation unavailable (offline?)' };
    }
  };

  /* ============================================================
     2. AUTO-FORMATTER
     Understands what the student typed and turns the raw character
     stream into structured, reviewable documents:
       titles · headings (Chapter/Section/Lesson/Exercise + Bangla)
       paragraphs (sentence spacing) · bullet lists · numbered lists
       per-line timestamps preserved from the original typing session
     ============================================================ */
  const BBAutoFormat = {

    // Split a raw char stream (with optional {char, time} entries) into
    // logical lines. Returns [{ text, time }] — time = first char typed.
    toLines(chars) {
      const lines = [];
      let cur = '', curTime = null;
      const push = () => {
        const t = cur.replace(/\u00a0/g, ' ').replace(/[ \t]+$/g, '');
        if (t !== '') lines.push({ text: t, time: curTime });
        cur = ''; curTime = null;
      };
      for (const entry of (chars || [])) {
        const isObj = entry && typeof entry === 'object';
        const ch = isObj ? entry.char : entry;
        if (ch === undefined || ch === null) continue;
        if (ch === ' ') {
          // collapse runs of spaces into one word boundary
          if (cur !== '' && !cur.endsWith(' ')) cur += ' ';
          continue;
        }
        if (ch === '\n' || ch === '\r') { push(); continue; }
        if (cur === '') curTime = (isObj && entry.time) || Date.now();
        cur += ch;
      }
      push();
      return lines;
    },

    // Detect heading level from the words on a line.
    headingLevel(text) {
      const t = text.trim();
      if (/^(chapter|অধ্যায়)\b/i.test(t)) return 1;
      if (/^(section|অনুচ্ছেদ)\b/i.test(t)) return 2;
      if (/^(lesson|পাঠ)\b/i.test(t)) return 3;
      if (/^(exercise|অনুশীলন|question|প্রশ্ন)\b/i.test(t)) return 4;
      return 0;
    },

    looksLikeTitle(line, isFirst, total) {
      if (!isFirst || total < 2) return false;
      const t = line.text.trim();
      if (t.length === 0 || t.length > 60) return false;
      if (t.split(/\s+/).length > 6) return false;
      if (/[.,;:!?।]$/.test(t)) return false; // titles don't end with punctuation
      return true;
    },

    // Fix sentence spacing + punctuation positioning inside one line.
    fixPunctuation(text) {
      let t = text.replace(/\u00a0/g, ' ');
      t = t.replace(/ +([.,;:!?।])/g, '$1');        // no space BEFORE punctuation
      t = t.replace(/([.,;:!?।])(?=[^\s\d.,;:!?।])/g, '$1 '); // one space AFTER
      t = t.replace(/\.{4,}/g, '...');               // normalize ellipses
      t = t.replace(/ {2,}/g, ' ');
      return t.trim();
    },

    // Main entry: raw chars -> structured blocks
    // blocks: { type: 'title'|'heading'|'para'|'bullet'|'numbered', text, time, level }
    format(chars) {
      const rawLines = this.toLines(chars);
      const blocks = [];

      // Paragraphs: group consecutive lines; a blank gap (no way to know from
      // char stream) or heading keyword starts a new block. Bullets/numbers
      // start list items.
      let para = null; // { lines: [{text,time}] }
      const flushPara = () => {
        if (!para || !para.lines.length) { para = null; return; }
        const joined = para.lines.map(l => l.text.trim()).join(' ');
        const text = this.fixPunctuation(joined);
        blocks.push({ type: 'para', text, time: para.lines[0].time });
        para = null;
      };

      rawLines.forEach((line, idx) => {
        const t = line.text.trim();
        if (!t) { flushPara(); return; }

        const bullet = /^[-*•·→]\s+/.test(t);
        const numbered = /^\d+[.)]\s+/.test(t);
        const head = this.headingLevel(t);

        if (bullet || numbered) {
          flushPara();
          blocks.push({
            type: bullet ? 'bullet' : 'numbered',
            text: this.fixPunctuation(t.replace(/^([-*•·→]|\d+[.)])\s+/, '')),
            time: line.time
          });
          return;
        }
        if (head) {
          flushPara();
          blocks.push({ type: 'heading', level: head, text: this.fixPunctuation(t), time: line.time });
          return;
        }
        if (!para) para = { lines: [] };
        para.lines.push(line);
        // A line ending a sentence hard > 80 chars naturally wraps; we keep
        // flowing unless the NEXT line starts a new construct.
        if (idx === rawLines.length - 1) flushPara();
      });
      flushPara();

      // Title detection: very first block if it looks like one
      const first = blocks.find(b => b.type === 'para' || b.type === 'heading');
      if (first && first.type === 'para' && this.looksLikeTitle({ text: first.text }, true, blocks.length)) {
        first.type = 'title';
      }
      return blocks;
    },

    // Render blocks into a container (used by review modal)
    render(blocks, container, withTranslate) {
      container.innerHTML = '';
      if (!blocks.length) {
        container.innerHTML = '<div class="bb-empty">Nothing to format yet.</div>';
        return;
      }
      for (const b of blocks) {
        const tag = (b.type === 'bullet' || b.type === 'numbered') ? 'div'
          : b.type === 'title' ? 'h2'
          : b.type === 'heading' ? 'h' + (b.level || 3)
          : 'p';
        const el = document.createElement(tag);
        el.className = 'fmt-' + b.type + (b.type === 'heading' ? ' fmt-h' + b.level : '');
        el.textContent = (b.type === 'bullet' ? '• ' : '') + b.text;
        if (b.time) {
          const ts = document.createElement('span');
          ts.className = 'fmt-ts';
          ts.textContent = new Date(b.time).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
          el.appendChild(ts);
        }
        container.appendChild(el);
      }
      if (withTranslate) {
        const bar = document.createElement('div');
        bar.className = 'fmt-translate-bar';
        container.insertBefore(bar, container.firstChild);
      }
    },

    // Blocks -> clean plain text (for .txt downloads)
    toText(blocks) {
      const out = [];
      let n = 0;
      for (const b of blocks) {
        if (b.type === 'title') { out.push(b.text.toUpperCase(), ''); n = 0; }
        else if (b.type === 'heading') { out.push('', b.text, ''); n = 0; }
        else if (b.type === 'bullet') out.push('• ' + b.text);
        else if (b.type === 'numbered') { n += 1; out.push(n + '. ' + b.text); }
        else { out.push(b.text, ''); n = 0; }
      }
      return out.join('\n').replace(/\n{3,}/g, '\n\n').trim() + '\n';
    }
  };

  /* ============================================================
     3. EXPORTS LIBRARY
     "Save to Exports" persists every export (student log, class log,
     demo session) into localStorage. The teacher opens the Exports
     tab later to review formatted documents, translate them, and
     re-download — a proper archive instead of loose .txt files.
     ============================================================ */
  const STORE_KEY = window.location.pathname.indexOf('website') >= 0
    ? 'bb-site-exports-v1' : 'bb-exports-v1';

  function loadExports() {
    try { return JSON.parse(localStorage.getItem(STORE_KEY) || '[]'); }
    catch (e) { return []; }
  }
  function persistExports(list) {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(list)); return true; }
    catch (e) { return false; }
  }

  const BBExports = {
    list: loadExports(),
    viewing: null, // id of export under review

    all() { return this.list; },

    save(payload) {
      // payload: { title, student, mode, source, chars, charsCount, stats }
      const blocks = BBAutoFormat.format(payload.chars || []);
      const doc = {
        id: 'ex_' + Date.now() + '_' + Math.floor(Math.random() * 1e4),
        title: payload.title || 'Untitled Export',
        student: payload.student || null,
        mode: payload.mode || 'Unknown',
        source: payload.source || 'log',
        charsCount: typeof payload.charsCount === 'number'
          ? payload.charsCount : (payload.chars || []).length,
        stats: payload.stats || null,
        blocks,
        created: Date.now()
      };
      this.list.unshift(doc);
      if (this.list.length > 100) this.list.length = 100; // archive cap
      persistExports(this.list);
      if (this._modalVisible) this.render();
      return doc.id;
    },

    // Convenience wrappers used by script.js
    saveFromStudent(student, mode) {
      const readable = (typeof buildReadableLog === 'function')
        ? buildReadableLog(student.chars).map(l => ({
            char: ' ', time: l.time, _line: l.text
          })) : null;
      // buildReadableLog joins words per line — feed the formatter line by
      // line by re-splitting into word chars while keeping the line time.
      let chars;
      if (readable) {
        chars = [];
        for (const l of readable) {
          for (const w of l._line.split(' ')) {
            for (const ch of w) chars.push({ char: ch, time: l.time });
            chars.push({ char: ' ', time: l.time });
          }
        }
      } else {
        chars = student.chars;
      }
      return this.save({
        title: student.name + ' — Session Log',
        student: { name: student.name, conn: student.connType, baud: student.baud },
        mode: mode || 'Teacher App',
        source: 'student',
        chars,
        charsCount: student.chars.length
      });
    },

    saveClass(studentsArr, totalChars, mode) {
      let chars = [];
      for (const s of studentsArr) {
        chars.push({ char: ' ', time: Date.now() }); // paragraph separators
        chars = chars.concat(s.chars);
      }
      return this.save({
        title: 'Class Export — ' + studentsArr.length + ' student' + (studentsArr.length === 1 ? '' : 's'),
        student: null,
        mode: mode || 'Teacher App',
        source: 'class',
        chars,
        charsCount: typeof totalChars === 'number' ? totalChars : chars.length,
        stats: { students: studentsArr.length }
      });
    },

    remove(id) {
      this.list = this.list.filter(e => e.id !== id);
      persistExports(this.list);
      this.render();
    },

    clearAll() {
      this.list = [];
      persistExports(this.list);
      this.render();
    },

    /* ---------------- Modal UI ---------------- */
    _modalVisible: false,

    ensureModals() {
      if (document.getElementById('bbExportsModal')) return;

      // ---- Exports modal ----
      const wrap = document.createElement('div');
      wrap.className = 'bb-modal-overlay';
      wrap.id = 'bbExportsModal';
      wrap.innerHTML = `
        <div class="bb-modal bb-modal-wide">
          <div class="bb-modal-head">
            <div class="bb-modal-title">
              <span class="bb-modal-icon"><i class="fa-solid fa-file-export"></i></span>
              <div>
                <div class="bb-modal-name">Exports</div>
                <div class="bb-modal-sub" id="bbExportsSub">Saved export documents — review, translate, download</div>
              </div>
            </div>
            <div class="bb-modal-actions">
              <button class="bb-btn-ghost" id="bbExportsClear" title="Delete all exports"><i class="fa-solid fa-trash-can"></i> Clear</button>
              <button class="bb-icon-btn" id="bbExportsClose" title="Close (Esc)"><i class="fa-solid fa-xmark"></i></button>
            </div>
          </div>
          <div class="bb-modal-body" id="bbExportsBody"></div>
          <div class="bb-modal-foot" id="bbExportsFoot"></div>
        </div>`;
      document.body.appendChild(wrap);

      // ---- Account modal ----
      const acc = document.createElement('div');
      acc.className = 'bb-modal-overlay';
      acc.id = 'bbAccountModal';
      acc.innerHTML = `
        <div class="bb-modal bb-modal-account">
          <div class="bb-acc-banner">
            <div class="bb-acc-banner-pattern" aria-hidden="true"></div>
            <button class="bb-icon-btn bb-acc-close" id="bbAccountClose" title="Close (Esc)"><i class="fa-solid fa-xmark"></i></button>
            <div class="bb-acc-avatar">SY</div>
          </div>
          <div class="bb-acc-head">
            <div class="bb-acc-name-row">
              <span class="bb-acc-name">Samin Yeasar</span>
              <span class="bb-acc-verified" title="Verified teacher account"><i class="fa-solid fa-circle-check"></i></span>
            </div>
            <div class="bb-acc-role">Teacher · Braille Literacy</div>
            <div class="bb-acc-badges">
              <span class="bb-badge bb-badge-gold"><i class="fa-solid fa-id-badge"></i> BB-T-0001</span>
              <span class="bb-badge"><i class="fa-solid fa-shield-halved"></i> Verified account</span>
              <span class="bb-badge"><i class="fa-solid fa-lock"></i> Local profile</span>
            </div>
          </div>
          <div class="bb-acc-stats">
            <div class="bb-acc-stat"><strong id="bbAccStatStudents">0</strong><span>Students</span></div>
            <div class="bb-acc-stat"><strong id="bbAccStatExports">0</strong><span>Exports</span></div>
            <div class="bb-acc-stat"><strong id="bbAccStatChars">0</strong><span>Characters</span></div>
          </div>
          <div class="bb-acc-rows">
            <div class="bb-acc-row"><i class="fa-regular fa-envelope"></i><span>samin.yeasar@braillebridge.edu</span></div>
            <div class="bb-acc-row"><i class="fa-solid fa-school"></i><span>Special Education — BrailleBridge Academy</span></div>
            <div class="bb-acc-row"><i class="fa-solid fa-language"></i><span>English · বাংলা · Google Translate enabled</span></div>
            <div class="bb-acc-row"><i class="fa-regular fa-calendar-check"></i><span>Member since 2026 · Device owner</span></div>
          </div>
          <div class="bb-acc-actions">
            <button class="bb-btn-gold" id="bbAccountSignout"><i class="fa-solid fa-arrow-right-from-bracket"></i> Sign out</button>
            <button class="bb-btn-ghost" id="bbAccountDone">Close</button>
          </div>
        </div>`;
      document.body.appendChild(acc);

      // wire closers
      wrap.addEventListener('click', e => { if (e.target === wrap) this.closeModal(); });
      acc.addEventListener('click', e => { if (e.target === acc) this.closeAccount(); });
      wrap.querySelector('#bbExportsClose').addEventListener('click', () => this.closeModal());
      acc.querySelector('#bbAccountClose').addEventListener('click', () => this.closeAccount());
      acc.querySelector('#bbAccountDone').addEventListener('click', () => this.closeAccount());
      acc.querySelector('#bbAccountSignout').addEventListener('click', () => {
        this.toast('Signed out of this session (demo account stays active).');
        this.closeAccount();
      });
      wrap.querySelector('#bbExportsClear').addEventListener('click', () => {
        if (this.list.length && confirm('Delete ALL saved exports? This cannot be undone.')) this.clearAll();
      });

      document.addEventListener('keydown', e => {
        if (e.key !== 'Escape') return;
        if (this._modalVisible) this.closeModal();
        if (this._accountVisible) this.closeAccount();
      });
    },

    _accountVisible: false,

    openAccount() {
      this.ensureModals();
      // Live stats from whatever the host app exposes. script.js declares
      // `students` with let (global lexical, not on window) — probe via typeof.
      try {
        let roster = null, totalChars = null;
        try { if (typeof students !== 'undefined' && Array.isArray(students)) roster = students; } catch (e) {}
        try { if (typeof totalCharsAllStudents !== 'undefined') totalChars = totalCharsAllStudents; } catch (e) {}
        if (roster) {
          document.getElementById('bbAccStatStudents').textContent = roster.length;
          document.getElementById('bbAccStatChars').textContent =
            (typeof totalChars === 'number') ? totalChars : 0;
        } else {
          document.getElementById('bbAccStatStudents').textContent = '—';
          document.getElementById('bbAccStatChars').textContent = '—';
        }
        document.getElementById('bbAccStatExports').textContent = this.list.length;
      } catch (e) { /* ignore */ }
      document.getElementById('bbAccountModal').classList.add('visible');
      document.body.style.overflow = 'hidden';
      this._accountVisible = true;
    },

    closeAccount() {
      document.getElementById('bbAccountModal').classList.remove('visible');
      document.body.style.overflow = '';
      this._accountVisible = false;
    },

    openModal() {
      this.ensureModals();
      this.viewing = null;
      document.getElementById('bbExportsModal').classList.add('visible');
      document.body.style.overflow = 'hidden';
      this._modalVisible = true;
      this.render();
    },

    closeModal() {
      document.getElementById('bbExportsModal').classList.remove('visible');
      document.body.style.overflow = '';
      this._modalVisible = false;
      this.viewing = null;
    },

    fmtDate(ts) {
      return new Date(ts).toLocaleString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric',
        hour: '2-digit', minute: '2-digit', hour12: false
      });
    },

    render() {
      const body = document.getElementById('bbExportsBody');
      const foot = document.getElementById('bbExportsFoot');
      const sub = document.getElementById('bbExportsSub');
      if (!body) return;

      if (this.viewing !== null) { this.renderReview(); return; }

      sub.textContent = 'Saved export documents — review, translate, download';
      if (!this.list.length) {
        body.innerHTML = `
          <div class="bb-empty">
            <i class="fa-regular fa-folder-open"></i>
            <h4>No exports yet</h4>
            <p>Use <strong>Export All</strong> or a student's <strong>Export</strong> button —<br>every export is saved here automatically for review.</p>
          </div>`;
        foot.innerHTML = '<span class="bb-foot-info">0 saved exports</span>';
        return;
      }

      body.innerHTML = '';
      for (const ex of this.list) {
        const card = document.createElement('div');
        card.className = 'bb-export-card';
        const icon = ex.source === 'class' ? 'fa-users'
          : ex.source === 'demo' ? 'fa-flask' : 'fa-user';
        const head = document.createElement('div');
        head.className = 'bb-export-head';
        head.innerHTML = `
          <span class="bb-export-icon"><i class="fa-solid ${icon}"></i></span>
          <div class="bb-export-meta">
            <div class="bb-export-title"></div>
            <div class="bb-export-sub">${this.fmtDate(ex.created)} · ${ex.mode} · ${ex.charsCount} chars${ex.student ? ' · ' + ex.student.conn.toUpperCase() + ' @ ' + ex.student.baud : ''}</div>
          </div>
          <span class="bb-badge bb-badge-soft">${ex.blocks.length} block${ex.blocks.length === 1 ? '' : 's'}</span>`;
        head.querySelector('.bb-export-title').textContent = ex.title;
        const actions = document.createElement('div');
        actions.className = 'bb-export-actions';
        actions.innerHTML = `
          <button class="bb-btn-ghost" data-act="review"><i class="fa-solid fa-file-lines"></i> Review</button>
          <button class="bb-btn-ghost" data-act="dl"><i class="fa-solid fa-download"></i> .txt</button>
          <button class="bb-icon-btn" data-act="del" title="Delete"><i class="fa-solid fa-trash-can"></i></button>`;
        card.appendChild(head);
        card.appendChild(actions);

        actions.querySelector('[data-act="review"]').addEventListener('click', () => { this.viewing = ex.id; this.render(); });
        actions.querySelector('[data-act="dl"]').addEventListener('click', () => this.download(ex));
        actions.querySelector('[data-act="del"]').addEventListener('click', () => this.remove(ex.id));

        body.appendChild(card);
      }
      foot.innerHTML = `<span class="bb-foot-info">${this.list.length} saved export${this.list.length === 1 ? '' : 's'} · stored locally on this device</span>`;
    },

    renderReview() {
      const ex = this.list.find(e => e.id === this.viewing);
      if (!ex) { this.viewing = null; this.render(); return; }
      const body = document.getElementById('bbExportsBody');
      const foot = document.getElementById('bbExportsFoot');
      const sub = document.getElementById('bbExportsSub');

      sub.textContent = 'Review — auto-formatted document';
      body.innerHTML = '';

      const bar = document.createElement('div');
      bar.className = 'bb-review-bar';
      bar.innerHTML = `
        <button class="bb-btn-ghost" id="bbReviewBack"><i class="fa-solid fa-arrow-left"></i> Back</button>
        <div class="bb-review-tools">
          <select class="bb-lang-select" id="bbReviewLang" title="Translate into any Google Translate language">${BBTranslate.optionsHTML('en')}</select>
          <button class="bb-btn-ghost" id="bbReviewTranslate"><i class="fa-solid fa-language"></i> <span id="bbReviewTranslateLbl">Translate</span></button>
          <button class="bb-btn-ghost" id="bbReviewShowOrig" style="display:none;"><i class="fa-solid fa-rotate-left"></i> Show original</button>
          <button class="bb-btn-ghost" id="bbReviewRaw"><i class="fa-solid fa-eye"></i> Raw</button>
          <button class="bb-btn-gold" id="bbReviewDl"><i class="fa-solid fa-download"></i> Download .txt</button>
        </div>`;
      body.appendChild(bar);

      const doc = document.createElement('div');
      doc.className = 'bb-review-doc';
      body.appendChild(doc);
      BBAutoFormat.render(ex.blocks, doc, false);

      let showingRaw = false;
      let currentBlocks = ex.blocks;   // what's on screen (original or translated)
      let originalBlocks = ex.blocks;  // untouched original

      bar.querySelector('#bbReviewBack').addEventListener('click', () => { this.viewing = null; this.render(); });
      bar.querySelector('#bbReviewDl').addEventListener('click', () => this.download(ex, currentBlocks === originalBlocks ? null : currentBlocks));
      const showBlocks = () => {
        if (showingRaw) {
          doc.classList.add('raw');
          doc.innerHTML = '<div class="bb-raw">' + currentBlocks.map(b =>
            '<span class="bb-raw-line">[' + (b.time ? new Date(b.time).toLocaleTimeString('en-US', { hour12: false }) : '--:--:--') + '] ' +
            (b.text || '').replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</span>').join('') + '</div>';
        } else {
          doc.classList.remove('raw');
          BBAutoFormat.render(currentBlocks, doc, false);
        }
      };
      bar.querySelector('#bbReviewRaw').addEventListener('click', () => { showingRaw = !showingRaw; showBlocks(); });

      // ---- Translate into ANY of the 128 catalogue languages ----
      const showOrigBtn = bar.querySelector('#bbReviewShowOrig');
      bar.querySelector('#bbReviewTranslate').addEventListener('click', async () => {
        const lbl = document.getElementById('bbReviewTranslateLbl');
        const sel = document.getElementById('bbReviewLang');
        const target = sel.value;
        if (!currentBlocks.length) return;
        lbl.textContent = 'Translating…';
        sel.disabled = true;
        const texts = currentBlocks.map(b => b.text);
        const joined = texts.join('\n\u241F\n'); // segment separator preserved by translator
        const res = await BBTranslate.translate(joined, target);
        sel.disabled = false;
        if (res.ok) {
          const parts = res.text.split('\u241F');
          currentBlocks = currentBlocks.map((b, i) => ({ ...b, text: (parts[i] || b.text).trim() }));
          const detected = res.detected ? BBTranslate.name(res.detected) : null;
          lbl.textContent = detected ? (BBTranslate.name(target) + ' (from ' + detected + ')') : BBTranslate.name(target);
          showOrigBtn.style.display = '';
          showBlocks();
        } else {
          lbl.textContent = 'Translate failed';
          setTimeout(() => { lbl.textContent = 'Translate'; }, 2000);
        }
      });
      // Show original restores the untouched document
      showOrigBtn.addEventListener('click', () => {
        currentBlocks = originalBlocks;
        showOrigBtn.style.display = 'none';
        document.getElementById('bbReviewTranslateLbl').textContent = 'Translate';
        showBlocks();
      });

      foot.innerHTML = `<span class="bb-foot-info">${ex.title} · ${ex.charsCount} characters · formatted ${ex.blocks.length} blocks</span>`;
    },

    download(ex, blocksOverride) {
      const blocks = blocksOverride || ex.blocks;
      const header = [
        'BrailleBridge Export',
        '===================',
        `Title: ${ex.title}`,
        `Saved: ${this.fmtDate(ex.created)}`,
        `Mode: ${ex.mode}`,
        ex.student ? `Student: ${ex.student.name} (${ex.student.conn.toUpperCase()} @ ${ex.student.baud} baud)` : 'Class export',
        `Characters: ${ex.charsCount}`,
        'Auto-formatted by BrailleBridge Auto-Formatter',
        '===================',
        ''
      ].join('\n');
      const content = header + BBAutoFormat.toText(blocks);
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = ex.title.replace(/[^\w\u0980-\u09FF]+/g, '_').slice(0, 60) + '_export.txt';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    },

    toast(msg) {
      let t = document.getElementById('bbToast');
      if (!t) {
        t = document.createElement('div');
        t.id = 'bbToast';
        t.className = 'bb-toast';
        document.body.appendChild(t);
      }
      t.textContent = msg;
      t.classList.add('visible');
      clearTimeout(this._toastTimer);
      this._toastTimer = setTimeout(() => t.classList.remove('visible'), 2600);
    }
  };

  /* ============================================================
     4. ACCOUNT ENTRY POINTS
     The host page provides a trigger element (#accountChip or
     #siteAccountChip); shared.js wires it to the modal.
     ============================================================ */
  function init() {
    BBExports.ensureModals();
    const chip = document.getElementById('accountChip') || document.getElementById('siteAccountChip');
    if (chip) chip.addEventListener('click', () => BBExports.openAccount());
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();

  window.BBTranslate = BBTranslate;
  window.BBAutoFormat = BBAutoFormat;
  window.BBExports = BBExports;
  window.BBAccount = { open: () => BBExports.openAccount(), close: () => BBExports.closeAccount() };
})();
