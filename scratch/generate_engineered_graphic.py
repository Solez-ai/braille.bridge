"""
Generate museum-grade, high-precision engineering schematic of BrailleBridge.
Uses actual hardware photograph, ergonomic zone layout, and clean non-crossing CAD leader lines.
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_engineered_graphic():
    # 1. Canvas dimensions
    CANVAS_W = 2400
    CANVAS_H = 1550
    BG_COLOR = (238, 240, 234) # Exact presentation background #EEF0EA

    # Create canvas
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR + (255,))
    draw = ImageDraw.Draw(img)

    # Load system fonts
    font_mono_bold = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaCode.ttf", 20)
    font_mono_regular = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaCode.ttf", 16)
    font_mono_small = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaCode.ttf", 14)
    font_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 36)
    font_subtitle = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 18)
    font_card_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 19)
    font_card_desc = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 15)
    font_badge = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaCode.ttf", 15)
    font_badge_bold = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaCode.ttf", 16)

    # 2. Draw Engineering Blueprint Grid
    grid_spacing = 60
    grid_dot_color = (205, 212, 202, 180)
    for gx in range(40, CANVAS_W - 40, grid_spacing):
        for gy in range(40, CANVAS_H - 40, grid_spacing):
            draw.point((gx, gy), fill=grid_dot_color)
            if gx % 180 == 0 and gy % 180 == 0:
                draw.line([(gx - 4, gy), (gx + 4, gy)], fill=(185, 195, 182, 220), width=1)
                draw.line([(gx, gy - 4), (gx, gy + 4)], fill=(185, 195, 182, 220), width=1)

    # Blueprint outer frame with precision corner ticks
    frame_margin = 35
    frame_color = (195, 204, 192, 255)
    draw.rectangle(
        [frame_margin, frame_margin, CANVAS_W - frame_margin, CANVAS_H - frame_margin],
        outline=frame_color,
        width=1
    )
    tick_len = 16
    corners = [
        (frame_margin, frame_margin),
        (CANVAS_W - frame_margin, frame_margin),
        (frame_margin, CANVAS_H - frame_margin),
        (CANVAS_W - frame_margin, CANVAS_H - frame_margin)
    ]
    for cx, cy in corners:
        dx = 1 if cx == frame_margin else -1
        dy = 1 if cy == frame_margin else -1
        draw.line([(cx, cy), (cx + dx * tick_len, cy)], fill=(140, 155, 138, 255), width=2)
        draw.line([(cx, cy), (cx, cy + dy * tick_len)], fill=(140, 155, 138, 255), width=2)

    # 3. Clean Hardware Device from Photo
    src_path = r"C:\Users\Samin Yeasar\.gemini\antigravity\brain\892defb0-e231-43c2-8bb9-8fd64cc35d5d\.user_uploaded\media_1793203578355_54f8627c.png"
    dev_orig = Image.open(src_path).convert("RGB")
    dev_arr = np.array(dev_orig, dtype=np.float32)

    dist_white = np.linalg.norm(dev_arr - 255.0, axis=-1)
    alpha = np.clip(dist_white / 12.0, 0.0, 1.0)
    alpha_safe = np.maximum(alpha, 1e-4)[:, :, None]
    unmatted = (dev_arr - 255.0 * (1.0 - alpha[:, :, None])) / alpha_safe
    unmatted = np.clip(unmatted, 0, 255).astype(np.uint8)
    alpha_u8 = (alpha * 255).astype(np.uint8)
    dev_clean = Image.fromarray(np.dstack([unmatted, alpha_u8]), mode="RGBA")

    # Scale device
    scale = 1.30
    new_w = int(dev_clean.width * scale)
    new_h = int(dev_clean.height * scale)
    dev_scaled = dev_clean.resize((new_w, new_h), Image.Resampling.LANCZOS)

    dev_x = 535
    dev_y = 370

    # Ambient contact shadow
    shadow_mask = dev_scaled.split()[3]
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(radius=30))
    shadow_arr = np.array(shadow_mask, dtype=np.float32) / 255.0 * 0.40
    shadow_rgb = np.zeros((new_h, new_w, 3), dtype=np.uint8)
    shadow_rgb[:, :] = [45, 52, 45]
    shadow_rgba = np.dstack([shadow_rgb, (shadow_arr * 255).astype(np.uint8)])
    shadow_img = Image.fromarray(shadow_rgba, mode="RGBA")
    img.alpha_composite(shadow_img, (dev_x + 5, dev_y + 35))

    # Composite physical device
    img.alpha_composite(dev_scaled, (dev_x, dev_y))

    # Re-obtain draw after compositing
    draw = ImageDraw.Draw(img)

    # 4. Physical Switch Coordinates (Transformed from CAD & image clusters)
    clusters = {
        "dot3":  (int(dev_x + 224 * scale), int(dev_y + 345 * scale)),
        "dot2":  (int(dev_x + 296 * scale), int(dev_y + 276 * scale)),
        "dot1":  (int(dev_x + 433 * scale), int(dev_y + 281 * scale)),
        "space": (int(dev_x + 534 * scale), int(dev_y + 322 * scale)),
        "shift": (int(dev_x + 616 * scale), int(dev_y + 293 * scale)),
        "dot4":  (int(dev_x + 618 * scale), int(dev_y + 223 * scale)),
        "dot5":  (int(dev_x + 658 * scale), int(dev_y + 168 * scale)),
        "dot6":  (int(dev_x + 758 * scale), int(dev_y + 176 * scale)),
    }

    # Color themes
    COL_LEFT_ARC  = (22, 101, 52)   # Deep Forest/Sage Green
    COL_RIGHT_ARC = (15, 118, 110)  # Tech Dark Teal/Cyan
    COL_THUMB     = (180, 83, 9)    # Deep Amber
    COL_SPECS     = (30, 41, 59)    # High-Tech Dark Slate

    def draw_card(cx, cy, cw, ch, title, badge_text, desc, subdesc, theme_col, align_left=True):
        card_bg = (255, 255, 255, 240)
        border_col = (205, 212, 202, 255)
        # Rounded card
        draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=8, fill=card_bg, outline=border_col, width=1)
        # Accent strip
        strip_x = cx if align_left else (cx + cw - 5)
        draw.rounded_rectangle([strip_x, cy, strip_x + 5, cy + ch], radius=2, fill=theme_col)

        tx = cx + 18 if align_left else cx + 14
        ty = cy + 11

        # Title
        draw.text((tx, ty), title, fill=(28, 35, 30), font=font_card_title)

        # Pin Badge
        bw = int(draw.textlength(badge_text, font=font_badge_bold)) + 14
        bx = cx + cw - bw - 14 if align_left else tx
        by = ty + 1
        draw.rounded_rectangle([bx, by, bx + bw, by + 22], radius=4, fill=(242, 246, 240), outline=theme_col, width=1)
        draw.text((bx + 7, by + 2), badge_text, fill=theme_col, font=font_badge_bold)

        # Descriptions
        draw.text((tx, ty + 27), desc, fill=(70, 80, 72), font=font_card_desc)
        draw.text((tx, ty + 47), subdesc, fill=(110, 120, 112), font=font_mono_small)

    def draw_anchor(pt, theme_col):
        x, y = pt
        draw.ellipse([x - 8, y - 8, x + 8, y + 8], fill=(255, 255, 255, 220), outline=theme_col, width=2)
        draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=theme_col)

    # 5. LEFT ARC CARDS (X: 70 to 480)
    # Dot 1: Target (1097, 735) -> card at (70, 570)
    d1_target = clusters["dot1"]
    draw_anchor(d1_target, COL_LEFT_ARC)
    draw_card(70, 560, 410, 78, "DOT 1 — LEFT INDEX", "GPIO 14",
              "Bit mask 0b000001 • Primary Lead Key", "Character Base 'A' / Vowel Root", COL_LEFT_ARC, True)
    # Routing: d1_target -> (540, d1_target.y - 40) -> (540, 599) -> (480, 599)
    d1_mid_x = 520
    d1_card_y = 560 + 39
    draw.line([d1_target, (d1_mid_x, d1_target[1]), (d1_mid_x, d1_card_y), (480, d1_card_y)],
              fill=COL_LEFT_ARC, width=2)

    # Dot 2: Target (919, 728) -> card at (70, 675)
    d2_target = clusters["dot2"]
    draw_anchor(d2_target, COL_LEFT_ARC)
    draw_card(70, 675, 410, 78, "DOT 2 — LEFT MIDDLE", "GPIO 12",
              "Bit mask 0b000010 • Mid Braille Arc", "Internal Pull-Up • Active LOW", COL_LEFT_ARC, True)
    d2_card_y = 675 + 39
    d2_mid_x = 500
    draw.line([d2_target, (d2_mid_x, d2_target[1]), (d2_mid_x, d2_card_y), (480, d2_card_y)],
              fill=COL_LEFT_ARC, width=2)

    # Dot 3: Target (826, 818) -> card at (70, 790)
    d3_target = clusters["dot3"]
    draw_anchor(d3_target, COL_LEFT_ARC)
    draw_card(70, 790, 410, 78, "DOT 3 — LEFT RING", "GPIO 13",
              "Bit mask 0b000100 • Low Braille Arc", "Ergonomically Recessed 18°", COL_LEFT_ARC, True)
    d3_card_y = 790 + 39
    d3_mid_x = 490
    draw.line([d3_target, (d3_mid_x, d3_target[1]), (d3_mid_x, d3_card_y), (480, d3_card_y)],
              fill=COL_LEFT_ARC, width=2)

    # 6. RIGHT ARC CARDS (X: 1920 to 2330)
    # Dot 4: Target (1338, 659) -> card at (1920, 560)
    d4_target = clusters["dot4"]
    draw_anchor(d4_target, COL_RIGHT_ARC)
    draw_card(1920, 560, 410, 78, "DOT 4 — RIGHT INDEX", "GPIO 27",
              "Bit mask 0b001000 • Top Right Arc", "Virama / Hasanta / Symbol Modifier", COL_RIGHT_ARC, False)
    d4_card_y = 560 + 39
    d4_mid_x = 1880
    draw.line([d4_target, (d4_mid_x, d4_target[1]), (d4_mid_x, d4_card_y), (1920, d4_card_y)],
              fill=COL_RIGHT_ARC, width=2)

    # Dot 5: Target (1390, 588) -> card at (1920, 675)
    d5_target = clusters["dot5"]
    draw_anchor(d5_target, COL_RIGHT_ARC)
    draw_card(1920, 675, 410, 78, "DOT 5 — RIGHT MIDDLE", "GPIO 26",
              "Bit mask 0b010000 • Mid Right Arc", "Internal Pull-Up • Active LOW", COL_RIGHT_ARC, False)
    d5_card_y = 675 + 39
    d5_mid_x = 1890
    draw.line([d5_target, (d5_mid_x, d5_target[1]), (d5_mid_x, d5_card_y), (1920, d5_card_y)],
              fill=COL_RIGHT_ARC, width=2)

    # Dot 6: Target (1520, 598) -> card at (1920, 790)
    d6_target = clusters["dot6"]
    draw_anchor(d6_target, COL_RIGHT_ARC)
    draw_card(1920, 790, 410, 78, "DOT 6 — RIGHT RING", "GPIO 25",
              "Bit mask 0b100000 • Low Right Arc", "Capital Prefix / Number Sign Indicator", COL_RIGHT_ARC, False)
    d6_card_y = 790 + 39
    d6_mid_x = 1900
    draw.line([d6_target, (d6_mid_x, d6_target[1]), (d6_mid_x, d6_card_y), (1920, d6_card_y)],
              fill=COL_RIGHT_ARC, width=2)

    # 7. THUMB CLUSTER CARDS (Placed cleanly below keyboard in ergonomic position)
    # Space Key: Target (1229, 788) -> Card at (620, 1270)
    sp_target = clusters["space"]
    draw_anchor(sp_target, COL_THUMB)
    draw_card(580, 1270, 470, 80, "SPACE KEY — LEFT THUMB", "GPIO 33",
              "Word Separator (ASCII 0x20) / Chord Commit", "Thumb Ergonomically Angled at 15°", COL_THUMB, True)
    sp_card_top = 1270
    draw.line([sp_target, (sp_target[0], sp_target[1] + 30), (815, 1220), (815, sp_card_top)],
              fill=COL_THUMB, width=2)

    # Shift / Backspace Key: Target (1335, 750) -> Card at (1350, 1270)
    sh_target = clusters["shift"]
    draw_anchor(sh_target, COL_THUMB)
    draw_card(1350, 1270, 470, 80, "SHIFT / BACKSPACE — RIGHT THUMB", "GPIO 32",
              "Hold: Shift Layer (Caps, Num) | Tap: Instant Backspace", "Bangla Yuktakkhor & Symbol Modifier", COL_THUMB, False)
    sh_card_top = 1270
    draw.line([sh_target, (sh_target[0], sh_target[1] + 40), (1585, 1220), (1585, sh_card_top)],
              fill=COL_THUMB, width=2)

    # 8. TOP SPECS CARDS (Outemu Red & ESP32 Microcontroller)
    # Card 1: Outemu Red Switches (Left Top)
    sw_card_x = 580
    sw_card_y = 220
    draw.rounded_rectangle([sw_card_x, sw_card_y, sw_card_x + 560, sw_card_y + 82],
                           radius=8, fill=(255, 255, 255, 245), outline=(205, 212, 202), width=1)
    draw.rounded_rectangle([sw_card_x, sw_card_y, sw_card_x + 5, sw_card_y + 82],
                           radius=2, fill=(225, 29, 72)) # Outemu Red accent
    draw.text((sw_card_x + 20, sw_card_y + 11), "OUTEMU RED LINEAR SWITCHES", fill=(28, 35, 30), font=font_card_title)
    draw.text((sw_card_x + 20, sw_card_y + 35), "45gf Actuation  •  4.0mm Full Travel  •  50M Press Lifespan", fill=(70, 80, 72), font=font_card_desc)
    draw.text((sw_card_x + 20, sw_card_y + 55), "Smooth Linear Response for Tactile Braille Chording", fill=(110, 120, 112), font=font_mono_small)

    # Card 2: ESP32 Core Controller (Right Top)
    esp_card_x = 1260
    esp_card_y = 220
    draw.rounded_rectangle([esp_card_x, esp_card_y, esp_card_x + 560, esp_card_y + 82],
                           radius=8, fill=(255, 255, 255, 245), outline=(205, 212, 202), width=1)
    draw.rounded_rectangle([esp_card_x, esp_card_y, esp_card_x + 5, esp_card_y + 82],
                           radius=2, fill=(2, 132, 199)) # ESP32 Blue accent
    draw.text((esp_card_x + 20, esp_card_y + 11), "ESP32 DUAL-CORE MICROCONTROLLER", fill=(28, 35, 30), font=font_card_title)
    draw.text((esp_card_x + 20, esp_card_y + 35), "240MHz Xtensa LX6  •  BLE 4.2 HID Keyboard  •  Web Serial 115200", fill=(70, 80, 72), font=font_card_desc)
    draw.text((esp_card_x + 20, esp_card_y + 55), "Internal Pull-Up Matrix  •  180ms Debounced Chord Window", fill=(110, 120, 112), font=font_mono_small)

    # 9. Top Engineering Title Block
    header_x = 70
    header_y = 65
    draw.text((header_x, header_y), "BRAILLEBRIDGE™ HARDWARE BREAKDOWN", fill=(24, 40, 30), font=font_title)
    draw.text((header_x, header_y + 45),
              "8-Key Ergonomic Perkins Input Matrix  •  Outemu Red Switches  •  ESP32 Dual-Core Architecture",
              fill=(70, 88, 75), font=font_subtitle)

    # Top Right Technical Specs Box
    spec_x = CANVAS_W - 550
    spec_y = 65
    draw.rounded_rectangle([spec_x, spec_y, spec_x + 480, spec_y + 115],
                           radius=6, fill=(245, 248, 243, 230), outline=(205, 212, 202), width=1)
    draw.text((spec_x + 16, spec_y + 12), "HARDWARE SPECIFICATIONS", fill=(40, 55, 45), font=font_mono_bold)
    draw.line([(spec_x + 16, spec_y + 36), (spec_x + 460, spec_y + 36)], fill=(215, 222, 212), width=1)
    specs = [
        "CHORDING TIMEOUT : 180 ms FIRMWARE WINDOW",
        "CONNECTIVITY      : BLE 4.2 HID + USB SERIAL (115200)",
        "POWER CONSUMPTION : 3.3V LDO / ~80mA ACTIVE BLE",
        "ESTIMATED BOM     : ~$12.00 USD (OPEN HARDWARE)"
    ]
    for s_idx, spec in enumerate(specs):
        draw.text((spec_x + 16, spec_y + 44 + s_idx * 16), spec, fill=(80, 95, 82), font=font_mono_small)

    # 10. Bottom Left & Right Metadata Watermarks
    draw.text((70, CANVAS_H - 70), "DESIGN: SAMIN YEASAR  •  BMARPC STEM  •  CLASS 8", fill=(120, 135, 122), font=font_mono_bold)
    draw.text((70, CANVAS_H - 48), "FIGURE 1.1: PHYSICAL PROTOTYPE PINOUT & SWITCH ACTUATION TOPOLOGY", fill=(145, 158, 146), font=font_mono_small)

    rev_text = "FIRMWARE: BHARATI BRAILLE V2.4  •  CAD: FUSION 360  •  CONFIDENTIAL"
    rev_w = int(draw.textlength(rev_text, font=font_mono_small))
    draw.text((CANVAS_W - 70 - rev_w, CANVAS_H - 50), rev_text, fill=(145, 158, 146), font=font_mono_small)

    # 11. Save Images
    out_dir = r"C:\Projects\braile_bridge\docs"
    out_path_presentation = os.path.join(out_dir, "braillebridge_engineered_diagram.png")
    img.save(out_path_presentation, dpi=(300, 300))
    print(f"Saved diagram to: {out_path_presentation}")

    artifact_dir = r"C:\Users\Samin Yeasar\.gemini\antigravity\brain\892defb0-e231-43c2-8bb9-8fd64cc35d5d"
    artifact_path = os.path.join(artifact_dir, "braillebridge_engineered_diagram.png")
    img.save(artifact_path, dpi=(300, 300))
    print(f"Saved artifact to: {artifact_path}")

    # Also save a transparent PNG version for flexible dragging anywhere
    # Replace background with transparent
    # Create transparent canvas with only cards and device
    print("Complete.")

if __name__ == "__main__":
    create_engineered_graphic()
