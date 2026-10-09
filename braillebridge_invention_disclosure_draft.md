# BrailleBridge — Invention Disclosure Draft

**Prepared by:** Samin Yeasar
**Contact:** samin@mentormind.bd
**GitHub:** github.com/Solez-ai
**Web:** solez.html-5.me
**Date prepared:** [fill in today's date]
**Status:** Draft for discussion with IP counsel / DPDT — not a filing, not legal advice

---

## 1. Invention title

**BrailleBridge — A low-cost bilingual (English + Bangla) digital Braille writing and classroom examination system, with coordinated dual-channel output for the student and the teacher.**

---

## 2. Inventor / applicant information

- Name:
- Address:
- Nationality:
- Contact details:
- Whether any co-inventor contributed to the technical conception:

---

## 3. What the invention is, in plain language

BrailleBridge is a device and software system that lets a blind or visually impaired student write independently using a six-dot Braille keyboard, while a sighted teacher receives readable text in real time.

The system has two main parts:

1. **A hardware device** that the student holds and types on:
   - Six mechanical Braille dot keys, plus a Space key and a Shift key
   - An ESP32 microcontroller that detects chorded key presses
   - Two LEDs indicating the active language: red for English, green for Bangla
   - A custom 3D-printed enclosure

2. **Software that receives and displays the typed text:**
   - A teacher software that runs in a browser using the Web Serial API
   - A Bluetooth path that lets the typed text appear on the student's own device
   - A USB Serial path that sends translated text to the teacher software

The key practical point is that the same Braille input can produce readable output for both the student and the teacher, and it works for both English and Bangla.

---

## 4. What problem it solves

Today, many blind students cannot independently produce a written answer that a sighted teacher can read. The common solution is a sighted writer, which creates problems including:

- loss of privacy,
- loss of independence,
- slower pace controlled by the writer,
- possible transcription errors,
- teacher inability to read Braille,
- high cost of existing Braille equipment.

BrailleBridge is meant to let the student write alone, while the teacher still receives ordinary readable text.

---

## 5. What makes this different from existing solutions

The invention is not just one feature. The distinctive technical combination is the point. Taken separately, some of the pieces may exist elsewhere; the inventive part is how they are integrated into one device and software system so that a single Braille input produces coordinated bilingual output for the student and the teacher.

Distinctive elements to discuss with counsel:

- A single hardware device that provides both a Bluetooth keyboard output path and a USB Serial output path at the same time, from the same typed input.
- Bilingual English + Bangla output from the same hardware, with the active language controlled in software rather than by a separate physical switch.
- Language switching using a deliberate Braille chord (dots 4+5+6 held) that is unlikely to be triggered by ordinary typing.
- A shift layer that expands the same six-dot input into numbers, punctuation, and math symbols without adding keys, with mode-dependent behavior for English uppercase and Bangla vowel signs.
- Shift-tap used as backspace, with explicit guards so it does not misfire during ordinary chorded input.
- A browser-based teacher interface that receives the translated output directly over serial/Bluetooth, supports multiple students, and can export timestamped records.
- A low-cost bill of materials that keeps the whole system affordable for schools.

---

## 6. The technical idea in more detail

### 6.1 Hardware input

- The six Braille dot keys are read as a 6-bit chord.
- The firmware collects keys pressed within a short time window so that fingers pressing at slightly different times still form one intended chord.
- Space and Shift are handled as separate inputs.

### 6.2 Language switching

- Dots 4+5+6 held for a set duration switches between English and Bangla.
- The device indicates the current language with LEDs.
- The language change is also reported over the serial/Bluetooth stream so the teacher software can update its display.

### 6.3 Translation

- The device contains dictionaries for English and Bangla.
- A chord is looked up and translated into the appropriate character.
- Shift modifies the result for numbers, punctuation, math symbols, uppercase letters, or Bangla vowel signs depending on mode.

### 6.4 Coordinated dual output

- The same typed chord produces two coordinated outputs.
- One output path is aimed at the student's own device through Bluetooth keyboard behavior.
- Another output path goes over USB Serial to the teacher software.
- The teacher software can display output live, organize multiple students, and export timestamped records.
- The practical effect is that one Braille input can simultaneously serve the student's device and the teacher's readable display, with language and shift behavior shared across the system.

---

## 7. What is novel / inventive about it

This is the most important section for patent discussion, and it should be completed with the help of a patent professional.

The stronger case is usually not “a Braille keyboard” in general, but the specific technical combination and integration in this system. Possible angles to develop with counsel:

- One input device producing two coordinated output channels at the same time: a student-facing Bluetooth keyboard path and a teacher-facing USB Serial path, both derived from the same Braille chord event.
- A single hardware platform supporting bilingual English/Bangla output with software-controlled language switching, where the language change is signalled through the output stream and confirmed by LEDs.
- A chord-based language toggle and a shift modifier architecture that expands a small six-key input into English, Bangla, numbers, punctuation, and math symbols without additional keys.
- The integrated behavior of the backspace/tap-guard logic with the chording, language, and shift systems, if any part of that integration is not obvious from generic keyboard logic.
- Any specific implementation detail in the firmware, dictionaries, or teacher software integration that is not just a restatement of known Braille patterns or known Bluetooth keyboard behavior.

Important caution: many individual elements may already be known. A patent discussion should focus on what is new and non-obvious in the combination and implementation, not on the broad idea of typing Braille into a connected device.

---

## 8. What parts may be protectable in different ways

A single project like this can involve several kinds of intellectual property. They protect different things and can overlap.

### 8.1 Patent
May be relevant for:
- the technical method and device architecture,
- inventive implementation details that are new and non-obvious.

Less likely to protect by itself:
- the general idea of a Braille keyboard,
- known Braille patterns by themselves,
- purely functional design choices that are obvious variations of existing input devices.

### 8.2 Industrial design
May be relevant for:
- the visual appearance of the device or enclosure,
- the shape, form, lines, and ornamental look of the external product.

This protects how the product looks, not how it works.

### 8.3 Copyright
May be relevant for:
- the firmware source code,
- the teacher software code,
- the desktop relay code,
- the documentation, paper, text, and drawings.

Copyright protects original expression, not the underlying technical function or idea.

### 8.4 Trademark
May be relevant for:
- the name “BrailleBridge”,
- any logo or brand identity used with it.

This protects brand identity, not the invention itself.

---

## 9. Current status of the invention

- Prototype stage.
- Firmware exists and has been revised over time.
- Teacher software exists in browser form.
- Desktop relay software exists.
- Documentation and a research paper are included in the project.
- The device has been tested in use.

---

## 10. Public disclosure history

This section matters a lot for patent filing strategy.

Please list any public disclosures already made, if any:

- Has the device been shown publicly?
- Has the project been published online?
- Has the paper been published or presented?
- Has the firmware been made public?
- Has the design been shared with anyone without restriction?
- Were screenshots, videos, CAD files, STL files, enclosure photos, or full source code shared?
- If yes, when, where, and with whom?

If there has been no public disclosure yet, say so explicitly.

If some parts were shared under a private or confidential arrangement, say that too, and keep any consent, message, or agreement that shows it was private.

---

## 11. Desired protection goals

Fill this in before meeting counsel, because the goal determines the strategy.

Possible goals include:

- protect the invention as an IP asset,
- prevent copying of the device or code,
- protect the appearance of the device,
- keep the code protected while still allowing some form of licensing,
- allow open or copyleft-style sharing under specific terms,
- keep the option of later commercial or exclusive use.

If several goals apply, say which ones matter most. For example, the user may want to protect the invention while still choosing how the code is shared. That is a policy and legal decision, not just a technical one.

---

## 12. Files and evidence already in the project

The project already contains materials that may help show development history, including:

- firmware source,
- teacher software source,
- desktop relay software source,
- documentation and research paper source,
- a timestamped record of the current repository state.

These are useful as supporting material, but they are not a substitute for a proper filing strategy.

---

## 13. Questions for the patent attorney / DPDT

1. Is the invention patentable in Bangladesh under the Patent Act 2023?
2. If yes, what should the claims focus on?
3. Has any prior art been disclosed that could affect novelty or inventive step?
4. Should a provisional specification be filed first?
5. Should industrial design registration also be considered for the enclosure/appearance?
6. Should copyright registration be filed for the code and documentation?
7. Should the name “BrailleBridge” be protected as a trademark?
8. What is the recommended filing order if budget is limited?
9. How does public disclosure so far affect the options?
10. What would be the recommended approach if international protection is also wanted later?

---

## 14. Note on licensing and protection goals

There are several common goals, and they do not all lead to the same legal setup. Examples:

- **Keep the invention protected and controlled.** This usually means not publishing the full technical detail broadly before filing, and considering patent, design, and/or copyright routes depending on the asset.
- **Protect the code as expression.** Copyright can protect the source code and documentation as written material, but it does not by itself protect the technical function.
- **Allow some sharing under controlled terms.** A chosen license can shape what others may do with the code or project, but licensing is a separate decision from patenting or design registration.
- **Use a copyleft-style license.** If the goal is to require downstream users to keep sharing under the same terms, a copyleft license can do that for the licensed material. That can be useful, but it is a distribution policy, not the same thing as obtaining exclusive patent or design rights.

These goals can conflict. For example, wide open distribution under a strong license can affect the legal position if patent protection is also wanted later. The right choice depends on what you actually want to achieve: protection, controlled sharing, open collaboration, or some mix of them.

---

## 15. Do this now — practical order of operations

If you want to protect the invention and still decide later how the code is shared, the safest general sequence is:

### Step 1: Stop broad public disclosure until you know your filing position
- Do not publish the full firmware, full design, or full technical method publicly yet if patent protection may matter.
- If you have already published anything, record exactly what, when, and where in Section 10.
- If you are unsure whether something is "too much disclosure," treat it as too much until a patent professional says otherwise.

### Step 2: Separate the private part from the shareable part
- Keep the invention-critical technical material private for now.
- Decide which parts, if any, can be shared safely before filing.
- Keep the private dev folder out of Git, which is already done here with the ignored folder.

### Step 3: Preserve evidence now
- Use the evidence checklist file.
- Keep dated records, backups, photos, build notes, and version history.
- Do not delete earlier versions if you may need to show development history later.

### Step 4: Decide the goal in plain language
Pick the main goal first, because it changes what you should do next:

- If the main goal is **exclusive protection**, then public sharing and strong open licensing before filing can be risky.
- If the main goal is **controlled sharing**, then the question is which license or agreement lets you keep the control you want.
- If the main goal is **open collaboration under rules you choose**, then a chosen license can express that, but it is not the same as obtaining patent or design rights.

### Step 5: Do not mix up "code license" with "invention protection"
- A license controls how others may use the material you share.
- A patent or design filing is about legal protection of the invention or appearance.
- You can keep the code private now and still decide later how to license it.
- You can also choose a license later, but once something is broadly released under a license, that can affect your options.

### Step 6: Get the family/permission issue right if it matters
- If you are not legally an adult in your jurisdiction, your ability to file, sign, or bind yourself may be limited.
- If your father has agreed to this, keep that agreement in writing and clear.
- If a filing or contract may be needed, ask a qualified lawyer or the relevant office whether a parent/guardian signature, consent, or assent is required.
- Do not assume a family agreement automatically does the same job as a legal filing or legal authority.

### Step 7: Talk to a qualified IP professional before you commit
- Bring this disclosure draft.
- Bring the public disclosure history.
- Bring the evidence you have preserved.
- Ask for a filing order that fits both the invention and the code-sharing goal.

---

## 16. Parent / guardian and signature note

If you are under the age of majority where you live, or if a parent/guardian is involved in the decision, keep this in mind:

- Agreement among family members is good for practical support, but it may not be enough by itself for legal filings or contracts.
- If you are a minor, some actions may require a parent/guardian signature, consent, or involvement depending on local law.
- If the invention is being developed with a parent, guardian, school, employer, or anyone else, the ownership and filing rights should be clarified in writing before filing.
- Keep any consent, agreement, or authorization in a saved record, not just in conversation.

This is a practical note, not legal advice. The exact rule depends on your jurisdiction and your exact situation.

---

## 17. Signature

Inventor signature: ______________________________

Date: ______________________________

Witness signature: ______________________________

Date: ______________________________

---

*This document is a practical draft for discussion and preparation only. It is not legal advice and is not a patent application, design application, copyright registration, trademark filing, or a substitute for advice from a qualified lawyer or the relevant IP office. The exact rules depend on your jurisdiction and your exact situation.*
