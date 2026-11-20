"""
Render a high-resolution (>=2000 px wide) light-background 2D composite PNG
from any KiCad PCB showing F.Cu (red), B.Cu (blue), plated pads/vias (plum),
translucent GND copper pours, F.Silkscreen, and Edge.Cuts.

Usage:
  python render_2d_composite.py <input.kicad_pcb> <output.png> [title]
"""
import os
import subprocess
import sys
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import pymupdf

KICAD_CLI = os.environ.get(
    "KICAD_CLI",
    r"C:\Users\Samin Yeasar\AppData\Local\Programs\KiCad\10.0\bin\kicad-cli.exe",
)
KICAD_PY = os.environ.get(
    "KICAD_PY",
    r"C:\Users\Samin Yeasar\AppData\Local\Programs\KiCad\10.0\bin\python.exe",
)


def render_pdf_mask(pdf_path: str, dpi: int = 800) -> np.ndarray:
    doc = pymupdf.open(pdf_path)
    pix = doc[0].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    doc.close()
    return arr < 180


def alpha_blend(dst: np.ndarray, mask: np.ndarray, rgb: list[int], alpha: float) -> None:
    c = np.array(rgb, dtype=np.float32)
    dst[mask] = dst[mask] * (1.0 - alpha) + c * alpha


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python render_2d_composite.py <input.kicad_pcb> <output.png> [title]")
        sys.exit(1)

    pcb_path = os.path.abspath(sys.argv[1])
    out_png = os.path.abspath(sys.argv[2])
    title = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(pcb_path)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_nofill = os.path.join(tmp, "nofill.kicad_pcb")
        subprocess.run(
            [
                KICAD_PY,
                "-c",
                f"import pcbnew; b=pcbnew.LoadBoard(r'{pcb_path}'); "
                f"[b.Delete(z) for z in list(b.Zones()) if not z.GetIsRuleArea()]; "
                f"b.Save(r'{tmp_nofill}')",
            ],
            check=True,
        )

        pdfs = {}
        cfg = [
            ("bcu_pour", pcb_path, "B.Cu,Edge.Cuts", True),
            ("fcu_pour", pcb_path, "F.Cu,Edge.Cuts", True),
            ("bcu_tr", tmp_nofill, "B.Cu,Edge.Cuts", True),
            ("fcu_tr", tmp_nofill, "F.Cu,Edge.Cuts", True),
            ("fsilk", pcb_path, "F.Silkscreen,Edge.Cuts", False),
            ("edge", pcb_path, "Edge.Cuts", False),
        ]
        for key, src, layers, drills in cfg:
            pdf_out = os.path.join(tmp, f"{key}.pdf")
            subprocess.run(
                [
                    KICAD_CLI, "pcb", "export", "pdf",
                    "--layers", layers, "--black-and-white", "--mode-single",
                    "--scale", "1", "--drill-shape-opt", "2" if drills else "0",
                    "--output", pdf_out, src,
                ],
                check=True,
            )
            pdfs[key] = pdf_out

        m_edge = render_pdf_mask(pdfs["edge"])
        m_bpour = render_pdf_mask(pdfs["bcu_pour"]) ^ m_edge
        m_fpour = render_pdf_mask(pdfs["fcu_pour"]) ^ m_edge
        m_btr = render_pdf_mask(pdfs["bcu_tr"]) ^ m_edge
        m_ftr = render_pdf_mask(pdfs["fcu_tr"]) ^ m_edge
        m_silk = render_pdf_mask(pdfs["fsilk"]) ^ m_edge

    ys, xs = np.where(m_edge)
    pad = 70
    y0, y1 = max(0, ys.min() - pad), min(m_edge.shape[0], ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(m_edge.shape[1], xs.max() + pad)
    crop = lambda m: m[y0:y1, x0:x1]

    me, mb_p, mf_p = crop(m_edge), crop(m_bpour), crop(m_fpour)
    mb_t, mf_t, ms = crop(m_btr), crop(m_ftr), crop(m_silk)

    canvas = np.full((me.shape[0], me.shape[1], 3), [248, 249, 251], dtype=np.float32)
    alpha_blend(canvas, mb_p & (~mb_t), [59, 130, 246], 0.14)
    alpha_blend(canvas, mf_p & (~mf_t), [239, 68, 68], 0.12)
    alpha_blend(canvas, mb_t, [29, 99, 220], 0.88)
    alpha_blend(canvas, mf_t, [217, 38, 38], 0.90)
    alpha_blend(canvas, mf_t & mb_t, [152, 58, 178], 0.92)
    canvas[me] = [20, 23, 30]
    canvas[ms] = [15, 18, 24]

    img = Image.fromarray(canvas.astype(np.uint8), mode="RGB")
    target_w = 2000
    target_h = int(me.shape[0] * (target_w / me.shape[1]))
    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

    out_img = Image.new("RGB", (target_w, target_h + 165), (248, 249, 251))
    out_img.paste(img, (0, 80))
    draw = ImageDraw.Draw(out_img)
    try:
        font_t = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 30)
        font_s = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 22)
    except Exception:
        font_t = ImageFont.load_default()
        font_s = font_t

    draw.text((48, 22), title, fill=(22, 24, 30), font=font_t)
    lx = 48
    ly = target_h + 104
    for col, lbl in (
        ((217, 38, 38), "F.Cu Tracks + Pour Tint"),
        ((29, 99, 220), "B.Cu Tracks + Pour Tint"),
        ((152, 58, 178), "Plated Through-Hole Pads / Vias"),
        ((15, 18, 24), "F.Silkscreen + Edge.Cuts"),
    ):
        draw.rectangle([lx, ly + 4, lx + 26, ly + 26], fill=col, outline=(60, 60, 70), width=1)
        draw.text((lx + 36, ly), lbl, fill=(35, 38, 45), font=font_s)
        lx += 445

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    out_img.save(out_png)
    print("Saved:", out_png, out_img.size)


if __name__ == "__main__":
    main()
