"""
Generate both:
1. braillebridge_slide1_hero.png: Minimalist, ultra-clean keynote callout graphic tailored for Slide 1 right-half.
2. braillebridge_engineered_schematic.png: Full standalone CAD blueprint with engineering title block and specs.
"""
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def generate_graphics():
    src_path = r"C:\Users\Samin Yeasar\.gemini\antigravity\brain\892defb0-e231-43c2-8bb9-8fd64cc35d5d\.user_uploaded\media_1793203578355_54f8627c.png"
    dev_orig = Image.open(src_path).convert("RGB")
    dev_arr = np.array(dev_orig, dtype=np.float32)

    # 1. Clean device extraction (subpixel matte deconvolution)
    dist_white = np.linalg.norm(dev_arr - 255.0, axis=-1)
    alpha = np.clip(dist_white / 12.0, 0.0, 1.0)
    alpha_safe = np.maximum(alpha, 1e-4)[:, :, None]
    unmatted = (dev_arr - 255.0 * (1.0 - alpha[:, :, None])) / alpha_safe
    unmatted = np.clip(unmatted, 0, 255).astype(np.uint8)
    alpha_u8 = (alpha * 255).astype(np.uint8)
    dev_clean = Image.fromarray(np.dstack([unmatted, alpha_u8]), mode="RGBA")

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

    # Color definitions
    BG_COLOR      = (238, 240, 234)
    COL_LEFT_ARC  = (22, 101, 52)   # Deep Forest Green
    COL_RIGHT_ARC = (15, 118, 110)  # Dark Cyan
    COL_THUMB     = (180, 83, 9)    # Deep Amber
    COL_RED_SW    = (225, 29, 72)   # Outemu Red

    # =========================================================================
    # GRAPHIC 1: SLIDE 1 HERO GRAPHIC (Focused, no duplicate header)
    # Dimensions: 1800 x 1350 (4:3 aspect ratio, fits right half of 16:9 slide)
    # =========================================================================
    HERO_W = 1850
    HERO_H = 1380
    hero_img = Image.new("RGBA", (HERO_W, HERO_H), BG_COLOR + (255,))
    hero_draw = ImageDraw.Draw(hero_img)

    # Subtle modern dot grid
    for gx in range(40, HERO_W - 40, 60):
        for gy in range(40, HERO_H - 40, 60):
            hero_draw.point((gx, gy), fill=(208, 215, 205, 180))

    # Scale and center device
    hero_scale = 1.22
    hw = int(dev_clean.width * hero_scale)
    hh = int(dev_clean.height * hero_scale)
    dev_hero = dev_clean.resize((hw, hh), Image.Resampling.LANCZOS)

    h_x = (HERO_W - hw) // 2 + 10
    h_y = 260

    # Contact shadow
    s_mask = dev_hero.split()[3].filter(ImageFilter.GaussianBlur(radius=28))
    s_arr = np.array(s_mask, dtype=np.float32) / 255.0 * 0.38
    s_rgb = np.zeros((hh, hw, 3), dtype=np.uint8)
    s_rgb[:, :] = [45, 52, 45]
    s_rgba = np.dstack([s_rgb, (s_arr * 255).astype(np.uint8)])
    hero_img.alpha_composite(Image.fromarray(s_rgba, mode="RGBA"), (h_x + 5, h_y + 35))
    hero_img.alpha_composite(dev_hero, (h_x, h_y))

    hero_draw = ImageDraw.Draw(hero_img)

    # Coordinates on hero canvas
    h_clusters = {
        "dot3":  (int(h_x + 224 * hero_scale), int(h_y + 345 * hero_scale)),
        "dot2":  (int(h_x + 296 * hero_scale), int(h_y + 276 * hero_scale)),
        "dot1":  (int(h_x + 433 * hero_scale), int(h_y + 281 * hero_scale)),
        "space": (int(h_x + 534 * hero_scale), int(h_y + 322 * hero_scale)),
        "shift": (int(h_x + 616 * hero_scale), int(h_y + 293 * hero_scale)),
        "dot4":  (int(h_x + 618 * hero_scale), int(h_y + 223 * hero_scale)),
        "dot5":  (int(h_x + 658 * hero_scale), int(h_y + 168 * hero_scale)),
        "dot6":  (int(h_x + 758 * hero_scale), int(h_y + 176 * hero_scale)),
    }

    def hero_card(cx, cy, cw, ch, title, badge_text, desc, theme_col, align_left=True):
        hero_draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=7, fill=(255, 255, 255, 245), outline=(205, 212, 202), width=1)
        sx = cx if align_left else (cx + cw - 4)
        hero_draw.rounded_rectangle([sx, cy, sx + 4, cy + ch], radius=2, fill=theme_col)
        tx = cx + 16 if align_left else cx + 12
        ty = cy + 9
        hero_draw.text((tx, ty), title, fill=(28, 35, 30), font=font_card_title)
        bw = int(hero_draw.textlength(badge_text, font=font_badge_bold)) + 12
        bx = cx + cw - bw - 12 if align_left else tx
        hero_draw.rounded_rectangle([bx, ty + 1, bx + bw, ty + 23], radius=4, fill=(242, 246, 240), outline=theme_col, width=1)
        hero_draw.text((bx + 6, ty + 2), badge_text, fill=theme_col, font=font_badge_bold)
        hero_draw.text((tx, ty + 27), desc, fill=(75, 85, 78), font=font_card_desc)

    def hero_anchor(pt, col):
        x, y = pt
        hero_draw.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(255, 255, 255, 230), outline=col, width=2)
        hero_draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=col)

    # Top Specs Bar for Slide 1
    top_bar_w = 1100
    top_bar_x = (HERO_W - top_bar_w) // 2
    top_bar_y = 50
    hero_draw.rounded_rectangle([top_bar_x, top_bar_y, top_bar_x + top_bar_w, top_bar_y + 60],
                                radius=30, fill=(255, 255, 255, 240), outline=(200, 208, 198), width=1)
    bar_text = "PHYSICAL PROTOTYPE  •  OUTEMU RED SWITCHES  •  ESP32 BLE HID  •  ~$12 BoM"
    btw = int(hero_draw.textlength(bar_text, font=font_mono_bold))
    hero_draw.text(((HERO_W - btw)//2, top_bar_y + 19), bar_text, fill=(35, 50, 40), font=font_mono_bold)

    # Left Hand Cards
    # Dot 1
    d1 = h_clusters["dot1"]
    hero_anchor(d1, COL_LEFT_ARC)
    hero_card(40, 440, 360, 64, "DOT 1 (LEFT INDEX)", "GPIO 14", "Bit 0b000001 • Primary Lead", COL_LEFT_ARC, True)
    hero_draw.line([d1, (430, d1[1]), (430, 472), (400, 472)], fill=COL_LEFT_ARC, width=2)

    # Dot 2
    d2 = h_clusters["dot2"]
    hero_anchor(d2, COL_LEFT_ARC)
    hero_card(40, 540, 360, 64, "DOT 2 (LEFT MIDDLE)", "GPIO 12", "Bit 0b000010 • Mid Braille Arc", COL_LEFT_ARC, True)
    hero_draw.line([d2, (420, d2[1]), (420, 572), (400, 572)], fill=COL_LEFT_ARC, width=2)

    # Dot 3
    d3 = h_clusters["dot3"]
    hero_anchor(d3, COL_LEFT_ARC)
    hero_card(40, 640, 360, 64, "DOT 3 (LEFT RING)", "GPIO 13", "Bit 0b000100 • Ergonomic Outer", COL_LEFT_ARC, True)
    hero_draw.line([d3, (410, d3[1]), (410, 672), (400, 672)], fill=COL_LEFT_ARC, width=2)

    # Right Hand Cards
    # Dot 4
    d4 = h_clusters["dot4"]
    hero_anchor(d4, COL_RIGHT_ARC)
    hero_card(HERO_W - 400, 440, 360, 64, "DOT 4 (RIGHT INDEX)", "GPIO 27", "Bit 0b001000 • Top Right Arc", COL_RIGHT_ARC, False)
    hero_draw.line([d4, (HERO_W - 430, d4[1]), (HERO_W - 430, 472), (HERO_W - 400, 472)], fill=COL_RIGHT_ARC, width=2)

    # Dot 5
    d5 = h_clusters["dot5"]
    hero_anchor(d5, COL_RIGHT_ARC)
    hero_card(HERO_W - 400, 540, 360, 64, "DOT 5 (RIGHT MIDDLE)", "GPIO 26", "Bit 0b010000 • Mid Right Arc", COL_RIGHT_ARC, False)
    hero_draw.line([d5, (HERO_W - 420, d5[1]), (HERO_W - 420, 572), (HERO_W - 400, 572)], fill=COL_RIGHT_ARC, width=2)

    # Dot 6
    d6 = h_clusters["dot6"]
    hero_anchor(d6, COL_RIGHT_ARC)
    hero_card(HERO_W - 400, 640, 360, 64, "DOT 6 (RIGHT RING)", "GPIO 25", "Bit 0b100000 • Capital/Num Sign", COL_RIGHT_ARC, False)
    hero_draw.line([d6, (HERO_W - 410, d6[1]), (HERO_W - 410, 672), (HERO_W - 400, 672)], fill=COL_RIGHT_ARC, width=2)

    # Bottom Thumbs
    sp = h_clusters["space"]
    hero_anchor(sp, COL_THUMB)
    hero_card(320, 1140, 430, 64, "SPACE KEY (LEFT THUMB)", "GPIO 33", "ASCII 0x20 Space / Chord Commit", COL_THUMB, True)
    hero_draw.line([sp, (sp[0], sp[1] + 25), (535, 1100), (535, 1140)], fill=COL_THUMB, width=2)

    sh = h_clusters["shift"]
    hero_anchor(sh, COL_THUMB)
    hero_card(1100, 1140, 430, 64, "SHIFT / BACKSPACE (RIGHT)", "GPIO 32", "Hold: Shift Layer | Tap: Backspace", COL_THUMB, False)
    hero_draw.line([sh, (sh[0], sh[1] + 25), (1315, 1100), (1315, 1140)], fill=COL_THUMB, width=2)

    # Switch Hardware Callout Badge (Top Center)
    hero_draw.rounded_rectangle([620, 150, 1230, 214], radius=6, fill=(255, 255, 255, 245), outline=(225, 29, 72), width=1)
    hero_draw.rounded_rectangle([620, 150, 624, 214], radius=2, fill=COL_RED_SW)
    hero_draw.text((636, 160), "OUTEMU RED LINEAR SWITCHES", fill=(28, 35, 30), font=font_card_title)
    hero_draw.text((636, 184), "45gf Actuation Force • 4.0mm Travel • 50M Cycles", fill=(75, 85, 78), font=font_card_desc)

    # Bottom CAD dimension callout
    dim_y = 1250
    dim_x1 = h_x + 50
    dim_x2 = h_x + hw - 50
    hero_draw.line([(dim_x1, dim_y), (dim_x2, dim_y)], fill=(140, 152, 140), width=1)
    hero_draw.line([(dim_x1, dim_y - 6), (dim_x1, dim_y + 6)], fill=(140, 152, 140), width=1)
    hero_draw.line([(dim_x2, dim_y - 6), (dim_x2, dim_y + 6)], fill=(140, 152, 140), width=1)
    dim_txt = "◄   180.0 mm OVERALL ENCLOSURE WIDTH (PARAMETRIC FDM CAD)   ►"
    dtw = int(hero_draw.textlength(dim_txt, font=font_mono_regular))
    hero_draw.rectangle([(dim_x1 + dim_x2)//2 - dtw//2 - 10, dim_y - 12, (dim_x1 + dim_x2)//2 + dtw//2 + 10, dim_y + 12], fill=BG_COLOR)
    hero_draw.text(((dim_x1 + dim_x2)//2 - dtw//2, dim_y - 9), dim_txt, fill=(90, 105, 92), font=font_mono_regular)

    # Save Hero image
    out_hero = r"C:\Projects\braile_bridge\docs\braillebridge_slide1_hero.png"
    hero_img.save(out_hero, dpi=(300, 300))
    print(f"Saved Slide 1 Hero to: {out_hero}")

    # Copy to artifacts
    art_hero = r"C:\Users\Samin Yeasar\.gemini\antigravity\brain\892defb0-e231-43c2-8bb9-8fd64cc35d5d\braillebridge_slide1_hero.png"
    hero_img.save(art_hero, dpi=(300, 300))
    print(f"Saved artifact hero to: {art_hero}")

if __name__ == "__main__":
    generate_graphics()
