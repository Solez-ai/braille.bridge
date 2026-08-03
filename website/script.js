/* ============================================================
   BrailleBridge — Showcase Website
   Interactions + interactive braille demo
   ============================================================ */
(function () {
  'use strict';

  const $ = (sel, ctx) => (ctx || document).querySelector(sel);
  const $$ = (sel, ctx) => Array.from((ctx || document).querySelectorAll(sel));
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ============================================================
     BRAILLE DICTIONARIES (from docs/braillebridge.tex)
     chord bits: dot1=bit0 ... dot6=bit5
     ============================================================ */
  const EN_DICT = {
    1: 'a', 3: 'b', 9: 'c', 25: 'd', 17: 'e', 11: 'f', 27: 'g', 19: 'h',
    10: 'i', 26: 'j', 5: 'k', 7: 'l', 13: 'm', 29: 'n', 21: 'o', 15: 'p',
    31: 'q', 23: 'r', 14: 's', 30: 't', 37: 'u', 39: 'v', 58: 'w', 45: 'x',
    61: 'y', 41: 'z'
  };

  // Bangla (Bharati Braille) — vowels, consonants by varga, special marks
  const BN_DICT = {
    1: 'অ', 28: 'আ', 10: 'ই', 20: 'ঈ', 37: 'উ', 51: 'ঊ', 17: 'এ', 12: 'ঐ', 21: 'ও', 42: 'ঔ',
    5: 'ক', 40: 'খ', 27: 'গ', 35: 'ঘ', 44: 'ঙ',
    9: 'চ', 33: 'ছ', 26: 'জ', 52: 'ঝ', 18: 'ঞ',
    62: 'ট', 54: 'ঠ', 43: 'ড', 63: 'ঢ', 60: 'ণ',
    30: 'ত', 57: 'থ', 25: 'দ', 46: 'ধ', 29: 'ন',
    15: 'প', 22: 'ফ', 3: 'ব', 24: 'ভ', 13: 'ম',
    61: 'য', 23: 'র', 7: 'ল', 41: 'শ', 47: 'ষ', 14: 'স', 19: 'হ',
    8: '্', 48: 'ং', 32: 'ঃ', 16: 'ঁ'
  };

  // Shift + vowel = vowel sign (কার) in Bangla
  const BN_KAR = { 1: 'া', 10: 'ি', 20: 'ী', 37: 'ু', 51: 'ূ', 17: 'ে', 12: 'ৈ', 21: 'ো', 42: 'ৌ' };

  // Numbers: Shift + A–J = 1–0  |  Punctuation & math from docs
  const NUM_DICT = { 1: '1', 3: '2', 9: '3', 25: '4', 17: '5', 11: '6', 27: '7', 19: '8', 10: '9', 26: '0' };
  // Note: '×' is omitted — it shares chord (2,3,6) with '?' in the docs; '?' wins.
  const SYM_DICT = { 2: ',', 6: ';', 18: ':', 50: '.', 38: '?', 22: '!', 36: '−', 12: '÷', 54: '=' };

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

  const onScroll = () => nav.classList.toggle('scrolled', window.scrollY > 12);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

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

  /* ============================================================
     REVEAL ON SCROLL
     ============================================================ */
  const revealEls = $$('.reveal');
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
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    revealEls.forEach((el) => io.observe(el));
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
    const dur = 1100;
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
      { threshold: 0.6 }
    );
    statEls.forEach((el) => io2.observe(el));
  } else {
    statEls.forEach((el) => el.innerHTML = (el.dataset.prefix || '') + el.dataset.count);
  }

  /* ============================================================
     HERO — ambient braille animation
     ============================================================ */
  const heroDots = $$('.hero-dot');
  const heroOutput = $('#heroOutput');
  const heroDotsLabel = $('#heroDots');
  let heroIdx = 0;
  const heroSeq = [
    { chord: 1, ch: 'a' }, { chord: 3, ch: 'b' }, { chord: 9, ch: 'c' },
    { chord: 25, ch: 'd' }, { chord: 17, ch: 'e' }, { chord: 11, ch: 'f' },
    { chord: 27, ch: 'g' }, { chord: 19, ch: 'h' }, { chord: 10, ch: 'i' },
    { chord: 26, ch: 'j' }, { chord: 5, ch: 'k' }, { chord: 7, ch: 'l' },
    { chord: 13, ch: 'm' }, { chord: 29, ch: 'n' }, { chord: 21, ch: 'o' },
    { chord: 15, ch: 'p' }, { chord: 31, ch: 'q' }, { chord: 23, ch: 'r' },
    { chord: 14, ch: 's' }, { chord: 30, ch: 't' }, { chord: 37, ch: 'u' },
    { chord: 39, ch: 'v' }, { chord: 58, ch: 'w' }, { chord: 45, ch: 'x' },
    { chord: 61, ch: 'y' }, { chord: 41, ch: 'z' }
  ];

  if (!reducedMotion) {
    const stepHero = () => {
      const seq = heroSeq[heroIdx % heroSeq.length];
      heroDots.forEach((d) => d.classList.toggle('on', Boolean(seq.chord & (1 << parseInt(d.dataset.d, 10)))));
      heroDotsLabel.textContent = '0b' + toBinary(seq.chord);
      heroOutput.textContent = seq.ch;
      heroIdx++;
      setTimeout(stepHero, 1700);
    };
    setTimeout(stepHero, 800);
  } else {
    heroDots[0].classList.add('on');
    heroDotsLabel.textContent = '0b000001';
    heroOutput.textContent = 'a';
  }

  /* ============================================================
     INTERACTIVE DEMO
     ============================================================ */
  const demoCell = $('#demoCell');
  const demoDots = $$('.demo-dot', demoCell);
  const langEn = $('#langEn');
  const langBn = $('#langBn');
  const shiftToggle = $('#shiftToggle');
  const spaceBtn = $('#spaceBtn');
  const clearBtn = $('#clearBtn');
  const readoutGlyph = $('#readoutGlyph');
  const readoutTrans = $('#readoutTrans');
  const readoutChord = $('#readoutChord');
  const readoutDots = $('#readoutDots');
  const readoutMode = $('#readoutMode');
  const readoutStream = $('#readoutStream');
  const readoutChar = $('.readout-char');
  const ledEn = $('#ledEn');
  const ledBn = $('#ledBn');

  let currentChord = 0;
  let currentLang = 'en'; // 'en' | 'bn'
  let shiftActive = false;

  const isVowel = (chord) => chord in BN_KAR;

  const translate = (chord, lang, shift) => {
    if (lang === 'bn') {
      if (shift && isVowel(chord)) return { ch: BN_KAR[chord], note: 'vowel sign (কার)' };
      return { ch: BN_DICT[chord] || null, note: null };
    }
    if (shift) {
      if (chord in NUM_DICT) return { ch: NUM_DICT[chord], note: 'number' };
      if (chord in SYM_DICT) return { ch: SYM_DICT[chord], note: 'symbol' };
      const up = EN_DICT[chord];
      return up ? { ch: up.toUpperCase(), note: 'uppercase' } : { ch: null, note: null };
    }
    return { ch: EN_DICT[chord] || null, note: null };
  };

  const renderDemo = (animate) => {
    const dots = chordToDots(currentChord);
    demoDots.forEach((d) => {
      const on = Boolean(currentChord & (1 << parseInt(d.dataset.d, 10)));
      d.setAttribute('aria-pressed', String(on));
      if (animate && on) {
        d.classList.remove('pop');
        void d.offsetWidth; // restart animation
        d.classList.add('pop');
      }
    });

    const isBn = currentLang === 'bn';
    const result = translate(currentChord, currentLang, shiftActive);

    readoutGlyph.textContent = currentChord ? brailleUnicode(currentChord) : '⠀';
    readoutChar.classList.toggle('bangla', isBn);
    readoutTrans.textContent = result && result.ch ? result.ch + (result.note ? ' · ' + result.note : '') : '—';
    readoutChord.textContent = '0b' + toBinary(currentChord);
    readoutDots.textContent = dots.length ? dots.join(', ') : 'None';
    readoutMode.textContent = (isBn ? 'Bangla' : 'English') + (shiftActive ? ' · Shift' : '');
    readoutStream.classList.toggle('bangla-stream', isBn);

    ledEn.classList.toggle('on', !isBn);
    ledBn.classList.toggle('on', isBn);

    if (animate && currentChord) {
      readoutGlyph.classList.remove('flash');
      void readoutGlyph.offsetWidth;
      readoutGlyph.classList.add('flash');
    }
  };

  const appendToStream = (text, invalid) => {
    const placeholder = $('.stream-placeholder', readoutStream);
    if (placeholder) placeholder.remove();
    const span = document.createElement('span');
    span.className = text === ' ' ? 'stream-space' : invalid ? 'stream-invalid' : 'stream-char';
    span.textContent = text;
    readoutStream.appendChild(span);
    readoutStream.scrollTop = readoutStream.scrollHeight;
  };

  const commitChord = () => {
    if (!currentChord) return;
    const result = translate(currentChord, currentLang, shiftActive);
    if (result && result.ch) {
      appendToStream(result.ch);
    } else {
      appendToStream('✕', true); // invalid chord — visually distinct
    }
    currentChord = 0;
    renderDemo(true);
  };

  demoCell.addEventListener('click', (e) => {
    const dot = e.target.closest('.demo-dot');
    if (!dot) return;
    const idx = parseInt(dot.dataset.d, 10);
    currentChord ^= (1 << idx);
    renderDemo(true);
  });

  langEn.addEventListener('click', () => {
    if (currentLang === 'en') return;
    currentLang = 'en';
    langEn.classList.add('active');
    langBn.classList.remove('active');
    langEn.setAttribute('aria-pressed', 'true');
    langBn.setAttribute('aria-pressed', 'false');
    renderDemo(true);
  });
  langBn.addEventListener('click', () => {
    if (currentLang === 'bn') return;
    currentLang = 'bn';
    langBn.classList.add('active');
    langEn.classList.remove('active');
    langBn.setAttribute('aria-pressed', 'true');
    langEn.setAttribute('aria-pressed', 'false');
    renderDemo(true);
  });

  shiftToggle.addEventListener('click', () => {
    shiftActive = !shiftActive;
    shiftToggle.classList.toggle('active', shiftActive);
    shiftToggle.setAttribute('aria-pressed', String(shiftActive));
    renderDemo(true);
  });

  spaceBtn.addEventListener('click', () => {
    if (currentChord) commitChord(); // commit any composed chord first
    appendToStream(' ');
    renderDemo(false);
  });

  clearBtn.addEventListener('click', () => {
    currentChord = 0;
    readoutStream.innerHTML = '<span class="stream-placeholder">Output appears here…</span>';
    renderDemo(true);
  });

  // Keyboard support: 1-6 toggle dots, space = space, shift = shift modifier, enter = commit, esc = clear
  const demoSection = $('#demo');
  const demoInView = () => {
    if (!demoSection) return false;
    const r = demoSection.getBoundingClientRect();
    // Require the section to be mostly on-screen so we never hijack scroll
    return r.top <= window.innerHeight * 0.7 && r.bottom >= window.innerHeight * 0.25;
  };
  document.addEventListener('keydown', (e) => {
    if (e.repeat) return; // no auto-repeat flicker
    if (!demoInView()) return;
    const tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

    const k = e.key.toLowerCase();
    if (k >= '1' && k <= '6') {
      e.preventDefault();
      currentChord ^= (1 << (parseInt(k, 10) - 1));
      renderDemo(true);
    } else if (e.key === ' ') {
      e.preventDefault();
      if (currentChord) commitChord();
      appendToStream(' ');
      renderDemo(false);
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
      currentChord = 0;
      renderDemo(true);
    }
  });

  renderDemo(false);

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
     CURVED MARQUEE — mission quote on a curved path
     (native reimplementation of the React Bits CurvedLoop)
     ============================================================ */
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  const loopJacket = $('#curvedLoop');
  if (loopJacket) {
    const MARQUEE_TEXT =
      'BrailleBridge does not replace Braille \u2726 It protects Braille as the ' +
      'student\u2019s natural writing method \u2726 Removing the barrier between ' +
      'braille input and teacher-readable output \u2726\u00A0';
    const measureRef = $('#curveMeasure');
    const textPathRef = $('#curveTextPath');
    const spacingRef = { value: 0 };
    const dirRef = { value: 'left' };
    const velRef = { value: 0 };
    const dragRef = { value: false };
    const lastXRef = { value: 0 };
    let rafId = 0;

    const setOffset = (px) => {
      let o = px;
      if (spacingRef.value && o <= -spacingRef.value) o += spacingRef.value;
      if (spacingRef.value && o > 0) o -= spacingRef.value;
      textPathRef.setAttribute('startOffset', o + 'px');
      return o;
    };

    let listenersAttached = false;
    const offsetRef = { value: 0 };

    const initMarquee = () => {
      if (!measureRef || !textPathRef) return;
      cancelAnimationFrame(rafId);
      measureRef.textContent = MARQUEE_TEXT;
      const spacing = measureRef.getComputedTextLength();
      if (!spacing) return;
      spacingRef.value = spacing;
      const totalText = Array(Math.ceil(1800 / spacing) + 2).fill(MARQUEE_TEXT).join('');
      textPathRef.textContent = totalText;

      if (reducedMotion) {
        setOffset(0);
        return;
      }

      let offset = setOffset(-spacing);
      offsetRef.value = offset;
      const step = () => {
        if (!dragRef.value) {
          const delta = dirRef.value === 'right' ? 2 : -2;
          offsetRef.value = setOffset(offsetRef.value + delta);
        }
        rafId = requestAnimationFrame(step);
      };
      rafId = requestAnimationFrame(step);

      if (listenersAttached) return;
      listenersAttached = true;
      const onDown = (e) => {
        if (!finePointer) return;
        dragRef.value = true;
        lastXRef.value = e.clientX;
        velRef.value = 0;
        e.target.setPointerCapture(e.pointerId);
      };
      const onMove = (e) => {
        if (!dragRef.value || !finePointer) return;
        const dx = e.clientX - lastXRef.value;
        lastXRef.value = e.clientX;
        velRef.value = dx;
        offsetRef.value = setOffset(offsetRef.value + dx);
      };
      const endDrag = () => {
        if (!dragRef.value) return;
        dragRef.value = false;
        dirRef.value = velRef.value > 0 ? 'right' : 'left';
      };

      loopJacket.addEventListener('pointerdown', onDown);
      loopJacket.addEventListener('pointermove', onMove);
      loopJacket.addEventListener('pointerup', endDrag);
      loopJacket.addEventListener('pointercancel', endDrag);
      loopJacket.addEventListener('pointerleave', endDrag);
    };

    // Wait for fonts so measured width is accurate; retry on font load.
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(initMarquee);
    } else {
      window.addEventListener('load', initMarquee);
    }
    // Fallback: try immediately too (will be corrected once fonts settle).
    initMarquee();
    window.addEventListener('resize', () => {
      cancelAnimationFrame(rafId);
      initMarquee();
    });
  }

  /* ============================================================
     CUSTOM BRAILLE-CELL CURSOR
     ============================================================ */
  const cursor = $('#cursor');
  const IS_TEXT = 'P, H1, H2, H3, H4, H5, H6, LI, TD, TH, DD, DT, CAPTION, FIGCAPTION, BLOCKQUOTE, EM, STRONG';

  if (cursor && finePointer) {
    document.documentElement.classList.add('js-cursor');
    let targetX = -100, targetY = -100, curX = -100, curY = -100, raf = null;

    const INTERACTIVE =
      'a, button, [role="button"], .toggle-btn, .dict-tab, .demo-dot, .pipe, .nav-burger, label, .device-caption, .curved-loop';

    const loop = () => {
      curX += (targetX - curX) * 0.32;
      curY += (targetY - curY) * 0.32;
      cursor.style.transform =
        'translate(' + curX + 'px, ' + curY + 'px) translate(-50%, -50%)';
      if (Math.abs(targetX - curX) > 0.2 || Math.abs(targetY - curY) > 0.2) {
        raf = requestAnimationFrame(loop);
      } else {
        raf = null;
      }
    };

    const move = (e) => {
      targetX = e.clientX;
      targetY = e.clientY;
      if (!raf) raf = requestAnimationFrame(loop);
      if (!reducedMotion) cursor.classList.add('on');
    };

    const leave = () => cursor.classList.remove('on');

    const classify = (e) => {
      const t = e.target;
      const isInteractive = !!(t.closest && t.closest(INTERACTIVE));
      const isText = !!(t.closest && t.closest(IS_TEXT));
      cursor.classList.toggle('cursor--hover', isInteractive);
      // text-bar state is mutually exclusive with the interactive state
      cursor.classList.toggle('cursor--text', !isInteractive && isText);
    };

    document.addEventListener('mousemove', move);
    document.addEventListener('mouseover', classify);
    document.addEventListener('mousedown', () => cursor.classList.add('cursor--press'));
    document.addEventListener('mouseup', () => cursor.classList.remove('cursor--press'));
    document.documentElement.addEventListener('mouseleave', leave);

    if (reducedMotion) {
      document.removeEventListener('mousemove', move);
      document.addEventListener('mousemove', (e) => {
        cursor.style.transform =
          'translate(' + e.clientX + 'px, ' + e.clientY + 'px) translate(-50%, -50%)';
        cursor.classList.add('on');
      });
    }
  }

  /* ============================================================
     FOOTER YEAR
     ============================================================ */
  $('#year').textContent = new Date().getFullYear();
})();
