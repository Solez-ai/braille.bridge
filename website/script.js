/* ============================================================
   BrailleBridge (b'bridge) — Interactive Website & Device Bridge
   - Firmware-accurate English + Bharati Braille translator
   - Web Bluetooth (BLE NUS) & Web Serial (115200 baud) device support
   - Apple-style hardware gallery, dictionary tabs & scroll reveals
   ============================================================ */
(function () {
  'use strict';

  const $ = (sel, ctx) => (ctx || document).querySelector(sel);
  const $$ = (sel, ctx) => Array.from((ctx || document).querySelectorAll(sel));
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ============================================================
     CLEVER WORDMARK & GOO BORDER LOADER -> HERO -> NAVBAR POP
     ============================================================ */
  function initSiteLoader() {
    const loader = $('#siteLoader');
    const borderEl = $('#loaderScreenBorder');
    const gooCanvas = $('#loaderGooCanvas');
    const dotEl = $('#loaderDot');

    if (!loader || !gooCanvas || !dotEl) {
      document.body.classList.remove('is-loading', 'nav-pending');
      return;
    }
    if (reducedMotion) {
      document.body.classList.remove('is-loading', 'nav-pending');
      loader.hidden = true;
      window.__startHeroAsciiIntro?.();
      return;
    }

    const ctx = gooCanvas.getContext('2d');
    const easeOutCubic = t => 1 - Math.pow(1 - t, 3);
    const easeInOutCubic = t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

    const BORDER_START = 950;
    const BORDER_HOLD_END = 1550;
    const SQUISH_END = 2650;
    const FADE_TEXT_AT = 3150;
    const REVEAL_HERO_AT = 3620;
    const CLEANUP_AT = 4300;

    let startTs = 0;
    let landed = false;
    let fadedText = false;
    let revealedHero = false;
    let navPopped = false;

    function popNavbar() {
      if (navPopped) return;
      navPopped = true;
      setTimeout(() => {
        document.body.classList.remove('nav-pending');
      }, 160);
    }

    window.__onHeroAsciiIntroDone = popNavbar;

    function syncCanvasSize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const w = window.innerWidth;
      const h = window.innerHeight;
      if (gooCanvas.width !== Math.round(w * dpr) || gooCanvas.height !== Math.round(h * dpr)) {
        gooCanvas.width = Math.round(w * dpr);
        gooCanvas.height = Math.round(h * dpr);
      }
      if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return { w, h };
    }

    function tickGoo(now) {
      if (!startTs) startTs = now;
      const elapsed = now - startTs;
      const { w, h } = syncCanvasSize();

      // Phase A: Screen-wide #FF7315 orange border forms around all 4 edges and holds cleanly
      if (elapsed >= BORDER_START && elapsed < BORDER_HOLD_END) {
        const growP = Math.min(1, (elapsed - BORDER_START) / 380);
        const thick = 16 * easeOutCubic(growP);
        if (borderEl) {
          borderEl.style.opacity = '1';
          borderEl.style.borderWidth = `${thick.toFixed(1)}px`;
        }
      } else if (elapsed >= BORDER_HOLD_END && elapsed < SQUISH_END) {
        // Phase B: Entire orange border detaches & squishes inward like goo into the Braille dot
        const p = easeInOutCubic((elapsed - BORDER_HOLD_END) / (SQUISH_END - BORDER_HOLD_END));
        if (borderEl) {
          borderEl.style.opacity = String(Math.max(0, 1 - p * 3.8));
        }

        if (ctx) {
          ctx.clearRect(0, 0, w, h);
          ctx.fillStyle = '#FF7315';

          const dr = dotEl.getBoundingClientRect();
          const tx = dr.left + dr.width / 2;
          const ty = dr.top + dr.height / 2;
          const tr = Math.max(6, dr.width * 0.42);

          // Shrinking outer goo frame collapsing toward (tx, ty)
          const frameShrink = Math.pow(p, 0.85);
          const left = tx * frameShrink;
          const top = ty * frameShrink;
          const right = w - (w - tx) * frameShrink;
          const bottom = h - (h - ty) * frameShrink;
          const strokeW = Math.max(4, 18 * (1 - p * 0.82));

          if (p < 0.85) {
            ctx.globalAlpha = Math.max(0, 1 - Math.max(0, p - 0.6) / 0.25);
            ctx.beginPath();
            ctx.rect(left, top, Math.max(0, right - left), Math.max(0, bottom - top));
            ctx.lineWidth = strokeW;
            ctx.strokeStyle = '#FF7315';
            ctx.stroke();
            ctx.globalAlpha = 1;
          }

          // 8 goo strands streaming from screen edges & corners into the dot center
          const sources = [
            [0, 0], [w * 0.5, 0], [w, 0],
            [w, h * 0.5], [w, h], [w * 0.5, h],
            [0, h], [0, h * 0.5]
          ];
          sources.forEach(([sx, sy], idx) => {
            const delay = (idx % 2) * 0.08;
            const sp = Math.max(0, Math.min(1, (p - delay) / (1 - delay)));
            const wobble = Math.sin(sp * Math.PI) * 24 * (idx % 2 === 0 ? 1 : -1);
            const cx = sx + (tx - sx) * sp + wobble * (1 - sp);
            const cy = sy + (ty - sy) * sp - wobble * (1 - sp);
            const blobR = Math.max(3, tr * (0.95 - sp * 0.45) + 8 * Math.sin(sp * Math.PI));

            ctx.beginPath();
            ctx.arc(cx, cy, blobR, 0, Math.PI * 2);
            ctx.fill();

            const spTail = Math.max(0, sp - 0.14);
            const lx = sx + (tx - sx) * spTail + wobble * 0.6 * (1 - spTail);
            const ly = sy + (ty - sy) * spTail - wobble * 0.6 * (1 - spTail);
            ctx.beginPath();
            ctx.arc(lx, ly, blobR * 0.62, 0, Math.PI * 2);
            ctx.fill();
          });

          // Central dot pool growing to exact target dot size
          const poolP = Math.max(0, (p - 0.32) / 0.68);
          const poolR = tr * Math.min(1.05, poolP * 1.15);
          if (poolR > 0.5) {
            ctx.beginPath();
            ctx.arc(tx, ty, poolR, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      } else if (elapsed >= SQUISH_END && !landed) {
        landed = true;
        if (borderEl) borderEl.style.opacity = '0';
        if (ctx) ctx.clearRect(0, 0, w, h);
        dotEl.classList.add('is-landed');
      }

      if (elapsed >= FADE_TEXT_AT && !fadedText) {
        fadedText = true;
        loader.classList.add('is-fading');
      }

      if (elapsed >= REVEAL_HERO_AT && !revealedHero) {
        revealedHero = true;
        document.body.classList.remove('is-loading');
        loader.classList.add('is-done');
        if (typeof window.__startHeroAsciiIntro === 'function') {
          window.__startHeroAsciiIntro();
        } else {
          popNavbar();
        }
      }

      if (elapsed >= CLEANUP_AT) {
        loader.hidden = true;
      }

      if (elapsed < CLEANUP_AT + 100) {
        requestAnimationFrame(tickGoo);
      }
    }
    requestAnimationFrame(tickGoo);
  }
  initSiteLoader();

  /* ============================================================
     BRAILLE DICTIONARIES — mirrored 100% from braile/braile.ino
     and braille-desktop/protocol.py (dot 1 = bit 0 ... dot 6 = bit 5)
     ============================================================ */
  const EN_DICT = {
    1: 'a', 3: 'b', 9: 'c', 25: 'd', 17: 'e', 11: 'f', 27: 'g', 19: 'h',
    8: 'i', 26: 'j', 5: 'k', 7: 'l', 13: 'm', 29: 'n', 21: 'o', 15: 'p',
    31: 'q', 23: 'r', 12: 's', 28: 't', 37: 'u', 39: 'v', 58: 'w', 45: 'x',
    61: 'y', 53: 'z'
  };
  // Also accept standard Grade-1 I/S/T/Z chords if typed on virtual pad
  const EN_FALLBACK = { 10: 'i', 14: 's', 30: 't', 41: 'z' };

  const BN_DICT = {
    1: 'অ', 28: 'আ', 10: 'ই', 20: 'ঈ', 37: 'উ', 51: 'ঊ', 17: 'এ', 12: 'ঐ', 21: 'ও', 42: 'ঔ',
    5: 'ক', 40: 'খ', 27: 'গ', 35: 'ঘ', 44: 'ঙ',
    9: 'চ', 33: 'ছ', 26: 'জ', 52: 'ঝ', 18: 'ঞ',
    62: 'ট', 54: 'ঠ', 43: 'ড', 63: 'ঢ', 60: 'ণ',
    30: 'ত', 57: 'থ', 25: 'দ', 46: 'ধ', 29: 'ন',
    15: 'প', 22: 'ফ', 3: 'ব', 24: 'ভ', 13: 'ম',
    45: 'য', 61: 'য', 23: 'র', 7: 'ল', 49: 'শ', 41: 'শ', 47: 'ষ', 14: 'স', 34: 'স', 19: 'হ',
    31: 'ক্ষ', 39: 'ৱ', 53: 'ড়',
    8: '্', 48: 'ং', 32: 'ঃ', 16: 'ঁ',
    38: 'ি', 50: 'ূ'
  };

  // Shift + vowel = Bangla vowel sign (কার)
  const BN_KAR = { 28: 'া', 10: 'ি', 20: 'ী', 37: 'ু', 51: 'ূ', 17: 'ে', 12: 'ৈ', 21: 'ো', 42: 'ৌ' };

  // Numbers: Shift + a-j chords → 1-0 (mirrors NUMBER_CHORDS in protocol.py & braile.ino)
  const NUM_DICT = {
    1: '1', 3: '2', 9: '3', 25: '4', 17: '5',
    11: '6', 27: '7', 19: '8', 8: '9', 10: '9', 26: '0'
  };

  // Shift + math & punctuation (mirrors shiftSymbols in braile.ino)
  const SYM_DICT = {
    22: '+', 36: '-', 38: '×', 54: '=', 12: '÷',
    2: ',', 6: ';', 18: ':', 50: '.'
  };

  const chordToDots = (chord) => {
    const dots = [];
    for (let i = 0; i < 6; i++) if (chord & (1 << i)) dots.push(i + 1);
    return dots;
  };
  const toBinary = (chord) => chord.toString(2).padStart(6, '0');
  const brailleUnicode = (chord) => String.fromCharCode(0x2800 + chord);

  /* ============================================================
     STICKY NAV + MOBILE MENU
     ============================================================ */
  const nav = $('#siteNav');
  const burger = $('#navBurger');
  const navLinks = $('#navLinks');

  const onScroll = () => {
    if (nav) nav.classList.toggle('scrolled', window.scrollY > 12);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  if (burger && navLinks) {
    burger.addEventListener('click', () => {
      const open = navLinks.classList.toggle('open');
      burger.classList.toggle('open', open);
      burger.setAttribute('aria-expanded', String(open));
      burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
    $$('#navLinks a').forEach((a) =>
      a.addEventListener('click', () => {
        navLinks.classList.remove('open');
        burger.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
      })
    );
  }

  /* ============================================================
     HERO SUBTLE DEPTH PARALLAX
     ============================================================ */
  const heroProductWrap = $('#heroProductWrap');
  if (heroProductWrap && !reducedMotion) {
    let ticking = false;
    const updateParallax = () => {
      const y = Math.min(window.scrollY, 700);
      heroProductWrap.style.transform = `translate3d(0, ${(y * 0.08).toFixed(1)}px, 0)`;
      ticking = false;
    };
    window.addEventListener('scroll', () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(updateParallax);
      }
    }, { passive: true });
  }

  /* ============================================================
     HARDWARE PRODUCT GALLERY
     ============================================================ */
  const galleryTabs = $$('.gallery-tab');
  const galleryImg = $('#galleryMainImg');
  const galleryBadge = $('#galleryBadge');
  const galleryCaption = $('#galleryCaption');

  if (galleryTabs.length && galleryImg) {
    const activateGalleryTab = (tab) => {
      galleryTabs.forEach((t) => {
        const active = t === tab;
        t.classList.toggle('active', active);
        t.setAttribute('aria-selected', String(active));
      });
      const nextSrc = tab.dataset.src;
      const nextAlt = tab.dataset.alt || '';
      const nextBadge = tab.dataset.badge || '';
      const nextCaption = tab.dataset.caption || '';

      if (galleryBadge) galleryBadge.textContent = nextBadge;
      if (galleryCaption) galleryCaption.textContent = nextCaption;

      if (reducedMotion || galleryImg.getAttribute('src') === nextSrc) {
        galleryImg.src = nextSrc;
        galleryImg.alt = nextAlt;
        return;
      }

      galleryImg.classList.add('switching');
      setTimeout(() => {
        galleryImg.src = nextSrc;
        galleryImg.alt = nextAlt;
        galleryImg.classList.remove('switching');
      }, 150);
    };

    galleryTabs.forEach((tab, idx) => {
      tab.addEventListener('click', () => activateGalleryTab(tab));
      tab.addEventListener('keydown', (e) => {
        let next = null;
        if (e.key === 'ArrowRight') next = galleryTabs[(idx + 1) % galleryTabs.length];
        else if (e.key === 'ArrowLeft') next = galleryTabs[(idx - 1 + galleryTabs.length) % galleryTabs.length];
        if (next) {
          e.preventDefault();
          activateGalleryTab(next);
          next.focus();
        }
      });
    });
  }

  /* ============================================================
     REVEAL ON SCROLL
     ============================================================ */
  const revealEls = $$('.reveal');
  const revealInViewport = () => {
    const vh = window.innerHeight || 900;
    revealEls.forEach((el) => {
      if (el.classList.contains('in')) return;
      const r = el.getBoundingClientRect();
      if (r.top < vh * 1.05 && r.bottom > -40) {
        el.classList.add('in');
      }
    });
  };
  if ('IntersectionObserver' in window && !reducedMotion) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add('in');
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.05, rootMargin: '0px 0px -20px 0px' }
    );
    revealEls.forEach((el) => io.observe(el));
    revealInViewport();
    window.addEventListener('scroll', revealInViewport, { passive: true });
    window.addEventListener('hashchange', () => setTimeout(revealInViewport, 60));
    window.addEventListener('load', revealInViewport);
  } else {
    revealEls.forEach((el) => el.classList.add('in'));
  }

  /* ============================================================
     COUNT-UP STATS
     ============================================================ */
  const animateCount = (el) => {
    const target = parseInt(el.dataset.count, 10);
    const prefix = el.dataset.prefix || '';
    if (reducedMotion) { el.innerHTML = prefix + target; return; }
    const dur = 950;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.innerHTML = prefix + Math.round(target * eased);
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };

  const statEls = $$('.num');
  if ('IntersectionObserver' in window) {
    const io2 = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            animateCount(e.target);
            io2.unobserve(e.target);
          }
        });
      },
      { threshold: 0.5 }
    );
    statEls.forEach((el) => io2.observe(el));
  } else {
    statEls.forEach((el) => el.innerHTML = (el.dataset.prefix || '') + el.dataset.count);
  }

  /* ============================================================
     INTERACTIVE DEMO + REAL BRAILLEBRIDGE BLE / USB SERIAL BRIDGE
     ============================================================ */
  const demoCell = $('#demoCell');
  const demoDots = $$('.demo-dot', demoCell);
  const langEn = $('#langEn');
  const langBn = $('#langBn');
  const shiftToggle = $('#shiftToggle');
  const autoCommitToggle = $('#autoCommitToggle');
  const commitBtn = $('#commitBtn');
  const spaceBtn = $('#spaceBtn');
  const bkspBtn = $('#bkspBtn');
  const clearBtn = $('#clearBtn');
  const copyStreamBtn = $('#copyStreamBtn');
  const speakStreamBtn = $('#speakStreamBtn');
  const readoutGlyph = $('#readoutGlyph');
  const readoutPreviewPill = $('#readoutPreviewPill');
  const readoutTrans = $('#readoutTrans');
  const readoutChord = $('#readoutChord');
  const readoutDots = $('#readoutDots');
  const readoutMode = $('#readoutMode');
  const readoutStream = $('#readoutStream');
  const readoutChar = $('.readout-char');
  const ledEn = $('#ledEn');
  const ledBn = $('#ledBn');

  // Hardware bridge controls
  const hwStatusDot = $('#hwStatusDot');
  const hwStatusTitle = $('#hwStatusTitle');
  const hwStatusSub = $('#hwStatusSub');
  const connectBleBtn = $('#connectBleBtn');
  const connectSerialBtn = $('#connectSerialBtn');
  const disconnectHwBtn = $('#disconnectHwBtn');

  let currentChord = 0;
  let currentLang = 'en'; // 'en' | 'bn'
  let shiftActive = false;
  let capsMode = 'OFF';   // 'OFF' | 'ONCE' | 'LOCK'
  let autoCommit = false;
  let autoTimer = null;

  const translateChord = (chord, lang, shift) => {
    if (!chord) return { ch: null, note: null };
    if (chord === 32 && !shift && lang === 'en') {
      return { ch: null, note: 'Capital sign (Dot 6)', isCapSign: true };
    }
    if (lang === 'bn') {
      if (shift) {
        if (chord in NUM_DICT) return { ch: NUM_DICT[chord], note: 'number' };
        if (chord in SYM_DICT) return { ch: SYM_DICT[chord], note: 'symbol' };
        if (chord in BN_KAR) return { ch: BN_KAR[chord], note: 'vowel sign (কার)' };
        return { ch: BN_DICT[chord] || null, note: null };
      }
      return { ch: BN_DICT[chord] || null, note: null };
    }
    if (shift) {
      if (chord in NUM_DICT) return { ch: NUM_DICT[chord], note: 'number' };
      if (chord in SYM_DICT) return { ch: SYM_DICT[chord], note: 'symbol' };
      const up = EN_DICT[chord] || EN_FALLBACK[chord];
      return up ? { ch: up.toUpperCase(), note: 'uppercase' } : { ch: null, note: null };
    }
    let ch = EN_DICT[chord] || EN_FALLBACK[chord] || null;
    if (ch && capsMode !== 'OFF') {
      ch = ch.toUpperCase();
      return { ch, note: capsMode === 'LOCK' ? 'CAPS LOCK' : 'capitalized' };
    }
    return { ch, note: null };
  };

  const setLanguageUI = (lang) => {
    currentLang = lang;
    if (langEn && langBn) {
      langEn.classList.toggle('active', lang === 'en');
      langBn.classList.toggle('active', lang === 'bn');
      langEn.setAttribute('aria-pressed', String(lang === 'en'));
      langBn.setAttribute('aria-pressed', String(lang === 'bn'));
    }
    renderDemo(false);
  };

  const renderDemo = (animate) => {
    if (!demoCell) return;
    const dots = chordToDots(currentChord);
    demoDots.forEach((d) => {
      const on = Boolean(currentChord & (1 << parseInt(d.dataset.d, 10)));
      d.setAttribute('aria-pressed', String(on));
      if (animate && on) {
        d.classList.remove('pop');
        void d.offsetWidth;
        d.classList.add('pop');
      }
    });

    const isBn = currentLang === 'bn';
    const result = translateChord(currentChord, currentLang, shiftActive);

    readoutGlyph.textContent = currentChord ? brailleUnicode(currentChord) : '⠀';
    readoutChar.classList.toggle('bangla', isBn);

    if (result && result.isCapSign) {
      readoutTrans.textContent = 'Capital Prefix (Dot 6)';
      readoutPreviewPill.textContent = 'Next letter UPPERCASE';
      readoutPreviewPill.classList.add('has-char');
    } else if (result && result.ch) {
      readoutTrans.textContent = result.ch + (result.note ? ' · ' + result.note : '');
      readoutPreviewPill.textContent = `Preview: "${result.ch}"`;
      readoutPreviewPill.classList.add('has-char');
    } else if (currentChord) {
      readoutTrans.textContent = 'Unmapped chord';
      readoutPreviewPill.textContent = 'No match';
      readoutPreviewPill.classList.remove('has-char');
    } else {
      readoutTrans.textContent = '—';
      readoutPreviewPill.textContent = 'Ready';
      readoutPreviewPill.classList.remove('has-char');
    }

    readoutChord.textContent = '0b' + toBinary(currentChord);
    readoutDots.textContent = dots.length ? dots.join(', ') : 'None';
    const modeParts = [isBn ? 'Bangla' : 'English'];
    if (shiftActive) modeParts.push('Shift');
    if (capsMode === 'ONCE') modeParts.push('Cap Next');
    if (capsMode === 'LOCK') modeParts.push('CAPS LOCK');
    readoutMode.textContent = modeParts.join(' · ');
    readoutStream.classList.toggle('bangla-stream', isBn);

    if (ledEn) ledEn.classList.toggle('on', !isBn);
    if (ledBn) ledBn.classList.toggle('on', isBn);

    if (animate && currentChord) {
      readoutGlyph.classList.remove('flash');
      void readoutGlyph.offsetWidth;
      readoutGlyph.classList.add('flash');
    }
  };

  const getStreamText = () =>
    $$('.stream-char, .stream-space', readoutStream).map((s) => s.textContent).join('');

  const appendToStream = (text, invalid) => {
    const placeholder = $('.stream-placeholder', readoutStream);
    if (placeholder) placeholder.remove();
    for (const ch of Array.from(text)) {
      if (ch === '\r') continue;
      if (ch === '\n') continue;
      const span = document.createElement('span');
      span.className = ch === ' ' ? 'stream-space' : invalid ? 'stream-invalid' : 'stream-char';
      span.textContent = ch;
      readoutStream.appendChild(span);
    }
    readoutStream.scrollTop = readoutStream.scrollHeight;
  };

  const backspaceStream = () => {
    const items = $$('.stream-char, .stream-space, .stream-invalid', readoutStream);
    if (items.length) {
      items[items.length - 1].remove();
    }
    if (!$$('.stream-char, .stream-space, .stream-invalid', readoutStream).length) {
      readoutStream.innerHTML = '<span class="stream-placeholder">Output appears here…</span>';
    }
  };

  const commitChord = () => {
    clearTimeout(autoTimer);
    if (!currentChord) return;
    if (currentChord === 32 && !shiftActive && currentLang === 'en') {
      capsMode = capsMode === 'OFF' ? 'ONCE' : capsMode === 'ONCE' ? 'LOCK' : 'OFF';
      currentChord = 0;
      renderDemo(true);
      return;
    }
    const result = translateChord(currentChord, currentLang, shiftActive);
    if (result && result.ch) {
      appendToStream(result.ch);
      if (capsMode === 'ONCE') capsMode = 'OFF';
    } else {
      appendToStream('✕', true);
      if (capsMode === 'ONCE') capsMode = 'OFF';
    }
    currentChord = 0;
    renderDemo(true);
  };

  const scheduleAutoCommit = () => {
    clearTimeout(autoTimer);
    if (autoCommit && currentChord) {
      autoTimer = setTimeout(commitChord, 650);
    }
  };

  /* ============================================================
     HARDWARE CONNECTION (Web Bluetooth NUS + Web Serial 115200)
     Mirrors protocol from braille-desktop/relay.py & braile.ino
     ============================================================ */
  const NUS_SERVICE_UUID = '6e400001-b5a3-f393-e0a9-e50e24dcca9e';
  const NUS_TX_UUID = '6e400002-b5a3-f393-e0a9-e50e24dcca9e';
  const NUS_RX_UUID = '6e400003-b5a3-f393-e0a9-e50e24dcca9e';

  const BOOT_PREFIXES = [
    'ets ', 'rst:0x', 'boot:0x', 'configSPIWP', 'clk_drv:', 'q_drv:',
    'd_drv:', 'cs0_drv:', 'hd_drv:', 'wp_drv:', 'mode:DIO', 'load:0x', 'entry 0x'
  ];

  let hwTransport = null; // 'ble' | 'serial' | null
  let bleDevice = null;
  let bleRxChar = null;
  let serialPort = null;
  let serialReader = null;
  let serialReading = false;
  let hwLineBuf = '';
  let bootSuppress = false;

  const setHwStatus = (state, title, sub) => {
    if (!hwStatusDot) return;
    hwStatusDot.classList.remove('connected', 'error');
    if (state === 'connected') hwStatusDot.classList.add('connected');
    if (state === 'error') hwStatusDot.classList.add('error');
    if (hwStatusTitle) hwStatusTitle.textContent = title;
    if (hwStatusSub) hwStatusSub.textContent = sub;
    if (disconnectHwBtn) disconnectHwBtn.hidden = state !== 'connected';
    if (connectBleBtn) connectBleBtn.hidden = state === 'connected';
    if (connectSerialBtn) connectSerialBtn.hidden = state === 'connected';
  };

  const handleControlLine = (rawLine) => {
    const line = rawLine.trim();
    if (!line) return;
    if (line.startsWith('ets ')) { bootSuppress = true; return; }
    if (BOOT_PREFIXES.some((p) => line.startsWith(p))) { bootSuppress = true; return; }
    if (bootSuppress && (line.includes('SYSTEM:') || line.startsWith('LANG:'))) {
      bootSuppress = false;
    }
    if (bootSuppress) { bootSuppress = false; return; }

    if (line === 'LANG:en') {
      setLanguageUI('en');
      return;
    }
    if (line === 'LANG:bn') {
      setLanguageUI('bn');
      return;
    }
    if (line === 'SYSTEM:BKSP') {
      backspaceStream();
      return;
    }
    if (line === 'SYSTEM:CAP_ONCE') { capsMode = 'ONCE'; renderDemo(false); return; }
    if (line === 'SYSTEM:CAP_LOCK') { capsMode = 'LOCK'; renderDemo(false); return; }
    if (line === 'SYSTEM:CAP_OFF') { capsMode = 'OFF'; renderDemo(false); return; }
    if (line.startsWith('SYSTEM:') || line === 'Invalid' || line.startsWith('SHIFT')) {
      readoutPreviewPill.textContent = line;
      return;
    }
    // Otherwise it's typed text from the device
    appendToStream(line);
    const lastCh = Array.from(line).pop();
    if (lastCh) {
      readoutTrans.textContent = lastCh + ' · hardware';
      readoutPreviewPill.textContent = `Hardware: "${lastCh}"`;
      readoutPreviewPill.classList.add('has-char');
    }
  };

  const handleHardwareChunk = (chunk) => {
    hwLineBuf += chunk;
    // Process complete newline-delimited messages; if no newline yet, forward immediate chars unless partial control prefix
    while (hwLineBuf.includes('\n')) {
      const idx = hwLineBuf.indexOf('\n');
      const line = hwLineBuf.slice(0, idx).replace(/\r$/, '');
      hwLineBuf = hwLineBuf.slice(idx + 1);
      handleControlLine(line);
    }
    if (hwLineBuf) {
      const rest = hwLineBuf;
      // Hold back incomplete control/boot prefixes until newline arrives
      const looksControl =
        'SYSTEM:'.startsWith(rest) || rest.startsWith('SYSTEM:') ||
        'LANG:'.startsWith(rest) || rest.startsWith('LANG:') ||
        'Invalid'.startsWith(rest) ||
        BOOT_PREFIXES.some((p) => p.startsWith(rest) || rest.startsWith(p));
      if (!looksControl) {
        hwLineBuf = '';
        appendToStream(rest);
        const lastCh = Array.from(rest).pop();
        if (lastCh) {
          readoutTrans.textContent = lastCh + ' · hardware';
          readoutPreviewPill.textContent = `Hardware: "${lastCh}"`;
          readoutPreviewPill.classList.add('has-char');
        }
      }
    }
  };

  const sendCommandToHardware = async (cmd) => {
    const payload = new TextEncoder().encode(cmd);
    if (hwTransport === 'ble' && bleRxChar) {
      try {
        await bleRxChar.writeValue(payload);
      } catch (_) { /* ignore write errors */ }
    } else if (hwTransport === 'serial' && serialPort && serialPort.writable) {
      try {
        const writer = serialPort.writable.getWriter();
        await writer.write(new TextEncoder().encode(cmd + '\n'));
        writer.releaseLock();
      } catch (_) { /* ignore write errors */ }
    }
  };

  const disconnectHardware = async () => {
    serialReading = false;
    hwLineBuf = '';
    if (serialReader) {
      try { await serialReader.cancel(); } catch (_) {}
      serialReader = null;
    }
    if (serialPort) {
      try { await serialPort.close(); } catch (_) {}
      serialPort = null;
    }
    if (bleDevice && bleDevice.gatt && bleDevice.gatt.connected) {
      try { bleDevice.gatt.disconnect(); } catch (_) {}
    }
    bleDevice = null;
    bleRxChar = null;
    hwTransport = null;
    setHwStatus('idle', 'Virtual Braille Pad', 'Click dots below or connect a physical BrailleBridge device');
  };

  if (connectBleBtn) {
    connectBleBtn.addEventListener('click', async () => {
      if (!navigator.bluetooth) {
        setHwStatus('error', 'Bluetooth unavailable in this browser', 'Open this page in Chrome or Edge (desktop or Android) to connect over Bluetooth LE.');
        return;
      }
      try {
        setHwStatus('idle', 'Scanning for BrailleBridge…', 'Select your BrailleBridge device in the browser prompt.');
        const device = await navigator.bluetooth.requestDevice({
          filters: [{ namePrefix: 'BrailleBridge' }, { services: [NUS_SERVICE_UUID] }],
          optionalServices: [NUS_SERVICE_UUID]
        });
        const server = await device.gatt.connect();
        const service = await server.getPrimaryService(NUS_SERVICE_UUID);
        const txChar = await service.getCharacteristic(NUS_TX_UUID);
        try {
          bleRxChar = await service.getCharacteristic(NUS_RX_UUID);
        } catch (_) {
          bleRxChar = null;
        }
        const decoder = new TextDecoder('utf-8');
        await txChar.startNotifications();
        txChar.addEventListener('characteristicvaluechanged', (ev) => {
          handleHardwareChunk(decoder.decode(ev.target.value, { stream: true }));
        });
        device.addEventListener('gattserverdisconnected', () => {
          if (hwTransport === 'ble') disconnectHardware();
        });
        bleDevice = device;
        hwTransport = 'ble';
        setHwStatus('connected', `Bluetooth Connected · ${device.name || 'BrailleBridge'}`, 'Type on your physical BrailleBridge — characters stream here live.');
      } catch (err) {
        if (err && err.name === 'NotFoundError') {
          setHwStatus('idle', 'Virtual Braille Pad', 'Bluetooth pairing cancelled.');
        } else {
          setHwStatus('error', 'Bluetooth connection failed', (err && err.message) || 'Make sure BrailleBridge is powered on and nearby.');
        }
      }
    });
  }

  if (connectSerialBtn) {
    connectSerialBtn.addEventListener('click', async () => {
      if (!('serial' in navigator)) {
        setHwStatus('error', 'Web Serial unavailable in this browser', 'Use Chrome or Edge on desktop to connect over USB Serial (115200 baud).');
        return;
      }
      try {
        setHwStatus('idle', 'Waiting for USB port…', 'Select the BrailleBridge ESP32 COM / ttyUSB port.');
        const port = await navigator.serial.requestPort();
        await port.open({ baudRate: 115200 });
        serialPort = port;
        hwTransport = 'serial';
        serialReading = true;
        setHwStatus('connected', 'USB Serial Connected · 115200 baud', 'Type on your physical BrailleBridge — characters stream here live.');

        const decoder = new TextDecoderStream();
        port.readable.pipeTo(decoder.writable).catch(() => {});
        serialReader = decoder.readable.getReader();

        (async () => {
          try {
            while (serialReading) {
              const { value, done } = await serialReader.read();
              if (done) break;
              if (value) handleHardwareChunk(value);
            }
          } catch (_) {
            /* port closed */
          } finally {
            if (hwTransport === 'serial') disconnectHardware();
          }
        })();
      } catch (err) {
        if (err && err.name === 'NotFoundError') {
          setHwStatus('idle', 'Virtual Braille Pad', 'Serial port selection cancelled.');
        } else {
          setHwStatus('error', 'USB Serial connection failed', (err && err.message) || 'Port may be busy in another application.');
        }
      }
    });
  }

  if (disconnectHwBtn) {
    disconnectHwBtn.addEventListener('click', disconnectHardware);
  }

  /* ============================================================
     VIRTUAL PAD EVENT WIRING
     ============================================================ */
  if (demoCell) {
    demoCell.addEventListener('click', (e) => {
      const dot = e.target.closest('.demo-dot');
      if (!dot) return;
      const idx = parseInt(dot.dataset.d, 10);
      currentChord ^= (1 << idx);
      renderDemo(true);
      scheduleAutoCommit();
    });

    if (commitBtn) {
      commitBtn.addEventListener('click', commitChord);
    }

    if (langEn) {
      langEn.addEventListener('click', () => {
        if (currentLang === 'en') return;
        setLanguageUI('en');
        sendCommandToHardware('LANG:en');
      });
    }
    if (langBn) {
      langBn.addEventListener('click', () => {
        if (currentLang === 'bn') return;
        setLanguageUI('bn');
        sendCommandToHardware('LANG:bn');
      });
    }

    if (shiftToggle) {
      shiftToggle.addEventListener('click', () => {
        shiftActive = !shiftActive;
        shiftToggle.classList.toggle('active', shiftActive);
        shiftToggle.setAttribute('aria-pressed', String(shiftActive));
        renderDemo(true);
      });
    }

    if (autoCommitToggle) {
      autoCommitToggle.addEventListener('click', () => {
        autoCommit = !autoCommit;
        autoCommitToggle.classList.toggle('active', autoCommit);
        autoCommitToggle.setAttribute('aria-pressed', String(autoCommit));
        if (autoCommit && currentChord) scheduleAutoCommit();
        else clearTimeout(autoTimer);
      });
    }

    if (spaceBtn) {
      spaceBtn.addEventListener('click', () => {
        if (currentChord) commitChord();
        appendToStream(' ');
        renderDemo(false);
      });
    }

    if (bkspBtn) {
      bkspBtn.addEventListener('click', () => {
        if (currentChord) {
          currentChord = 0;
          renderDemo(true);
        } else {
          backspaceStream();
        }
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', () => {
        clearTimeout(autoTimer);
        currentChord = 0;
        capsMode = 'OFF';
        readoutStream.innerHTML = '<span class="stream-placeholder">Output appears here…</span>';
        renderDemo(true);
      });
    }

    if (copyStreamBtn) {
      copyStreamBtn.addEventListener('click', async () => {
        const text = getStreamText();
        if (!text) return;
        try {
          await navigator.clipboard.writeText(text);
          const orig = copyStreamBtn.textContent;
          copyStreamBtn.textContent = 'Copied';
          setTimeout(() => { copyStreamBtn.textContent = orig; }, 1400);
        } catch (_) {}
      });
    }

    if (speakStreamBtn) {
      speakStreamBtn.addEventListener('click', () => {
        const text = getStreamText().trim();
        if (!text || !('speechSynthesis' in window)) return;
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(text);
        utter.lang = currentLang === 'bn' ? 'bn-BD' : 'en-US';
        window.speechSynthesis.speak(utter);
      });
    }

    const demoSection = $('#demo');
    const demoInView = () => {
      if (!demoSection) return false;
      const r = demoSection.getBoundingClientRect();
      return r.top <= window.innerHeight * 0.75 && r.bottom >= window.innerHeight * 0.2;
    };

    document.addEventListener('keydown', (e) => {
      if (e.repeat) return;
      if (!demoInView()) return;
      const tag = (e.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

      const k = e.key.toLowerCase();
      if (k >= '1' && k <= '6') {
        e.preventDefault();
        currentChord ^= (1 << (parseInt(k, 10) - 1));
        renderDemo(true);
        scheduleAutoCommit();
      } else if (e.key === ' ') {
        e.preventDefault();
        if (currentChord) commitChord();
        appendToStream(' ');
        renderDemo(false);
      } else if (e.key === 'Backspace') {
        e.preventDefault();
        if (currentChord) {
          currentChord = 0;
          renderDemo(true);
        } else {
          backspaceStream();
        }
      } else if (e.key === 'Shift' && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        shiftActive = !shiftActive;
        shiftToggle.classList.toggle('active', shiftActive);
        shiftToggle.setAttribute('aria-pressed', String(shiftActive));
        renderDemo(true);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        commitChord();
      } else if (e.key === 'Escape') {
        clearTimeout(autoTimer);
        currentChord = 0;
        renderDemo(true);
      }
    });

    renderDemo(false);
  }

  /* ============================================================
     DICTIONARY TABS
     ============================================================ */
  const tabs = $$('.dict-tab');
  const panels = $$('.dict-panel');
  const activateTab = (tab) => {
    tabs.forEach((t) => {
      t.classList.toggle('active', t === tab);
      t.setAttribute('aria-selected', String(t === tab));
    });
    const target = 'panel' + tab.id.replace('tab', '');
    panels.forEach((p) => {
      const show = p.id === target;
      p.hidden = !show;
      if (show) p.querySelectorAll('.reveal').forEach((el) => el.classList.add('in'));
    });
  };
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => activateTab(tab));
    tab.addEventListener('keydown', (e) => {
      let next = null;
      if (e.key === 'ArrowRight') next = tabs[(i + 1) % tabs.length];
      else if (e.key === 'ArrowLeft') next = tabs[(i - 1 + tabs.length) % tabs.length];
      else if (e.key === 'Home') next = tabs[0];
      else if (e.key === 'End') next = tabs[tabs.length - 1];
      if (next) {
        e.preventDefault();
        activateTab(next);
        next.focus();
      }
    });
  });

  /* ============================================================
     FOOTER YEAR
     ============================================================ */
  const yearEl = $('#year');
  if (yearEl) yearEl.textContent = new Date().getFullYear();
})();
