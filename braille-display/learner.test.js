/* Minimal tests for the Learner decoder — no DOM.
   Run:  node learner.test.js
   Exits non-zero on the first failure. */
const { decodeText, chordDotsList, speechTextFor } = require('./learner.js');

let pass = 0, fail = 0;
function eq(actual, expected, name) {
  const a = JSON.stringify(actual), e = JSON.stringify(expected);
  if (a === e) { pass++; }
  else { fail++; console.error(`FAIL ${name}\n  expected: ${e}\n  actual:   ${a}\n`); }
}

const dotsOf = (t, lang) => decodeText(t, lang).map(s => (s.type === 'chord' ? s.dots : s.type));

// English: every letter decodes to the firmware's exact chord.
eq(dotsOf('ab', 'en'), [[1], [1, 2]], 'english a b');
eq(dotsOf('z', 'en'), [[1, 3, 5, 6]], 'english z (1356)');

// Uppercase = Shift + the lowercase chord, exactly like the firmware.
const hi = decodeText('Hi', 'en');
eq(hi.map(s => s.chord).join(','), '19,8', 'H i chords (h=0b010011, i=0b001000)');
eq(hi.map(s => s.shift).join(','), 'true,false', 'H shifted, i not');

// Digits 1-0 ride on Shift + the a-j chords (firmware numberChords).
// '0' = j chord 0b011010 = dots 2,4,5.
eq(decodeText('10', 'en').map(s => [s.dots, s.shift]), [[[1], true], [[2, 4, 5], true]], 'digits 1 0 shifted');

// Shift symbols decode to the firmware's math/punctuation chords.
// + = dots 235, , = dot 2, . = dots 256, = = dots 2356.
eq(decodeText('+,.=', 'en').map(s => s.dots), [[2, 3, 5], [2], [2, 5, 6], [2, 3, 5, 6]], 'shift symbols');

// Space and newline are their own step types.
eq(decodeText('a b', 'en').map(s => s.type), ['chord', 'space', 'chord'], 'space step');
eq(decodeText('a\nb', 'en').map(s => s.type), ['chord', 'newline', 'chord'], 'newline step');

// Characters with no firmware chord are flagged, not guessed.
eq(decodeText('a?', 'en').map(s => s.type), ['chord', 'unknown'], 'unknown char flagged');
eq(decodeText('খ', 'en').map(s => s.type), ['unknown'], 'bangla char flagged in english mode');

// Bangla: every Bharati cell used by the firmware decodes identically.
eq(dotsOf('অ', 'bn'), [[1]], 'অ = dot 1');
eq(dotsOf('বাংলা', 'bn'),
  [[1, 2], [3, 4, 5], [5, 6], [1, 2, 3], [3, 4, 5]], 'বাংলা sequence');
eq(dotsOf('ক্ষ', 'bn'), [[1, 2, 3, 4, 5]], 'ক্ষ single chord (greedy multi-char match)');
eq(dotsOf('ও', 'bn'), [[1, 3, 5]], 'ও = dots 135');

// kar signs: those the firmware only emits with Shift must say so.
eq(decodeText('ক', 'bn').map(s => s.shift), [false], 'ক unshifted');
eq(decodeText('্', 'bn').map(s => [s.dots, s.shift]), [[[4], false]], 'hasanta = dot 4 unshifted');
eq(decodeText('া', 'bn').map(s => [s.dots, s.shift]), [[[3, 4, 5], true]], 'আ-কার = shift + 345');
eq(decodeText('ি', 'bn').map(s => [s.dots, s.shift]), [[[2, 3, 6], false]], 'ি-কার unshifted (firmware dict)');

// Full firmware spell-out of ক্ষ as three separate cells still decodes per code point.
eq(decodeText('ক', 'bn').map(s => s.dots).concat([]), [[1, 3]], 'ক = 13');

// Speech text: capitals announce, symbols get names.
eq(speechTextFor('H'), 'capital h', 'capital speech');
eq(speechTextFor('a'), 'a', 'lowercase speech');
eq(speechTextFor('+'), 'plus', 'symbol speech');
eq(speechTextFor('.'), 'period', 'period speech');
eq(speechTextFor('অ'), 'অ', 'bangla char passes through');

// chordDotsList matches the firmware bit order (bit i = dot i+1).
eq(chordDotsList(0b101010), [2, 4, 6], 'bit order');
eq(chordDotsList(0b111111), [1, 2, 3, 4, 5, 6], 'all dots');

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
