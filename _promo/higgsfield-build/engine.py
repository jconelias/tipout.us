# TipOut motion-graphics engine: everything is drawn with cairo, no screen recordings.
import cairo, math, re, random, subprocess, os
from PIL import Image

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))

def hexc(h, a=1.0):
    h = h.lstrip('#'); return (int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255, a)

G = hexc('32D67B'); DG = hexc('307351'); INK = hexc('0A100D'); INK2 = hexc('121B16')
CARD = hexc('EEF0F2'); WHITE = hexc('FFFFFF'); MINT = hexc('BEECD0'); BLUE = hexc('62AFD3')
PURP = hexc('9A22C4'); CORAL = hexc('FF6B5E'); YEL = hexc('F4FF6A'); TXT = hexc('1E1F1F'); GREY = hexc('8A938E')
NEON = hexc('3CFF95')

FONTS = {9: ('Nunito Black', 0), 8: ('Nunito ExtraBold', 0), 7: ('Nunito', 1), 'm': ('DejaVu Sans Mono', 0), 'mb': ('DejaVu Sans Mono', 1)}

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)
def eo(x): return 1 - (1 - x) ** 3
def eio(x): return 4*x*x*x if x < .5 else 1 - (-2*x + 2) ** 3 / 2
def back(x, s=1.9): x -= 1; return max(0.001, 1 + (s + 1) * x**3 + s * x**2)
def lerp(a, b, x): return a + (b - a) * x
def mix(c1, c2, x): return tuple(lerp(a, b, x) for a, b in zip(c1, c2))
def wa(c, a): return (c[0], c[1], c[2], c[3] * a)

# ---------- basics ----------
def src(c, col): c.set_source_rgba(*col)
def rrect(c, x, y, w, h, r):
    r = min(r, w/2, h/2)
    c.new_sub_path(); c.arc(x+w-r, y+r, r, -math.pi/2, 0); c.arc(x+w-r, y+h-r, r, 0, math.pi/2)
    c.arc(x+r, y+h-r, r, math.pi/2, math.pi); c.arc(x+r, y+r, r, math.pi, 3*math.pi/2); c.close_path()
def fill_rrect(c, x, y, w, h, r, col): rrect(c, x, y, w, h, r); src(c, col); c.fill()

def font(c, w, sz):
    name, bold = FONTS[w]
    c.select_font_face(name, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(sz)

def tw(c, s, w, sz, track=0):
    font(c, w, sz); return c.text_extents(s).x_advance + track * max(0, len(s) - 1)

def text(c, s, x, y, sz, w=9, col=WHITE, align='c', track=0):
    """y is the baseline. Returns width."""
    font(c, w, sz); width = c.text_extents(s).x_advance + track * max(0, len(s) - 1)
    x0 = x - width/2 if align == 'c' else (x - width if align == 'r' else x)
    src(c, col)
    if track:
        for ch in s:
            c.move_to(x0, y); c.show_text(ch); x0 += c.text_extents(ch).x_advance + track
    else:
        c.move_to(x0, y); c.show_text(s)
    return width

def money(v, cents=True, sign=False):
    s = f"{abs(v):,.2f}" if cents else f"{abs(v):,.0f}"
    return ('−' if v < 0 else ('+' if sign else '')) + '$' + s

# ---------- kinetic text ----------
def pop_lines(c, lines, cx, cy, sz, t, t0=0.0, stagger=0.07, w=9, col=WHITE, hl=YEL, hl_txt=INK, lh=1.06, dur=0.38):
    """Words pop in one by one with overshoot. Wrap a word in *stars* for a highlighter box.
    Wrap in _underscores_ for green text. cy is the visual center of the block."""
    font(c, w, sz)
    asc = sz * 0.72
    n = len(lines); total = sz * lh * (n - 1)
    k = 0
    for i, ln in enumerate(lines):
        words = ln.split(' ')
        widths = [tw(c, re.sub(r'[*_]', '', wd), w, sz) for wd in words]
        sp = tw(c, ' ', w, sz)
        x = cx - (sum(widths) + sp * (len(words) - 1)) / 2
        base = cy - total/2 + i * sz * lh + asc/2
        hlon = False
        for wd, wdt in zip(words, widths):
            starts = wd.startswith('*'); ends = wd.rstrip('.,?!:;”"').endswith('*') or wd.endswith('*')
            ish = hlon or starts
            if starts and not ends: hlon = True
            if ends and (hlon or starts): hlon = False
            p = prog(t, t0 + k*stagger, t0 + k*stagger + dur); k += 1
            if p <= 0: x += wdt + sp; continue
            s = back(p) if p < 1 else 1
            clean = re.sub(r'[*_]', '', wd)
            c.save(); c.translate(x + wdt/2, base - asc/2); c.scale(s, s); c.translate(-(x + wdt/2), -(base - asc/2))
            a = clamp(p * 3)
            if ish:
                pad = sz*0.12
                fill_rrect(c, x - pad, base - asc - pad*1.2, wdt + 2*pad + (sp if hlon else 0), asc + pad*2.6, sz*0.14, wa(hl, a))
                text(c, clean, x, base, sz, w, wa(hl_txt, a), 'l')
            elif wd.startswith('_'):
                text(c, clean, x, base, sz, w, wa(G, a), 'l')
            else:
                text(c, clean, x, base, sz, w, wa(col, a), 'l')
            c.restore()
            x += wdt + sp

def label(c, s, cx, y, sz=34, bg=G, fg=INK, alpha=1, track=3, w=9, h=None):
    """Pill label centred at cx, top y."""
    wdt = tw(c, s, w, sz, track); h = h or sz*1.9; padx = sz*0.85
    fill_rrect(c, cx - wdt/2 - padx, y, wdt + 2*padx, h, h/2, wa(bg, alpha))
    text(c, s, cx, y + h/2 + sz*0.36, sz, w, wa(fg, alpha), 'c', track)
    return y + h

# ---------- backgrounds ----------
_grain = []
def _make_grain():
    rnd = random.Random(7)
    for k in range(6):
        im = Image.effect_noise((W//2, H//2), 64).convert('L')
        a = im.point(lambda v: int(abs(v - 128) * 0.9))
        rgba = Image.merge('RGBA', (im, im, im, a))
        b = bytearray(rgba.tobytes('raw', 'BGRA'))
        s = cairo.ImageSurface.create_for_data(b, cairo.FORMAT_ARGB32, W//2, H//2)
        _grain.append((s, b))
def grain(c, t, amt=0.07):
    if not _grain: _make_grain()
    s, _ = _grain[int(t * 15) % len(_grain)]
    c.save(); c.scale(2, 2); p = cairo.SurfacePattern(s); p.set_extend(cairo.EXTEND_REPEAT); c.set_source(p); c.paint_with_alpha(amt); c.restore()

def bg(c, kind='dark', t=0.0, glow=True, w=W, h=H):
    if kind == 'dark':
        src(c, INK); c.paint()
        if glow:
            gx = w*0.5 + math.sin(t*0.9)*w*0.18; gy = h*0.42 + math.cos(t*0.7)*h*0.08
            r = cairo.RadialGradient(gx, gy, 0, gx, gy, w*0.95)
            r.add_color_stop_rgba(0, *wa(G, 0.26)); r.add_color_stop_rgba(0.55, *wa(DG, 0.10)); r.add_color_stop_rgba(1, 0, 0, 0, 0)
            c.set_source(r); c.paint()
    elif kind == 'green':
        src(c, G); c.paint()
        r = cairo.RadialGradient(w*0.5, h*0.35, 0, w*0.5, h*0.35, w*1.1)
        r.add_color_stop_rgba(0, 1, 1, 1, 0.22); r.add_color_stop_rgba(1, 0, 0, 0, 0.10)
        c.set_source(r); c.paint()
    elif kind == 'deep':
        src(c, DG); c.paint()
        r = cairo.RadialGradient(w*0.5, h*0.4, 0, w*0.5, h*0.4, w*1.0)
        r.add_color_stop_rgba(0, *wa(G, 0.35)); r.add_color_stop_rgba(1, 0, 0, 0, 0.25)
        c.set_source(r); c.paint()
    elif kind == 'spooky':
        src(c, hexc('0D0814')); c.paint()
        r = cairo.RadialGradient(w*0.5, h*0.45, 0, w*0.5, h*0.45, w*0.9)
        r.add_color_stop_rgba(0, *wa(PURP, 0.35 + 0.05*math.sin(t*9))); r.add_color_stop_rgba(0.6, *wa(G, 0.06)); r.add_color_stop_rgba(1, 0, 0, 0, 0)
        c.set_source(r); c.paint()

def dots_grid(c, t, col=WHITE, alpha=0.06, gap=54, w=W, h=H):
    c.new_path()
    src(c, wa(col, alpha)); off = (t*20) % gap
    y = -gap + off
    while y < h + gap:
        x = gap/2
        while x < w:
            c.arc(x, y, 2.2, 0, 2*math.pi); c.fill(); x += gap
        y += gap

# ---------- pig logo (vector, from the site's pig.svg) ----------
_pig = None
def _pig_path():
    global _pig
    if _pig is None:
        d = re.search(r' d="([^"]+)"', open(os.path.join(HERE, 'pig.svg')).read()).group(1)
        toks = re.findall(r'[MCLZmclz]|-?\d*\.?\d+', d)
        cmds = []; i = 0; cur = None
        while i < len(toks):
            if toks[i] in 'MCLZmclz': cur = toks[i]; i += 1
            n = {'M': 2, 'L': 2, 'C': 6}.get(cur.upper(), 0)
            if n == 0: cmds.append(('Z',)); continue
            cmds.append((cur.upper(), [float(v) for v in toks[i:i+n]])); i += n
            if cur == 'M': cur = 'L'
        _pig = cmds
    return _pig
def pig(c, cx, cy, width, col=WHITE, alpha=1.0):
    s = width / 126.0
    c.save(); c.translate(cx - 63*s, cy - 46.5*s); c.scale(s, s)
    c.new_path()
    for cmd in _pig_path():
        if cmd[0] == 'M': c.close_path(); c.move_to(*cmd[1])
        elif cmd[0] == 'L': c.line_to(*cmd[1])
        elif cmd[0] == 'C': c.curve_to(*cmd[1])
        else: c.close_path()
    c.close_path(); c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); src(c, wa(col, alpha)); c.fill()
    c.restore()

def app_icon(c, cx, cy, size, alpha=1.0):
    fill_rrect(c, cx - size/2, cy - size/2, size, size, size*0.23, wa(G, alpha))
    pig(c, cx, cy + size*0.02, size*0.66, WHITE, alpha)

# ---------- icons ----------
def check(c, cx, cy, r, col=G, fg=INK, p=1.0):
    c.new_path()
    src(c, col); c.arc(cx, cy, r, 0, 2*math.pi); c.fill()
    c.set_line_width(r*0.28); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND); src(c, fg)
    pts = [(cx - r*0.45, cy + r*0.02), (cx - r*0.1, cy + r*0.38), (cx + r*0.5, cy - r*0.35)]
    c.move_to(*pts[0])
    if p < 0.5: q = p/0.5; c.line_to(lerp(pts[0][0], pts[1][0], q), lerp(pts[0][1], pts[1][1], q))
    else:
        q = (p - .5)/.5; c.line_to(*pts[1]); c.line_to(lerp(pts[1][0], pts[2][0], q), lerp(pts[1][1], pts[2][1], q))
    c.stroke()

def cross(c, cx, cy, r, col=CORAL, lw=None):
    c.set_line_width(lw or r*0.3); c.set_line_cap(cairo.LINE_CAP_ROUND); src(c, col)
    c.move_to(cx - r, cy - r); c.line_to(cx + r, cy + r); c.move_to(cx + r, cy - r); c.line_to(cx - r, cy + r); c.stroke()

def glow(c, cx, cy, r, col=G, a=0.45):
    c.new_path()
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, r); g.add_color_stop_rgba(0, *wa(col, a)); g.add_color_stop_rgba(1, *wa(col, 0))
    c.set_source(g); c.arc(cx, cy, r, 0, 2*math.pi); c.fill()

# ---------- phone + app screens (402 x 874 coordinate space, like the Figma frames) ----------
SW, SH = 402, 874
def phone(c, cx, cy, scale, screen_fn, t=0.0, tilt=0.0, glow_a=0.35):
    pw, ph = SW + 26, SH + 26
    if glow_a: glow(c, cx, cy, ph*scale*0.75, G, glow_a)
    c.save(); c.translate(cx, cy); c.rotate(tilt); c.scale(scale, scale); c.translate(-pw/2, -ph/2)
    # shadow
    fill_rrect(c, 6, 18, pw, ph, 68, (0, 0, 0, 0.35))
    fill_rrect(c, 0, 0, pw, ph, 66, hexc('161A18'))
    rrect(c, 2, 2, pw-4, ph-4, 64); c.set_line_width(2.5); src(c, hexc('3A423E')); c.stroke()
    c.save(); c.translate(13, 13); rrect(c, 0, 0, SW, SH, 54); c.clip()
    screen_fn(c, t)
    # status bar + island
    text(c, '9:41', 44, 38, 17, 8, WHITE, 'l')
    fill_rrect(c, SW/2 - 62, 12, 124, 36, 18, hexc('050505'))
    for i in range(4): fill_rrect(c, SW - 92 + i*7, 30 - i*3, 4.5, 8 + i*3, 1.5, WHITE)
    fill_rrect(c, SW - 58, 24, 30, 15, 4.5, wa(WHITE, 0.9))
    c.restore(); c.restore()

def ring(c, cx, cy, r, lw, segs, track=(1, 1, 1, 0.2), start=-math.pi/2):
    """segs: list of (fraction, colour)."""
    c.new_path()
    c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_BUTT)
    src(c, track); c.arc(cx, cy, r, 0, 2*math.pi); c.stroke()
    a = start
    for f, col in segs:
        if f <= 0: continue
        src(c, col); c.arc(cx, cy, r, a, a + f*2*math.pi); c.stroke(); a += f*2*math.pi

def row_icon(c, kind, x, y, col):
    c.new_path()
    c.set_line_width(2.2); src(c, col)
    if kind == 'clock':
        c.arc(x+9, y, 8, 0, 2*math.pi); c.stroke(); c.move_to(x+9, y-4); c.line_to(x+9, y); c.line_to(x+12, y+2); c.stroke()
    elif kind == 'card':
        rrect(c, x, y-7, 18, 13, 2.5); c.stroke(); c.move_to(x, y-2.5); c.line_to(x+18, y-2.5); c.stroke()
    elif kind == 'cash':
        rrect(c, x, y-6, 18, 12, 3); c.stroke(); c.arc(x+13, y, 1.8, 0, 2*math.pi); c.fill()
    elif kind == 'bars':
        for i, hh in enumerate([7, 11, 15]): fill_rrect(c, x+2+i*6, y+6-hh, 3.5, hh, 1, col)
    elif kind == 'out':
        c.move_to(x+2, y); c.line_to(x+16, y); c.move_to(x+11, y-5); c.line_to(x+16, y); c.line_to(x+11, y+5); c.stroke()
    elif kind == 'home':
        c.move_to(x+1, y+1); c.line_to(x+9, y-7); c.line_to(x+17, y+1); c.stroke(); rrect(c, x+4, y, 10, 7, 1); c.stroke()

def paycheck_card(c, x, y, w, rows, title='This Paycheck', sub='Oct 12 – Oct 25', p=1.0):
    h = 74 + 34*len(rows)
    fill_rrect(c, x, y, w, h, 22, (0, 0, 0, 0.12))
    fill_rrect(c, x, y-3, w, h, 22, CARD)
    text(c, title, x+20, y+44, 26, 9, TXT, 'l')
    text(c, sub, x+w-20, y+40, 13, 7, GREY, 'r')
    for i, (ic, lab, val, col) in enumerate(rows):
        yy = y + 82 + 34*i
        a = clamp(p*len(rows) - i)
        row_icon(c, ic, x+20, yy-6, wa(col, a))
        text(c, lab, x+48, yy, 17, 7, wa(col, a), 'l')
        text(c, val, x+w-20, yy, 17, 8, wa(col if col != TXT else TXT, a), 'r')
    return y + h

def home_screen(amount=1981.75, ring_p=1.0, hourly='$35.23/hr', day='Day 10 of 14', name='Maya', card_p=1.0, rows=None, fab=True):
    rows = rows or [('clock', 'Hours Worked', '56.3 hrs', PURP), ('card', 'Credit Card Tips', '$1,673.15', DG),
                    ('cash', 'Cash Tips', '$308.00', BLUE), ('out', 'Tip-out', '−$308.82', CORAL), ('home', 'Take-home', '$1,981.75', TXT)]
    def fn(c, t):
        bg(c, 'green', t, w=SW, h=SH)
        text(c, 'Good Evening,', 24, 110, 27, 9, WHITE, 'l'); text(c, name, 24, 144, 27, 9, WHITE, 'l')
        for i in range(3): fill_rrect(c, SW-56, 96 + i*9, 26, 3.2, 1.6, WHITE)
        rp = ring_p
        ring(c, SW/2, 330, 138, 30, [(0.73*rp, DG), (0.13*rp, BLUE), (0.14*rp, MINT)])
        text(c, money(amount), SW/2, 340, 50 if amount < 10000 else 44, 9, WHITE)
        text(c, hourly, SW/2, 378, 17, 8, wa(WHITE, 0.9))
        text(c, day.upper(), SW/2, 402, 11, 8, wa(WHITE, 0.75), track=1.5)
        if card_p > 0:
            yy = 540 + (1 - eo(card_p)) * 300
            paycheck_card(c, 16, yy, SW-32, rows, p=card_p)
        if fab:
            src(c, DG); c.arc(SW/2, SH-62, 31, 0, 2*math.pi); c.fill()
            c.set_line_width(3.5); src(c, WHITE); c.move_to(SW/2-11, SH-62); c.line_to(SW/2+11, SH-62); c.move_to(SW/2, SH-73); c.line_to(SW/2, SH-51); c.stroke()
    return fn

def shift_screen(card=389.00, cash=15.00, hours=7.8, tipout=47.31, wage=7.19, reveal=1.0, highlight=0.0, day='Saturday', date='10/24'):
    real = (card + cash - tipout + hours*wage) / hours
    def fn(c, t):
        bg(c, 'green', t, w=SW, h=SH)
        text(c, day, 24, 112, 30, 9, WHITE, 'l'); text(c, date, SW-24, 112, 24, 7, WHITE, 'r')
        y = 150
        items = [('clock', 'Hours Worked', f'{hours} hrs', PURP), ('card', 'Credit Card Tips', money(card), DG),
                 ('cash', 'Cash Tips', money(cash), BLUE), ('out', 'Tip-out', money(-tipout), CORAL), ('home', 'Wages', money(hours*wage), TXT)]
        fill_rrect(c, 16, y, SW-32, 260, 22, CARD)
        for i, (ic, lab, val, col) in enumerate(items):
            a = clamp(reveal*6 - i)
            yy = y + 46 + 46*i
            row_icon(c, ic, 36, yy-6, wa(col, a)); text(c, lab, 64, yy, 18, 7, wa(col, a), 'l'); text(c, val, SW-36, yy, 18, 8, wa(col, a), 'r')
        a = clamp(reveal*6 - 5)
        hy = 440
        fill_rrect(c, 16, hy, SW-32, 150, 22, wa(DG, a))
        if highlight > 0: rrect(c, 16, hy, SW-32, 150, 22); c.set_line_width(4); src(c, wa(YEL, highlight*a)); c.stroke()
        text(c, 'REAL HOURLY', SW/2, hy+44, 14, 9, wa(MINT, a), track=2)
        text(c, f'${real:.2f}/hr', SW/2, hy+112, 54, 9, wa(WHITE, a))
        text(c, 'tip-out out · wages in', SW/2, hy+138, 14, 7, wa(MINT, a*0.9))
        ty = 620; fill_rrect(c, 16, ty, SW-32, 120, 22, wa(CARD, a))
        text(c, 'Shift take-home', 36, ty+44, 17, 8, wa(TXT, a), 'l'); text(c, money(real*hours), SW-36, ty+44, 22, 9, wa(DG, a), 'r')
        for i, v in enumerate([0.45, 0.6, 0.38, 0.7, 0.82, 0.66, 1.0]):
            fill_rrect(c, 36 + i*48, ty+104 - 40*v*a, 30, 40*v*a, 6, wa(G if i == 6 else hexc('B9C4BE'), a))
    return fn

# ---------- receipt ----------
RECEIPT = [('SERVER CHECKOUT', None), ('Sat 10/24  4:02 PM-11:50 PM', None), ('', None),
           ('Net Sales', '1,846.20'), ('Cash Sales', '211.40'), ('Credit Card Sales', '1,634.80'), ('', None),
           ('Credit Card Tips', '389.00'), ('Tip-out (bar/bus)', '47.31'), ('Cash Due', '42.85'), ('', None),
           ('Guests', '61'), ('Checks', '23'), ('', None), ('*** THANK YOU ***', None)]
def receipt(c, cx, top, w, t=0.0, lines=RECEIPT, highlights=(), hp=0.0, scan=None):
    lh = 46; h = 60 + lh*len(lines)
    x = cx - w/2
    c.save()
    # zig-zag bottom
    c.move_to(x, top); c.line_to(x+w, top); c.line_to(x+w, top+h)
    n = 18
    for i in range(n):
        c.line_to(x + w - (i+0.5)*w/n, top + h + 14); c.line_to(x + w - (i+1)*w/n, top + h)
    c.close_path(); src(c, hexc('FBFAF5')); c.fill_preserve(); c.clip()
    for i, (l, v) in enumerate(lines):
        y = top + 66 + lh*i
        if v is None: text(c, l, cx, y, 26, 'mb', hexc('2A2A2A'))
        else: text(c, l, x+34, y, 26, 'm', hexc('2A2A2A'), 'l'); text(c, v, x+w-34, y, 26, 'mb', hexc('2A2A2A'), 'r')
    for i, col in highlights:
        y = top + 66 + lh*i
        a = hp
        rrect(c, x+18, y-34, w-36, 46, 8); src(c, wa(col, 0.22*a)); c.fill_preserve(); c.set_line_width(4); src(c, wa(col, a)); c.stroke()
    if scan is not None:
        sy = top + scan*h
        g = cairo.LinearGradient(0, sy-120, 0, sy)
        g.add_color_stop_rgba(0, *wa(G, 0)); g.add_color_stop_rgba(1, *wa(G, 0.35))
        c.rectangle(x, sy-120, w, 120); c.set_source(g); c.fill()
        c.rectangle(x, sy-3, w, 6); src(c, NEON); c.fill()
    c.restore()
    return top + h

def corners(c, x, y, w, h, l=60, col=WHITE, lw=7, a=1):
    c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND); src(c, wa(col, a))
    for (px, py, dx, dy) in [(x, y, 1, 1), (x+w, y, -1, 1), (x, y+h, 1, -1), (x+w, y+h, -1, -1)]:
        c.move_to(px, py + dy*l); c.line_to(px, py); c.line_to(px + dx*l, py); c.stroke()

# ---------- end cards ----------
def end_countdown(days_text, big, sub='until TipOut hits the App Store'):
    """days_text e.g. '3 DAYS'; big e.g. '3' or None for TOMORROW."""
    def fn(c, t, d):
        bg(c, 'deep', t)
        dots_grid(c, t, WHITE, 0.05)
        p = prog(t, 0, 0.45)
        pig(c, W/2, 430, 260*back(prog(t, 0.05, 0.5)) + 0.01, WHITE)
        if big:
            s = back(p)
            c.save(); c.translate(W/2, 860); c.scale(s, s); text(c, big, 0, 160, 440, 9, G); c.restore()
            text(c, 'DAYS' if big != '1' else 'DAY', W/2, 1130, 120, 9, wa(WHITE, clamp(p*2)))
        else:
            s = back(p)
            c.save(); c.translate(W/2, 900); c.scale(s, s); text(c, 'TOMORROW', 0, 50, 128, 9, G); c.restore()
        a = prog(t, 0.35, 0.7)
        text(c, sub, W/2, 1240, 46, 8, wa(MINT, a))
        label(c, 'MON · OCT 26', W/2, 1300, 40, WHITE, INK, a)
        text(c, '@tipout_us', W/2, 1480, 38, 8, wa(WHITE, a*0.8))
    return fn

def end_now(line1='Available on the', line2='App Store now'):
    def fn(c, t, d):
        bg(c, 'deep', t)
        dots_grid(c, t, WHITE, 0.05)
        s = back(prog(t, 0, 0.45))
        c.save(); c.translate(W/2, 560); c.scale(max(s, 0.01), max(s, 0.01)); app_icon(c, 0, 0, 260); c.restore()
        a = prog(t, 0.15, 0.5)
        text(c, 'TipOut', W/2, 840, 120, 9, wa(WHITE, a))
        p2 = prog(t, 0.3, 0.7)
        c.save(); c.translate(W/2, 1010); c.scale(lerp(0.7, 1, back(p2)), lerp(0.7, 1, back(p2)))
        fill_rrect(c, -390, -95, 780, 190, 95, wa(WHITE, clamp(p2*2)))
        text(c, line1, 0, -12, 46, 8, wa(INK, clamp(p2*2)))
        text(c, line2, 0, 50, 62, 9, wa(INK, clamp(p2*2)))
        c.restore()
        a = prog(t, 0.55, 0.9)
        text(c, 'Search “TipOut” · iPhone', W/2, 1210, 44, 8, wa(MINT, a))
        text(c, '@tipout_us · tipout.us', W/2, 1290, 36, 8, wa(WHITE, a*0.75))
    return fn

# ---------- render ----------
class Seg:
    def __init__(self, dur, fn, bgk=None, punch=True):
        self.dur, self.fn, self.punch = dur, fn, punch

def render(segs, out, w=W, h=H, fps=FPS, grain_amt=0, preview=None):
    total = sum(s.dur for s in segs); n = int(round(total * fps))
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    proc = None
    if out:
        proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-',
                                 '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    frames = range(n) if preview is None else [int(p*fps) for p in preview]
    for f in frames:
        t = f / fps; acc = 0
        for i, s in enumerate(segs):
            if t < acc + s.dur or i == len(segs) - 1: break
            acc += s.dur
        lt = t - acc
        c = cairo.Context(surf)
        c.save()
        if s.punch and i > 0 and lt < 0.22:
            k = 1 + 0.07 * (1 - eo(lt/0.22)); c.translate(w/2, h/2); c.scale(k, k); c.translate(-w/2, -h/2)
        s.fn(c, lt, s.dur)
        c.restore()
        if s.punch and i > 0 and lt < 0.07:
            src(c, (1, 1, 1, 0.5 * (1 - lt/0.07))); c.paint()
        if grain_amt: grain(c, t, grain_amt)
        surf.flush()
        if proc: proc.stdin.write(bytes(surf.get_data()))
        else: surf.write_to_png(preview_path(out, f, t) if False else f'{os.environ.get("PREV","/tmp")}/f_{f:04d}.png')
    if proc:
        proc.stdin.close(); proc.wait()
        if proc.returncode: raise SystemExit('ffmpeg failed')
    return total
def preview_path(*a): return None
