#!/usr/bin/env python3
"""
BrailleBridge 1 - WEDGE shells, Option C  (front 24 mm -> back 40 mm, 11.3 deg tilt)
====================================================================================
Usage:  python3 bb1_wedge_shells.py OUTDIR            (writes BOTTOM, TOP, TOP_PRINT, LID stl files)
Needs:  numpy, scikit-image          (pip install numpy scikit-image)

Same 180 x 80 mm outline with R12 corners and the same 8 key positions as your FINAL_BRAILLE_TOP / BOTTOM.
  BOTTOM   flat floor on the table, walls up to the seam (z=16), AA-holder hatch + lid recess, GND-rail pocket,
           slide-switch pocket + lever slot, USB hole, hinge knuckles (back), snap-latch recesses (front).
  TOP      sloped key plate (2.5 mm), 8 key holes cut square to the sloped plate, hinge knuckles, 2 snap tabs.
  TOP_PRINT = TOP rotated so the key-plate face lies flat on the bed (print it as is, supports only for the hinge/tabs if the slicer asks).
  LID      battery lid (plate + plug + 6 crush ribs)
Hinge pin: a piece of 1.75 mm filament, 150 mm long.
Coordinates (device frame): X long side -50..130, Y across -50 (front, your hands) .. 30 (back), Z up from the table.
"""
import sys, os, struct
import numpy as np
from functools import reduce
from skimage.measure import marching_cubes

# ------------------------------------------------------------------ PARAMETERS
RES = 0.25                         # mesh resolution (mm)
X0, X1, Y0, Y1, R = -50.0, 130.0, -50.0, 30.0, 12.0
WALL, FLOOR, PLATE = 2.5, 2.5, 2.5
HF, HB = 24.0, 40.0                # option C: height at the front / at the back
P = 16.0                           # seam height (bottom shell is 16 mm tall, USB hole top is 14.46)
TONGUE_H, TONGUE_IN, GROOVE_OUT = 3.0, 1.45, 1.25     # lip: tongue sits between sd -2.5 and -1.45; top wall keeps sd > -1.25
S = (HB - HF) / (Y1 - Y0); TH = np.arctan(S); CT, ST = np.cos(TH), np.sin(TH)
H = lambda y: HF + S * (y - Y0)

HOLE = (4.993984222412109, 24.99398422241211, 4.456787586212158, 14.456788063049316)   # USB hole in the front wall
SX, SZ = 45.0, 12.0                                   # slide switch (RadioGear 8.5 x 4)
SW_L, SW_W, SW_CLR, SW_D, SLOT_L, SLOT_H = 8.5, 4.0, 0.4, 1.2, 7.4, 2.8

# AA holder 62 x 58 x 15 (open face down on two 3 mm ledges)
CASE_L, CASE_W, CASE_CLR = 62.0, 58.0, 0.5
PK_X1, PK_Y1 = 123.5, 23.0
LEDGE_X = 3.0
BR_H, BR_LEG, BR_T = 8.0, 10.0, 1.2
RECESS_D, RM_X, RM_F, RM_B = 1.0, 1.5, 6.0, 1.5
LID_GAP, PLUG_TOP, RIB = 0.15, 2.3, 0.25
FINGER_SLOT, FP_DEPTH = (12.0, 2.8), 1.8

# GND rail  11 (end) x 80 (long) x 11 (deep) - pocket against the back wall, back-left
RAIL_L, RAIL_W, RAIL_H, RAIL_CLR = 80.0, 11.0, 11.0, 0.5
RAIL_X0, RAIL_Y1 = -39.0, 27.0
RAIL_BR_H, RAIL_BR_LEG = 7.0, 8.0

# keys: same positions as FINAL_BRAILLE_TOP (translated by +50, -70), hole 20 x 14.2 cut square to the plate
KEYS = [(5.9,25.9,55,69.2),(-66.9,-46.9,68,82.2),(-42.1,-22.1,55,69.2),(26.9,46.9,68,82.2),
        (-7.1,12.9,35,49.2),(-87.9,-67.9,55,69.2),(-29.1,-9.1,35,49.2),(47.9,67.9,55,69.2)]
KEYS = [((a+b)/2 + 50, (c+d)/2 - 70) for a, b, c, d in KEYS]
KEY_X, KEY_Y = 20.0, 14.2

# hinge (back edge, pin = 1.75 mm filament)
HG_R, HG_BORE = 3.2, 1.05
HG_YA = 30.0 + HG_R + 0.4
HG_SEG, HG_GAP, HG_X0, HG_N = 30.0, 0.5, -36.0, 5

# front snap latches (cantilever tab on TOP, recess + groove on BOTTOM)
LATCH_X = (-24.0, 98.0)
TAB_W, TAB_T, TAB_Z0, REC_W, REC_D = 14.0, 0.9, 5.5, 16.0, 1.2
HOOK = [(0.0, 5.5), (0.7, 6.2), (0.7, 6.5), (0.0, 7.2)]       # (inward, z) relative to the tab inner face
GROOVE_W, GROOVE_D, GROOVE_Z = 12.0, 0.7, (5.3, 7.4)
PAD = 1.5
NOTCH_X = 66.0

# ------------------------------------------------------------------ SDF helpers (negative = inside), float32
f32 = np.float32
def grid(zr):
    X = np.arange(-51.0, 131.0 + RES / 2, RES, dtype=np.float64)
    Y = np.arange(-51.0, 38.0 + RES / 2, RES, dtype=np.float64)
    Z = np.arange(zr[0], zr[1] + RES / 2, RES, dtype=np.float64)
    return X, Y, Z

def sd_plan(X, Y):
    qx = np.abs(X[:, None] - (X0 + X1) / 2) - ((X1 - X0) / 2 - R)
    qy = np.abs(Y[None, :] - (Y0 + Y1) / 2) - ((Y1 - Y0) / 2 - R)
    return (np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - R).astype(f32)

class Vol:
    def __init__(self, zr):
        self.X, self.Y, self.Z = grid(zr)
        self.SD = sd_plan(self.X, self.Y)
    def base(self):
        Y, Z, SD = self.Y, self.Z, self.SD
        Zb = Z[None, None, :].astype(f32)
        tp = ((Zb - H(Y)[None, :, None].astype(f32)) * f32(CT))
        A = np.maximum(np.maximum(SD[:, :, None], -Zb), tp)
        C = np.maximum(np.maximum(SD[:, :, None] + f32(WALL), f32(FLOOR) - Zb), tp + f32(PLATE))
        return np.maximum(A, -C)
    def sl(self, ax, lo, hi):
        a = self.__dict__[ax]; i0 = max(0, int(np.floor((lo - a[0]) / RES))); i1 = min(len(a), int(np.ceil((hi - a[0]) / RES)) + 1)
        return slice(i0, max(i0, i1))
    def op(self, f, bx, fn, add):
        sx, sy, sz = self.sl('X', bx[0], bx[1]), self.sl('Y', bx[2], bx[3]), self.sl('Z', bx[4], bx[5])
        if sx.stop <= sx.start or sy.stop <= sy.start or sz.stop <= sz.start: return
        Xl = self.X[sx, None, None]; Yl = self.Y[None, sy, None]; Zl = self.Z[None, None, sz]
        g = fn(Xl, Yl, Zl).astype(f32); sub = f[sx, sy, sz]
        if add: np.minimum(sub, g, out=sub)
        else: np.maximum(sub, -g, out=sub)
    def box(self, f, b, add):
        x0, x1, y0, y1, z0, z1 = b
        self.op(f, (x0 - 1, x1 + 1, y0 - 1, y1 + 1, z0 - 1, z1 + 1),
                lambda X, Y, Z: reduce(np.maximum, [x0 - X, X - x1, y0 - Y, Y - y1, z0 - Z, Z - z1]), add)
    def cylx(self, f, x0, x1, yc, zc, r, add):
        self.op(f, (x0 - 1, x1 + 1, yc - r - 1, yc + r + 1, zc - r - 1, zc + r + 1),
                lambda X, Y, Z: reduce(np.maximum, [np.hypot(Y - yc, Z - zc) - r, x0 - X, X - x1]), add)
    def polyx(self, f, x0, x1, poly, add):
        poly = np.array(poly, float)
        if 0.5 * np.sum(poly[:, 0] * np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1) * poly[:, 1]) < 0: poly = poly[::-1]
        ys, zs = poly[:, 0], poly[:, 1]
        def fn(X, Y, Z):
            terms = [x0 - X, X - x1]
            for i in range(len(poly)):
                j = (i + 1) % len(poly); dy, dz = ys[j] - ys[i], zs[j] - zs[i]; L = np.hypot(dy, dz)
                terms.append((dz * (Y - ys[i]) - dy * (Z - zs[i])) / L)
            return reduce(np.maximum, terms)
        self.op(f, (x0 - 1, x1 + 1, ys.min() - 1, ys.max() + 1, zs.min() - 1, zs.max() + 1), fn, add)
    def brackets(self, f, rect, zt, leg, t, z0=FLOOR - 0.3):
        x0, x1, y0, y1 = rect
        for cx, sx in ((x0, 1), (x1, -1)):
            for cy, sy in ((y0, 1), (y1, -1)):
                xa, xb = sorted([cx - sx * t, cx + sx * leg]); ya, yb = sorted([cy - sy * t, cy])
                xc, xd = sorted([cx - sx * t, cx]); yc, yd = sorted([cy - sy * t, cy + sy * leg])
                self.box(f, (xa, xb, ya, yb, z0, zt), True); self.box(f, (xc, xd, yc, yd, z0, zt), True)

def mesh(f, V, level=1e-3):
    v, fc, _, _ = marching_cubes(f, level, spacing=(RES,) * 3)
    v = v.astype(np.float64) + np.array([V.X[0], V.Y[0], V.Z[0]])
    T = v[fc]
    vol = np.sum(np.einsum('ij,ij->i', T[:, 0], np.cross(T[:, 1], T[:, 2]))) / 6
    if vol < 0: T = T[:, ::-1]
    return T.astype(np.float32), abs(vol)

def write_stl(path, T, name):
    T = T.astype(np.float32)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    r = np.zeros(len(T), dtype=np.dtype([('n', '<3f4'), ('v', '<9f4'), ('a', '<u2')])); r['n'] = n; r['v'] = T.reshape(-1, 9)
    open(path, 'wb').write(name.encode().ljust(80, b'\0') + struct.pack('<I', len(T)) + r.tobytes())

def layout():
    px1, py1 = PK_X1, PK_Y1; px0, py0 = px1 - CASE_L - CASE_CLR, py1 - CASE_W - CASE_CLR
    cx = (px0 + px1) / 2; hl = CASE_L + CASE_CLR - 2 * LEDGE_X
    hatch = (cx - hl / 2, cx + hl / 2, py0, py1)
    recess = (hatch[0] - RM_X, hatch[1] + RM_X, hatch[2] - RM_F, hatch[3] + RM_B)
    fx0, fx1 = cx - FINGER_SLOT[0] / 2, cx + FINGER_SLOT[0] / 2
    fy1 = hatch[2] - 1.8; fy0 = fy1 - FINGER_SLOT[1]
    return dict(pocket=(px0, px1, py0, py1), hatch=hatch, recess=recess, slot=(fx0, fx1, fy0, fy1),
                fpocket=(fx0 - .8, fx1 + .8, fy0 - .4, fy1 + .8),
                rail=(RAIL_X0, RAIL_X0 + RAIL_L + RAIL_CLR, RAIL_Y1 - RAIL_W - RAIL_CLR, RAIL_Y1))

def hinge_segments():
    return [(HG_X0 + i * (HG_SEG + HG_GAP), HG_X0 + i * (HG_SEG + HG_GAP) + HG_SEG) for i in range(HG_N)]

# ------------------------------------------------------------------ BOTTOM
def build_bottom():
    L = layout(); V = Vol((-0.75, P + TONGUE_H + 0.75)); f = V.base()
    Zb = V.Z[None, None, :].astype(f32); SD3 = V.SD[:, :, None]
    np.maximum(f, Zb - f32(P), out=f)                                         # keep z <= P
    T = np.maximum.reduce([SD3 + f32(TONGUE_IN), -(SD3 + f32(WALL)), Zb - f32(P + TONGUE_H)]) if False else \
        np.maximum(np.maximum(SD3 + f32(TONGUE_IN), -(SD3 + f32(WALL))), np.maximum(Zb - f32(P + TONGUE_H), f32(P - 0.6) - Zb))
    np.minimum(f, T, out=f); del T                                            # lip (tongue) on the inner half of the wall
    # USB hole, slide-switch pocket + lever slot
    V.box(f, (HOLE[0], HOLE[1], -51.5, -47.0, HOLE[2], HOLE[3]), False)
    V.box(f, (SX - (SW_L + SW_CLR) / 2, SX + (SW_L + SW_CLR) / 2, -47.5 - SW_D, -47.0, SZ - (SW_W + SW_CLR) / 2, SZ + (SW_W + SW_CLR) / 2), False)
    V.box(f, (SX - SLOT_L / 2, SX + SLOT_L / 2, -51.5, -47.4 - SW_D, SZ - SLOT_H / 2, SZ + SLOT_H / 2), False)
    hh = (SW_L + SW_CLR) / 2                                                   # switch support (pillar + 2 tabs)
    V.box(f, (SX - hh - 1.5, SX + hh + 1.5, -47.4, -43.5, 2.2, SZ - SW_W / 2 - 0.2), True)
    V.box(f, (SX - hh - 1.5, SX - hh, -47.4, -44.5, 2.2, SZ + 1.8), True)
    V.box(f, (SX + hh, SX + hh + 1.5, -47.4, -44.5, 2.2, SZ + 1.8), True)
    # AA hatch, lid recess, finger pocket, holder brackets
    V.box(f, (*L['hatch'][:2], *L['hatch'][2:], -1.0, FLOOR + 1.0), False)
    V.box(f, (*L['recess'][:2], *L['recess'][2:], -1.0, RECESS_D), False)
    V.box(f, (*L['fpocket'][:2], *L['fpocket'][2:], -1.0, FP_DEPTH), False)
    V.brackets(f, L['pocket'], FLOOR + BR_H, BR_LEG, BR_T)
    # GND rail pocket
    V.brackets(f, L['rail'], FLOOR + RAIL_BR_H, RAIL_BR_LEG, BR_T)
    # front latches: recess in the outer face, groove, inner pad ; finger notch
    for lx in LATCH_X:
        V.box(f, (lx - PAD / 2 - REC_W / 2 + 0.75, lx + REC_W / 2 - 0.75 + PAD / 2 - 0.75, -47.5, -47.5 + PAD, FLOOR - 0.3, P), True)   # pad (x +-8)
        V.box(f, (lx - REC_W / 2, lx + REC_W / 2, -51.5, -50.0 + REC_D, TAB_Z0 - 0.5, P + 1.0), False)                                # recess
        V.box(f, (lx - GROOVE_W / 2, lx + GROOVE_W / 2, -50.0 + REC_D - 0.1, -50.0 + REC_D + GROOVE_D, GROOVE_Z[0], GROOVE_Z[1]), False)  # groove
    V.box(f, (NOTCH_X - 7, NOTCH_X + 7, -51.5, -49.0, P - 3.0, P + 1.0), False)
    # hinge: bottom knuckles (segments 0,2,4) with web, bore through the lot
    segs = hinge_segments()
    for i, (a, b) in enumerate(segs):
        if i % 2: continue
        V.cylx(f, a, b, HG_YA, P, HG_R, True)
        V.box(f, (a, b, 29.5, HG_YA + HG_R, P - 9.0, P - HG_R + 0.3), True)
        V.box(f, (a, b, 29.5, HG_YA, P - HG_R, P), True)
    V.cylx(f, segs[0][0] - 1, segs[-1][1] + 1, HG_YA, P, HG_BORE, False)
    T, vol = mesh(f, V); return T, vol, (V, f)

# ------------------------------------------------------------------ TOP
def build_top():
    V = Vol((TAB_Z0 - 0.75, HB + 1.0)); f = V.base()
    Zb = V.Z[None, None, :].astype(f32); SD3 = V.SD[:, :, None]
    np.maximum(f, f32(P) - Zb, out=f)                                         # keep z >= P
    G = np.maximum(SD3 + f32(GROOVE_OUT), Zb - f32(P + TONGUE_H + 0.3)); np.maximum(f, -G, out=f); del G   # groove for the tongue
    # key holes, cut square to the sloped plate
    for kx, ky in KEYS:
        hc = H(ky)
        def fn(X, Y, Z, kx=kx, ky=ky, hc=hc):
            u = X - kx; v = (Y - ky) * CT + (Z - hc) * ST; w = -(Y - ky) * ST + (Z - hc) * CT
            return reduce(np.maximum, [np.abs(u) - KEY_X / 2, np.abs(v) - KEY_Y / 2, np.abs(w) - 8.0])
        V.op(f, (kx - 14, kx + 14, ky - 14, ky + 14, hc - 12, hc + 12), fn, False)
    # front snap tabs (hang below the seam) + hooks
    for lx in LATCH_X:
        V.box(f, (lx - TAB_W / 2, lx + TAB_W / 2, -50.0, -50.0 + TAB_T, TAB_Z0, P + 1.2), True)
        poly = [(-50.0 + TAB_T - 0.05 + a, z) for a, z in HOOK]
        V.polyx(f, lx - TAB_W / 2, lx + TAB_W / 2, poly, True)
    # hinge: top knuckles (segments 1,3) with web above the seam
    segs = hinge_segments()
    for i, (a, b) in enumerate(segs):
        if i % 2 == 0: continue
        V.cylx(f, a, b, HG_YA, P, HG_R, True)
        V.box(f, (a, b, 29.5, HG_YA, P, P + HG_R), True)
    V.cylx(f, segs[0][0] - 1, segs[-1][1] + 1, HG_YA, P, HG_BORE, False)
    T, vol = mesh(f, V); return T, vol, (V, f)

def print_orientation(T):
    """rotate TOP so the sloped key-plate face lies flat on the bed (plate down)"""
    T = T.astype(np.float64).copy(); x, y, z = T[..., 0].copy(), T[..., 1].copy(), T[..., 2].copy()
    y2 = y * CT + z * ST; z2 = -y * ST + z * CT                 # plate normal -> +Z
    T[..., 0] = -x; T[..., 1] = y2; T[..., 2] = -z2             # flip over (rotation 180 deg about Y): plate face on the bed
    T[..., 2] -= T[..., 2].min()
    return T.astype(np.float32)

# ------------------------------------------------------------------ LID (same as the AA version)
def box_tris(x0, x1, y0, y1, z0, z1):
    v = np.array([[x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0],[x0,y0,z1],[x1,y0,z1],[x1,y1,z1],[x0,y1,z1]], float)
    f = [(0,3,2),(0,2,1),(4,5,6),(4,6,7),(0,1,5),(0,5,4),(1,2,6),(1,6,5),(2,3,7),(2,7,6),(3,0,4),(3,4,7)]
    return np.array([v[list(t)] for t in f])

def build_lid():
    L = layout(); r, h = L['recess'], L['hatch']; g = LID_GAP; o = 0.2
    px0, px1, py0, py1 = r[0] + g, r[1] - g, r[2] + g, r[3] - g; s = L['slot']
    plate = [(px0, px1, py0, s[2], 0, RECESS_D), (px0, px1, s[3], py1, 0, RECESS_D),
             (px0, s[0], s[2] - o, s[3] + o, 0, RECESS_D), (s[1], px1, s[2] - o, s[3] + o, 0, RECESS_D)]
    hx0, hx1, hy0, hy1 = h[0] + g, h[1] - g, h[2] + g, h[3] - g
    plug = [(hx0, hx1, hy0, hy1, RECESS_D - 0.2, PLUG_TOP)]
    cx = (h[0] + h[1]) / 2; cy = (h[2] + h[3]) / 2; zt = PLUG_TOP - 0.2; ribs = []
    for dx in (-12, 12):
        ribs.append((cx + dx - 3, cx + dx + 3, hy0 - RIB, hy0 + o, RECESS_D, zt)); ribs.append((cx + dx - 3, cx + dx + 3, hy1 - o, hy1 + RIB, RECESS_D, zt))
    ribs.append((hx0 - RIB, hx0 + o, cy - 3, cy + 3, RECESS_D, zt)); ribs.append((hx1 - o, hx1 + RIB, cy - 3, cy + 3, RECESS_D, zt))
    return np.concatenate([box_tris(*q) for q in plate + plug + ribs]).astype(np.float32)

def main(out):
    os.makedirs(out, exist_ok=True)
    T, vol, _ = build_bottom(); write_stl(f'{out}/BB1_WEDGE_BOTTOM.stl', T, 'BB1 wedge bottom'); print('bottom', len(T), 'tris', round(vol), 'mm3')
    T, vol, _ = build_top(); write_stl(f'{out}/BB1_WEDGE_TOP.stl', T, 'BB1 wedge top'); print('top', len(T), 'tris', round(vol), 'mm3')
    write_stl(f'{out}/BB1_WEDGE_TOP_PRINT.stl', print_orientation(T), 'BB1 wedge top, print orientation')
    write_stl(f'{out}/BB1_WEDGE_LID.stl', build_lid(), 'BB1 AA lid')

if __name__ == '__main__':
    if len(sys.argv) != 2: sys.exit(__doc__)
    main(sys.argv[1])
