"""
Generate high-precision engineering diagram of BrailleBridge hardware.
Uses actual hardware photograph and precision CAD/firmware callouts.
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
    font_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 34)
    font_subtitle = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 18)
    font_card_title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 19)
    font_card_desc = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 15)
    font_badge = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaCode.ttf", 15)

    # 2. Draw Engineering Blueprint Grid
    # Subtle dot matrix grid across canvas
    grid_spacing = 60
    grid_dot_color = (205, 212, 202, 180)
    for gx in range(40, CANVAS_W - 40, grid_spacing):
        for gy in range(40, CANVAS_H - 40, grid_spacing):
            draw.point((gx, gy), fill=grid_dot_color)
            # Add small plus ticks every 180px
            if gx % 180 == 0 and gy % 180 == 0:
                draw.line([(gx - 4, gy), (gx + 4, gy)], fill=(185, 195, 182, 220), width=1)
                draw.line([(gx, gy - 4), (gx, gy + 4)], fill=(185, 195, 182, 220), width=1)

    # Blueprint outer border frame with corner ticks
    frame_margin = 35
    frame_color = (195, 204, 192, 255)
    draw.rectangle(
        [frame_margin, frame_margin, CANVAS_W - frame_margin, CANVAS_H - frame_margin],
        outline=frame_color,
        width=1
    )
    # Corner registration marks
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

    # 3. Extract and Clean Hardware Image
    src_path = r"C:\Users\Samin Yeasar\.gemini\antigravity\brain\892defb0-e231-43c2-8bb9-8fd64cc35d5d\.user_uploaded\media_1793203578355_54f8627c.png"
    dev_orig = Image.open(src_path).convert("RGB")
    dev_arr = np.array(dev_orig, dtype=np.float32)

    # Matte deconvolution from white background
    dist_white = np.linalg.norm(dev_arr - 255.0, axis=-1)
    alpha = np.clip(dist_white / 12.0, 0.0, 1.0)
    alpha_safe = np.maximum(alpha, 1e-4)[:, :, None]
    unmatted = (dev_arr - 255.0 * (1.0 - alpha[:, :, None])) / alpha_safe
    unmatted = np.clip(unmatted, 0, 255).astype(np.uint8)
    alpha_u8 = (alpha * 255).astype(np.uint8)
    dev_clean = Image.fromarray(np.dstack([unmatted, alpha_u8]), mode="RGBA")

    # Resize device for canvas
    scale = 1.32
    new_w = int(dev_clean.width * scale)
    new_h = int(dev_clean.height * scale)
    dev_scaled = dev_clean.resize((new_w, new_h), Image.Resampling.LANCZOS)

    dev_x = 540
    dev_y = 390

    # 4. Realistic Ambient Contact Shadow under device
    # Extract alpha mask, blur heavily, tint dark warm slate
    shadow_mask = dev_scaled.split()[3]
    shadow_mask = shadow_mask.filter(ImageFilter.GaussianBlur(radius=28))
    shadow_arr = np.array(shadow_mask, dtype=np.float32) / 255.0 * 0.45
    shadow_rgb = np.zeros((new_h, new_w, 3), dtype=np.uint8)
    shadow_rgb[:, :] = [45, 52, 45]
    shadow_rgba = np.dstack([shadow_rgb, (shadow_arr * 255).astype(np.uint8)])
    shadow_img = Image.fromarray(shadow_rgba, mode="RGBA")
    # Paste shadow offset downwards slightly
    img.alpha_composite(shadow_img, (dev_x + 5, dev_y + 35))

    # Paste scaled device
    img.alpha_composite(dev_scaled, (dev_x, dev_y))

    # Re-obtain draw after alpha composites
    draw = ImageDraw.Draw(img)

    # 5. Switch Cluster Coordinates on Canvas
    # Based on original image coordinates:
    # 0: Dot 3 (Left Ring) -> (224, 345)
    # 1: Dot 2 (Left Mid)  -> (296, 276)
    # 2: Dot 1 (Left Idx)  -> (433, 281)
    # 3: Space (Left Thumb)-> (534, 322)
    # 4: Shift (Right Thumb)->(616, 293)
    # 5: Dot 4 (Right Idx) -> (618, 223)
    # 6: Dot 5 (Right Mid) -> (658, 168)
    # 7: Dot 6 (Right Ring)-> (758, 176)
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

    # 6. Helper: Draw Precision Engineering Callout Card & Leader
    def draw_callout(target_pt, card_x, card_y, card_w, card_h,
                     title, pin, desc, subdesc,
                     theme_color, is_left_align=True):
        """
        Draws a floating frosted engineering card with leader line and switch anchor.
        """
        # Card Background: crisp white with subtle border and colored accent strip
        card_bg = (255, 255, 255, 235)
        border_col = (200, 208, 198, 255)

        # Draw card rounded rect
        draw.rounded_rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            radius=8,
            fill=card_bg,
            outline=border_col,
            width=1
        )
        # Accent strip on edge
        accent_x = card_x if is_left_align else (card_x + card_w - 5)
        draw.rounded_rectangle(
            [accent_x, card_y, accent_x + 5, card_y + card_h],
            radius=2,
            fill=theme_color
        )

        # Title & Pin Badge
        tx = card_x + 18 if is_left_align else card_x + 14
        ty = card_y + 10
        draw.text((tx, ty), title, fill=(28, 35, 30), font=font_card_title)

        # Badge pill for GPIO
        badge_text = f" {pin} "
        badge_w = int(draw.textlength(badge_text, font=font_badge)) + 8
        badge_x = card_x + card_w - badge_w - 14 if is_left_align else tx
        badge_y = ty + 2
        if not is_left_align:
            # Shift title right if badge on left
            pass

        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + badge_w, badge_y + 22],
            radius=4,
            fill=(240, 244, 238),
            outline=theme_color,
            width=1
        )
        draw.text((badge_x + 4, badge_y + 2), badge_text, fill=theme_color, font=font_badge)

        # Descriptions
        draw.text((tx, ty + 26), desc, fill=(70, 80, 72), font=font_card_desc)
        draw.text((tx, ty + 46), subdesc, fill=(110, 120, 112), font=font_mono_small)

        # Leader Line
        # Card attach point: middle of facing edge
        attach_x = card_x + card_w if is_left_align else card_x
        attach_y = card_y + card_h // 2

        # Anchor point on switch
        ax, ay = target_pt

        # Anchor graphic: small concentric target
        draw.ellipse([ax - 9, ay - 9, ax + 9, ay + 9], fill=(255, 255, 255, 200), outline=theme_color, width=2)
        draw.ellipse([ax - 4, ay - 4, ax + 4, ay + 4], fill=theme_color)

        # Leader path: target -> elbow -> card edge
        elbow_dx = 30 if is_left_align else -30
        elbow_x = ax - 45 if is_left_align else ax + 45
        elbow_y = attach_y

        draw.line([(ax, ay), (elbow_x, ay), (elbow_x, attach_y), (attach_x, attach_y)],
                  fill=theme_color, width=2)

    # Color palettes for callouts
    COL_LEFT_ARC  = (22, 101, 52)   # Deep Sage Green
    COL_RIGHT_ARC = (15, 118, 110)  # High-Tech Dark Cyan
    COL_THUMB     = (180, 83, 9)    # Deep Amber / Modifier Orange

    # LEFT HAND CALLOUTS (Cards positioned on Left side: X = 70 to 480)
    # Dot 3 (Ring Finger)
    draw_callout(
        target_pt=clusters["dot3"],
        card_x=70, card_y=860, card_w=390, card_h=75,
        title="DOT 3 — LEFT RING", pin="GPIO 13",
        desc="Bit mask 0b000100 • Low Braille Arc",
        subdesc="Internal Pull-up • Active LOW",
        theme_color=COL_LEFT_ARC, is_left_align=True
    )

    # Dot 2 (Middle Finger)
    draw_callout(
        target_pt=clusters["dot2"],
        card_x=70, card_y=755, card_w=390, card_h=75,
        title="DOT 2 — LEFT MIDDLE", pin="GPIO 12",
        desc="Bit mask 0b000010 • Mid Braille Arc",
        subdesc="Internal Pull-up • Active LOW",
        theme_color=COL_LEFT_ARC, is_left_align=True
    )

    # Dot 1 (Index Finger)
    draw_callout(
        target_pt=clusters["dot1"],
        card_x=70, card_y=650, card_w=390, card_h=75,
        title="DOT 1 — LEFT INDEX", pin="GPIO 14",
        desc="Bit mask 0b000001 • Primary Lead Key",
        subdesc="Character Base 'A' / Vowel Lead",
        theme_color=COL_LEFT_ARC, is_left_align=True
    )

    # Space Key (Left Thumb)
    draw_callout(
        target_pt=clusters["space"],
        card_x=70, card_y=965, card_w=400, card_h=75,
        title="SPACE KEY — LEFT THUMB", pin="GPIO 33",
        desc="Word Separator (ASCII 0x20) / Chord Commit",
        subdesc="Thumb ergonomically angled at 15°",
        theme_color=COL_THUMB, is_left_align=True
    )

    # RIGHT HAND CALLOUTS (Cards positioned on Right side: X = 1920 to 2320)
    # Shift Key (Right Thumb)
    draw_callout(
        target_pt=clusters["shift"],
        card_x=1930, card_y=965, card_w=400, card_h=75,
        title="SHIFT / BACKSPACE — RIGHT THUMB", pin="GPIO 32",
        desc="Hold: Shift Layer | Tap: Instant Backspace",
        subdesc="Numbers, Caps & Bangla Yuktakkhor",
        theme_color=COL_THUMB, is_left_align=False
    )

    # Dot 4 (Right Index)
    draw_callout(
        target_pt=clusters["dot4"],
        card_x=1930, card_y=650, card_w=400, card_h=75,
        title="DOT 4 — RIGHT INDEX", pin="GPIO 27",
        desc="Bit mask 0b001000 • Top Right Arc",
        subdesc="Virama / Hasanta / Symbol Modifier",
        theme_color=COL_RIGHT_ARC, is_left_align=False
    )

    # Dot 5 (Right Middle)
    draw_callout(
        target_pt=clusters["dot5"],
        card_x=1930, card_y=755, card_w=400, card_h=75,
        title="DOT 5 — RIGHT MIDDLE", pin="GPIO 26",
        desc="Bit mask 0b010000 • Mid Right Arc",
        subdesc="Internal Pull-up • Active LOW",
        theme_color=COL_RIGHT_ARC, is_left_align=False
    )

    # Dot 6 (Right Ring)
    draw_callout(
        target_pt=clusters["dot6"],
        card_x=1930, card_y=860, card_w=400, card_h=75,
        title="DOT 6 — RIGHT RING", pin="GPIO 25",
        desc="Bit mask 0b100000 • Low Right Arc",
        subdesc="Capital Prefix / Numeric Sign Prefix",
        theme_color=COL_RIGHT_ARC, is_left_align=False
    )

    # 7. Hardware Architecture Spec Badges (Top & Bottom Center)
    # Switch Specs Callout
    sw_target = (dev_x + int(433 * scale), dev_y + int(281 * scale))
    draw.line([(sw_target[0], sw_target[1] - 12), (sw_target[0], dev_y - 40), (1200, dev_y - 40)],
              fill=(100, 115, 105), width=2)
    draw.ellipse([sw_target[0] - 6, sw_target[1] - 18, sw_target[0] + 6, sw_target[1] - 6],
                 fill=(255, 255, 255), outline=(100, 115, 105), width=2)

    # Switch card at (920, 270)
    sw_card_x = 900
    sw_card_y = 260
    draw.rounded_rectangle([sw_card_x, sw_card_y, sw_card_x + 580, sw_card_y + 80],
                           radius=8, fill=(255, 255, 255, 240), outline=(200, 208, 198), width=1)
    draw.rounded_rectangle([sw_card_x, sw_card_y, sw_card_x + 5, sw_card_y + 80],
                           radius=2, fill=(225, 29, 72)) # Outemu Red accent
    draw.text((sw_card_x + 20, sw_card_y + 10), "OUTEMU RED LINEAR SWITCHES", fill=(28, 35, 30), font=font_card_title)
    draw.text((sw_card_x + 20, sw_card_y + 34), "45gf Actuation • 4.0mm Full Travel • 50M Press Lifespan", fill=(70, 80, 72), font=font_card_desc)
    draw.text((sw_card_x + 20, sw_card_y + 54), "Smooth Linear Response for Fatigue-Free Braille Chording", fill=(110, 120, 112), font=font_mono_small)

    # 8. CAD Dimensions Line at the Bottom
    dim_y = dev_y + new_h + 35
    dim_x1 = dev_x + 50
    dim_x2 = dev_x + new_w - 50

    # Dimension line
    draw.line([(dim_x1, dim_y), (dim_x2, dim_y)], fill=(130, 142, 130), width=1)
    draw.line([(dim_x1, dim_y - 8), (dim_x1, dim_y + 8)], fill=(130, 142, 130), width=1)
    draw.line([(dim_x2, dim_y - 8), (dim_x2, dim_y + 8)], fill=(130, 142, 130), width=1)
    dim_label = "◄   180.0 mm OVERALL ENCLOSURE WIDTH (PARAMETRIC CAD)   ►"
    dim_w = int(draw.textlength(dim_label, font=font_mono_regular))
    draw.rectangle([(dim_x1 + dim_x2)//2 - dim_w//2 - 10, dim_y - 12, (dim_x1 + dim_x2)//2 + dim_w//2 + 10, dim_y + 12],
                   fill=BG_COLOR)
    draw.text(((dim_x1 + dim_x2)//2 - dim_w//2, dim_y - 8), dim_label, fill=(90, 105, 92), font=font_mono_regular)

    # 9. Top Engineering Header Block
    header_x = 70
    header_y = 65
    draw.text((header_x, header_y), "BRAILLEBRIDGE™ HARDWARE BREAKDOWN", fill=(24, 40, 30), font=font_title)
    draw.text((header_x, header_y + 45),
              "8-Key Ergonomic Perkins Input Matrix  |  Outemu Red Switches  |  ESP32 Dual-Core Architecture",
              fill=(70, 88, 75), font=font_subtitle)

    # Top Right Technical Specs Box
    spec_x = CANVAS_W - 550
    spec_y = 65
    draw.rounded_rectangle([spec_x, spec_y, spec_x + 480, spec_y + 115],
                           radius=6, fill=(245, 248, 243, 220), outline=(205, 212, 202), width=1)
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

    # 10. Bottom Left / Right Blueprint Metadata Watermark
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

    # Also save to artifact directory so it renders in conversation
    artifact_dir = r"C:\Users\Samin Yeasar\.gemini\antigravity\brain\892defb0-e231-43c2-8bb9-8fd64cc35d5d"
    artifact_path = os.path.join(artifact_dir, "braillebridge_engineered_diagram.png")
    img.save(artifact_path, dpi=(300, 300))
    print(f"Saved artifact to: {artifact_path}")

if __name__ == "__main__":
    create_engineered_graphic()
