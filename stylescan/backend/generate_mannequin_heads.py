"""
generate_mannequin_heads.py  v3
Siluetas limpias: descenso lateral paramétrico (sin bezier = sin alas),
sin orejas salientes en vista frontal/trasera.
"""
import math
import os
from PIL import Image, ImageDraw

OUT_DIR = r"c:/Users/Pc2025/Desktop/ANTIGRAVITY/stylescan/backend/knowledge_base/haircut_illustrations"
W, H = 400, 500
BG = (255, 255, 255)
HEAD_FILL = (45, 45, 45)
HEAD_STROKE = (10, 10, 10)
STROKE_W = 6
SCALE = 3
SW, SH = W * SCALE, H * SCALE
CX, CY = 200, 175

os.makedirs(OUT_DIR, exist_ok=True)


def canvas():
    img = Image.new("RGB", (SW, SH), BG)
    return img, ImageDraw.Draw(img)


def out(img):
    return img.resize((W, H), Image.LANCZOS)


def sc(v):
    return int(round(v * SCALE))


def cbez(p0, p1, p2, p3, n=80):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u**3*p0[0] + 3*u**2*t*p1[0] + 3*u*t**2*p2[0] + t**3*p3[0]
        y = u**3*p0[1] + 3*u**2*t*p1[1] + 3*u*t**2*p2[1] + t**3*p3[1]
        pts.append((x, y))
    return pts


def draw_filled(draw, pts, fill, stroke, sw):
    ipts = [(int(x), int(y)) for x, y in pts]
    if len(ipts) >= 3:
        draw.polygon(ipts, fill=fill)
        draw.line(ipts + [ipts[0]], fill=stroke, width=sw * SCALE)


# ── PARÁMETROS ──────────────────────────────────────────────────────────────
#  rx        = radio horizontal cráneo en ecuador (cy)
#  ry        = radio vertical cráneo
#  jaw_w     = semiancho en línea de mandíbula
#  jaw_drop  = distancia cy → jaw_y  (px)
#  chin_drop = distancia cy → chin_y (px)   siempre > jaw_drop
#  ang       = 0.0 redondo … 1.0 cuadrado
FRONT_P = {
    #                      rx   ry  jaw_w jaw_drop chin_drop  ang
    "oval_balanced":    ( 82, 100,   66,    28,      88,    0.20),
    "oval_elongated":   ( 68, 125,   56,    38,     112,    0.18),
    "oval_wide":        (108, 100,   90,    28,      88,    0.20),
    "round_balanced":   ( 92,  90,   84,    12,      76,    0.05),
    "round_wide":       (116,  90,  106,    12,      76,    0.05),
    "square_balanced":  ( 86, 100,   84,    26,      88,    0.88),
    "square_wide":      (110, 100,  108,    24,      88,    0.92),
    "oblong_balanced":  ( 68, 122,   58,    36,     108,    0.25),
    "oblong_elongated": ( 58, 148,   48,    48,     132,    0.22),
    "heart_balanced":   ( 96, 106,   56,    26,      96,    0.10),
    "diamond_balanced": ( 80, 112,   66,     6,      96,    0.12),
    "triangle_balanced":( 74,  98,   88,    20,      88,    0.78),
}

SIDE_P = {
    #                      fw   fh  jaw_fwd brow chin_fwd
    "oval_balanced":    ( 140, 205,  0.38,  0.28,  0.32),
    "oval_elongated":   ( 120, 248,  0.36,  0.24,  0.30),
    "oval_wide":        ( 168, 205,  0.38,  0.28,  0.32),
    "round_balanced":   ( 155, 180,  0.24,  0.14,  0.18),
    "round_wide":       ( 178, 180,  0.22,  0.12,  0.16),
    "square_balanced":  ( 148, 205,  0.52,  0.62,  0.22),
    "square_wide":      ( 175, 205,  0.58,  0.68,  0.22),
    "oblong_balanced":  ( 124, 235,  0.40,  0.26,  0.34),
    "oblong_elongated": ( 108, 272,  0.38,  0.24,  0.32),
    "heart_balanced":   ( 144, 210,  0.28,  0.26,  0.52),
    "diamond_balanced": ( 138, 216,  0.48,  0.24,  0.38),
    "triangle_balanced":( 152, 200,  0.62,  0.38,  0.18),
}

BACK_P = {
    #                      rx    ry   occ
    "oval_balanced":    (  84, 100,  1.06),
    "oval_elongated":   (  70, 125,  1.05),
    "oval_wide":        ( 110, 100,  1.06),
    "round_balanced":   (  96,  90,  1.12),
    "round_wide":       ( 120,  90,  1.12),
    "square_balanced":  (  88, 100,  1.04),
    "square_wide":      ( 114, 100,  1.04),
    "oblong_balanced":  (  70, 122,  1.05),
    "oblong_elongated": (  60, 148,  1.04),
    "heart_balanced":   (  98, 108,  1.07),
    "diamond_balanced": (  76, 112,  1.06),
    "triangle_balanced":(  68,  98,  1.04),
}


# ── VISTA FRONTAL ─────────────────────────────────────────────────────────────

def _side_descent(cx, cy, jaw_y, chin_start_y, rx, jaw_w, chin_hw, ang, sign):
    """
    Genera puntos del perfil lateral izquierdo (sign=-1) o derecho (sign=+1).
    Sin bezier en la transición: todo paramétrico → sin muescas.
    - ang < 0.5: descenso único cy→chin_start_y  (formas suaves)
    - ang ≥ 0.5: dos fases cy→jaw_y→chin_start_y (esquinas mandibulares)
    """
    pts = []
    if ang < 0.5:
        # Descenso único, exponent controla la curvatura
        exp = max(0.55, 1.0 - 0.5 * ang)
        N = 70
        for i in range(1, N + 1):
            t = i / N
            w = rx + (chin_hw - rx) * (t ** exp)
            y = cy + (chin_start_y - cy) * t
            pts.append((cx + sign * w, y))
    else:
        # Fase 1: cy → jaw_y  (rx → jaw_w)
        exp1 = max(0.3, 1.0 - 0.7 * ang)
        N1 = 30
        for i in range(1, N1 + 1):
            t = i / N1
            w = rx + (jaw_w - rx) * (t ** exp1)
            y = cy + (jaw_y - cy) * t
            pts.append((cx + sign * w, y))
        # Fase 2: jaw_y → chin_start_y  (jaw_w → chin_hw)
        exp2 = max(0.3, 1.0 - 0.5 * ang)
        N2 = 50
        for i in range(1, N2 + 1):
            t = i / N2
            w = jaw_w + (chin_hw - jaw_w) * (t ** exp2)
            y = jaw_y + (chin_start_y - jaw_y) * t
            pts.append((cx + sign * w, y))
    return pts


def front_outline(params):
    rx_n, ry_n, jaw_w_n, jaw_drop_n, chin_drop_n, ang = params
    cx = CX * SCALE
    cy = CY * SCALE
    rx = rx_n * SCALE
    ry = ry_n * SCALE
    jaw_w = jaw_w_n * SCALE
    jaw_y = cy + jaw_drop_n * SCALE
    chin_y = cy + chin_drop_n * SCALE

    # Mentón: semiancho y radio del arco inferior
    avg_w = (rx + jaw_w) / 2
    chin_hw = avg_w * (0.55 + (1 - ang) * 0.15)
    arc_h  = sc(8) + sc(10) * (1 - ang)   # arco mayor en caras redondas
    chin_start_y = chin_y - arc_h

    pts = []

    # 1. Cúpula superior: elipse de (cx+rx, cy) → cima → (cx-rx, cy)
    N_dome = 80
    for i in range(N_dome + 1):
        angle = math.pi * i / N_dome
        pts.append((cx + rx * math.cos(angle), cy - ry * math.sin(angle)))

    # 2. Descenso izquierdo: (cx-rx, cy) → (cx-chin_hw, chin_start_y)
    pts += _side_descent(cx, cy, jaw_y, chin_start_y, rx, jaw_w, chin_hw, ang, sign=-1)

    # 3. Arco del mentón: izquierdo → derecho
    chin_l = (cx - chin_hw, chin_start_y)
    chin_r = (cx + chin_hw, chin_start_y)
    chin_tip = chin_start_y + arc_h   # = chin_y (punta del mentón)
    pts += cbez(
        chin_l,
        (cx - chin_hw * 0.55, chin_tip),
        (cx + chin_hw * 0.55, chin_tip),
        chin_r,
    )

    # 4. Ascenso derecho: (cx+chin_hw, chin_start_y) → (cx+rx, cy)
    right = _side_descent(cx, cy, jaw_y, chin_start_y, rx, jaw_w, chin_hw, ang, sign=+1)
    pts += list(reversed(right))

    return pts, chin_y


def generate_front(arch):
    img, draw = canvas()
    head_pts, chin_y = front_outline(FRONT_P[arch])

    # Cuello (detrás de la cabeza)
    cx = CX * SCALE
    nw_top = sc(50); nw_bot = sc(64); nh = sc(70)
    ny = int(chin_y)
    neck = [
        (cx - nw_top // 2, ny), (cx + nw_top // 2, ny),
        (cx + nw_bot // 2, ny + nh), (cx - nw_bot // 2, ny + nh),
        (cx - nw_top // 2, ny),
    ]
    draw_filled(draw, neck, HEAD_FILL, HEAD_STROKE, STROKE_W)
    draw_filled(draw, head_pts, HEAD_FILL, HEAD_STROKE, STROKE_W)
    return out(img)


# ── VISTA LATERAL ─────────────────────────────────────────────────────────────

def generate_side(arch):
    fw, fh, jaw_fwd, brow, chin_fwd = SIDE_P[arch]
    img, draw = canvas()

    cx_n = 198; cy_n = CY
    top_y_n  = cy_n - fh / 2
    bot_y_n  = cy_n + fh / 2
    front_x_n = cx_n - fw * 0.42
    occ_x_n   = cx_n + fw * 0.58
    brow_y_n  = top_y_n + fh * 0.14
    jaw_y_n   = top_y_n + fh * 0.74
    nuca_y_n  = top_y_n + fh * 0.80
    jaw_x_n   = front_x_n + fw * jaw_fwd
    chin_x_n  = front_x_n + fw * chin_fwd

    def p(v): return sc(v)

    head_pts = []
    head_pts += cbez(
        (p(front_x_n), p(brow_y_n)),
        (p(front_x_n - fw * 0.05 * (1 - brow)), p(brow_y_n)),
        (p(front_x_n + fw * 0.04 * brow), p(top_y_n + fh * 0.02)),
        (p(cx_n), p(top_y_n)),
    )
    head_pts += cbez(
        (p(cx_n), p(top_y_n)),
        (p(occ_x_n + fw * 0.12), p(top_y_n + fh * 0.08)),
        (p(occ_x_n + fw * 0.14), p(top_y_n + fh * 0.58)),
        (p(occ_x_n), p(nuca_y_n)),
    )
    head_pts += cbez(
        (p(occ_x_n), p(nuca_y_n)),
        (p(occ_x_n - fw * 0.08), p(nuca_y_n + fh * 0.08)),
        (p(jaw_x_n + fw * 0.10), p(jaw_y_n - fh * 0.04)),
        (p(jaw_x_n), p(jaw_y_n)),
    )
    head_pts += cbez(
        (p(jaw_x_n), p(jaw_y_n)),
        (p(jaw_x_n - fw * 0.04), p(bot_y_n - fh * 0.06)),
        (p(chin_x_n + fw * 0.08), p(bot_y_n + fh * 0.01)),
        (p(chin_x_n), p(bot_y_n)),
    )
    head_pts += cbez(
        (p(chin_x_n), p(bot_y_n)),
        (p(front_x_n + fw * 0.10), p(bot_y_n + fh * 0.03)),
        (p(front_x_n - fw * 0.04), p(jaw_y_n + fh * 0.06)),
        (p(front_x_n), p(brow_y_n)),
    )

    # Oreja en perfil (natural en vista lateral)
    ear_cx = cx_n + fw * 0.28
    ear_cy = jaw_y_n - fh * 0.10
    ear_pts = []
    ear_pts += cbez(
        (p(ear_cx), p(ear_cy - 18)),
        (p(ear_cx + 13), p(ear_cy - 18)),
        (p(ear_cx + 13), p(ear_cy + 18)),
        (p(ear_cx), p(ear_cy + 18)),
    )
    ear_pts += cbez(
        (p(ear_cx), p(ear_cy + 18)),
        (p(ear_cx - 4), p(ear_cy + 18)),
        (p(ear_cx - 4), p(ear_cy - 18)),
        (p(ear_cx), p(ear_cy - 18)),
    )

    ny = p(bot_y_n); nw = sc(50); nh_neck = sc(70)
    nx0 = p(front_x_n + fw * 0.02)
    neck_pts = [
        (nx0, ny), (nx0 + nw, ny),
        (nx0 + nw + sc(8), ny + nh_neck), (nx0 - sc(2), ny + nh_neck),
        (nx0, ny),
    ]

    draw_filled(draw, neck_pts, HEAD_FILL, HEAD_STROKE, STROKE_W)
    draw_filled(draw, ear_pts,  HEAD_FILL, HEAD_STROKE, STROKE_W)
    draw_filled(draw, head_pts, HEAD_FILL, HEAD_STROKE, STROKE_W)
    return out(img)


# ── VISTA TRASERA ─────────────────────────────────────────────────────────────

def generate_back(arch):
    rx_n, ry_n, occ = BACK_P[arch]
    img, draw = canvas()

    cx = CX * SCALE; cy = CY * SCALE
    rx = sc(rx_n * occ); ry = sc(ry_n)
    k = 0.5523
    base_y = cy + int(ry * 0.58)
    half_neck = sc(40)

    pts = []
    pts += cbez(
        (cx, cy - ry),
        (cx + rx * k, cy - ry),
        (cx + rx, cy - ry * k),
        (cx + rx, cy),
    )
    pts += cbez(
        (cx + rx, cy),
        (cx + rx, cy + ry * k * 0.55),
        (cx + rx * 0.65, base_y - sc(4)),
        (cx + half_neck, base_y),
    )
    pts += cbez(
        (cx + half_neck, base_y),
        (cx + half_neck * 0.4, base_y + sc(5)),
        (cx - half_neck * 0.4, base_y + sc(5)),
        (cx - half_neck, base_y),
    )
    pts += cbez(
        (cx - half_neck, base_y),
        (cx - rx * 0.65, base_y - sc(4)),
        (cx - rx, cy + ry * k * 0.55),
        (cx - rx, cy),
    )
    pts += cbez(
        (cx - rx, cy),
        (cx - rx, cy - ry * k),
        (cx - rx * k, cy - ry),
        (cx, cy - ry),
    )

    nw_top = sc(44); nw_bot = sc(58); nh = sc(72)
    ny = base_y
    neck_pts = [
        (cx - nw_top // 2, ny), (cx + nw_top // 2, ny),
        (cx + nw_bot // 2, ny + nh), (cx - nw_bot // 2, ny + nh),
        (cx - nw_top // 2, ny),
    ]

    draw_filled(draw, neck_pts, HEAD_FILL, HEAD_STROKE, STROKE_W)
    draw_filled(draw, pts, HEAD_FILL, HEAD_STROKE, STROKE_W)
    return out(img)


# ── GENERAR TODOS ─────────────────────────────────────────────────────────────

ARCHETYPES = list(FRONT_P.keys())
GENERATORS = {"front": generate_front, "side": generate_side, "back": generate_back}

ok = 0; errs = []
for arch in ARCHETYPES:
    for view, fn in GENERATORS.items():
        fname = f"{arch}_base_{view}.png"
        try:
            fn(arch).save(os.path.join(OUT_DIR, fname), "PNG")
            ok += 1
            print(f"OK  {fname}")
        except Exception as e:
            errs.append(f"{fname}: {e}")
            import traceback; traceback.print_exc()

print(f"\n{'='*50}")
print(f"  {ok}/{len(ARCHETYPES)*3} generados  —  {len(errs)} errores")
if errs:
    for e in errs:
        print(f"  ERR {e}")
print(f"{'='*50}")
