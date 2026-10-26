# TipOut business card: 3.5 x 2 in trim, 0.125 in bleed (3.75 x 2.25 in canvas).
# Builds front.html / back.html, renders PDF (vector) + 600 dpi PNG with Playwright, then checks the QR decodes.
# Run: python3 card.py
import base64, io, os, re, subprocess, json
import segno
from PIL import Image

B = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(B)
PF = '/mnt/project-files'
URL = 'https://apps.apple.com/us/app/id6817116243'  # short form of the listing URL: same app, far less dense QR

G, DG, INK = '#34D77B', '#1F5F3F', '#0F2E1E'

def b64(path, mime):
    return f'data:{mime};base64,' + base64.b64encode(open(path, 'rb').read()).decode()

def pig_path():
    s = open(f'{PF}/content-2wk/_build/pig.svg').read()
    return re.search(r' d="([^"]+)"', s).group(1)

PIG = pig_path()
def pig_svg(fill, w='100%'):
    return f'<svg viewBox="0 0 126 93" width="{w}" xmlns="http://www.w3.org/2000/svg"><path fill="{fill}" fill-rule="evenodd" d="{PIG}"/></svg>'

def qr_svg():
    """Branded QR: rounded modules, rounded finder eyes, pig badge in the middle (error level H)."""
    q = segno.make(URL, error='h', boost_error=False)
    m = [list(r) for r in q.matrix]; n = len(m)
    eyes = [(0, 0), (0, n - 7), (n - 7, 0)]
    def in_eye(r, c): return any(er <= r < er + 7 and ec <= c < ec + 7 for er, ec in eyes)
    hole = 7.6  # modules cleared in the centre for the logo (well under H's 30% budget)
    lo, hi = (n - hole) / 2, (n + hole) / 2
    parts = []
    for r in range(n):
        for c in range(n):
            if not m[r][c] or in_eye(r, c): continue
            if lo - .5 < r < hi - .5 and lo - .5 < c < hi - .5: continue
            parts.append(f'<rect x="{c+.05:.2f}" y="{r+.05:.2f}" width=".9" height=".9" rx=".28"/>')
    for er, ec in eyes:
        parts.append(f'<path fill-rule="evenodd" d="M{ec+1.6},{er} h3.8 a1.6,1.6 0 0 1 1.6,1.6 v3.8 a1.6,1.6 0 0 1 -1.6,1.6 h-3.8 a1.6,1.6 0 0 1 -1.6,-1.6 v-3.8 a1.6,1.6 0 0 1 1.6,-1.6z '
                     f'M{ec+1.9},{er+1} h3.2 a.9,.9 0 0 1 .9,.9 v3.2 a.9,.9 0 0 1 -.9,.9 h-3.2 a.9,.9 0 0 1 -.9,-.9 v-3.2 a.9,.9 0 0 1 .9,-.9z"/>')
        parts.append(f'<rect x="{ec+2}" y="{er+2}" width="3" height="3" rx=".9"/>')
    cx = n / 2; r = hole / 2 - .35
    badge = (f'<circle cx="{cx}" cy="{cx}" r="{r}" fill="{G}"/>'
             f'<g transform="translate({cx - r*.62},{cx - r*.62*93/126}) scale({r*1.24/126})"><path fill="#fff" fill-rule="evenodd" d="{PIG}"/></g>')
    return f'<svg viewBox="0 0 {n} {n}" xmlns="http://www.w3.org/2000/svg"><g fill="{INK}">{"".join(parts)}</g>{badge}</svg>', n

def receipt_crop():
    im = Image.open(f'{PF}/receipt-scene/assets/receipt.png').convert('RGB')
    im = im.crop((0, 0, im.width, 1380))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=92)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode(), im.size

def screen_crop():
    im = Image.open(f'{PF}/receipt-scene/assets/screen-logged.png').convert('RGB')
    buf = io.BytesIO(); im.save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()

FONTS = ''.join(f"@font-face{{font-family:N;font-weight:{w}00;src:url('{b64(f'{PF}/launch/_build/N{w}.ttf', 'font/ttf')}')}}" for w in (7, 8, 9))

BASE_CSS = FONTS + f"""
@page{{size:3.75in 2.25in;margin:0}}
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;width:3.75in;height:2.25in;overflow:hidden}}
body{{font-family:N,sans-serif;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.card{{position:relative;width:3.75in;height:2.25in;overflow:hidden}}
"""

def front():
    qr, n = qr_svg()
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}
.card{{background:{G};color:#fff}}
.wm{{position:absolute;left:-.55in;bottom:-.5in;width:2.3in;opacity:.13;transform:rotate(-12deg)}}
.coin{{position:absolute;border-radius:50%;border:.02in solid rgba(255,255,255,.22)}}
.brand{{position:absolute;left:.36in;top:.36in;display:flex;align-items:center;gap:.07in}}
.brand .p{{width:.42in;display:block}}
.brand b{{font-weight:900;font-size:.33in;letter-spacing:-.006in;line-height:1}}
.tag{{position:absolute;left:.37in;top:.86in;font-weight:900;font-size:.165in;line-height:1.12;width:1.75in}}
.note{{position:absolute;left:.37in;top:1.33in;font-weight:800;font-size:.085in;line-height:1.35;color:{DG};width:1.6in}}
.url{{position:absolute;left:.37in;bottom:.29in;font-weight:900;font-size:.08in;letter-spacing:.006in;color:#fff;opacity:.95}}
.qrbox{{position:absolute;right:.32in;top:.32in;width:1.36in;height:1.61in;background:#fff;border-radius:.13in;padding:.1in .1in 0}}
.qrbox svg{{display:block;width:1.16in;height:1.16in}}
.cta{{text-align:center;font-weight:900;font-size:.083in;color:{INK};margin-top:.055in;line-height:1.15}}
.cta small{{display:block;font-weight:800;font-size:.062in;color:#5a6b62;margin-top:.012in}}
</style></head><body><div class="card">
<div class="brand"><span class="p">{pig_svg('#fff')}</span><b>TipOut</b></div>
<div class="tag">Every tip,<br>tracked.</div>
<div class="note">Thanks for taking such good care of us tonight. This one&rsquo;s for you.</div>
<div class="url">tipout.us &nbsp;·&nbsp; @tipout_us</div>
<div class="qrbox">{qr}<div class="cta">Scan to get TipOut<small>on the App Store</small></div></div>
</div></body></html>"""

def back():
    rc, (rw, rh) = receipt_crop()
    scr = screen_crop()
    # receipt shown 1.0in wide; "Non-cash tips" is line 22 (pad 60 + 52*line)
    k = 1.0 / rw
    hl_top, hl_h = (60 + 52 * 22 + 6) * k, 50 * k
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}
.card{{background:{DG};color:#fff}}
.glow{{position:absolute;right:-.4in;top:-.3in;width:2.6in;height:2.6in;border-radius:50%;background:radial-gradient(circle,rgba(52,215,123,.38),rgba(52,215,123,0) 68%)}}
.pill{{position:absolute;left:.36in;top:.34in;background:{G};color:{INK};font-weight:900;font-size:.07in;letter-spacing:.012in;padding:.035in .085in;border-radius:.1in;display:flex;align-items:center;gap:.04in}}
.pill svg{{width:.085in;height:.085in}}
h1{{position:absolute;left:.36in;top:.55in;margin:0;font-weight:900;font-size:.205in;line-height:1.02;letter-spacing:-.003in;width:1.6in}}
h1 em{{font-style:normal;color:{G}}}
.sub{{position:absolute;left:.37in;top:1.25in;font-weight:800;font-size:.082in;line-height:1.35;color:#BFEFD3;width:1.45in}}
.steps{{position:absolute;left:.37in;bottom:.3in;display:flex;gap:.05in;font-weight:900;font-size:.066in;color:#fff;align-items:center}}
.steps i{{font-style:normal;width:.13in;height:.13in;border-radius:50%;background:rgba(255,255,255,.14);display:inline-flex;align-items:center;justify-content:center;color:{G};margin-right:.025in}}
.steps span{{display:flex;align-items:center}}
.steps .ar{{color:rgba(255,255,255,.4)}}
.rc{{position:absolute;left:1.98in;top:.26in;width:1.0in;height:{rh*k:.3f}in;transform:rotate(-8deg);transform-origin:center;box-shadow:0 .04in .1in rgba(0,0,0,.35);border-radius:.015in;overflow:hidden}}
.rc img{{display:block;width:100%}}
.rc .hl{{position:absolute;left:.03in;right:.03in;top:{hl_top:.3f}in;height:{hl_h:.3f}in;border:.012in solid {G};background:rgba(52,215,123,.28);border-radius:.012in}}
.rc .scan{{position:absolute;left:0;right:0;top:{hl_top + hl_h/2:.3f}in;height:.012in;background:{G};box-shadow:0 0 .05in {G}}}
.frame{{position:absolute;left:1.9in;top:.2in;width:1.16in;height:1.72in;transform:rotate(-8deg)}}
.frame b{{position:absolute;width:.16in;height:.16in;border:0 solid {G}}}
.frame .a{{left:0;top:0;border-left-width:.025in;border-top-width:.025in;border-top-left-radius:.04in}}
.frame .b{{right:0;top:0;border-right-width:.025in;border-top-width:.025in;border-top-right-radius:.04in}}
.frame .c{{left:0;bottom:0;border-left-width:.025in;border-bottom-width:.025in;border-bottom-left-radius:.04in}}
.frame .d{{right:0;bottom:0;border-right-width:.025in;border-bottom-width:.025in;border-bottom-right-radius:.04in}}
.ph{{position:absolute;left:2.66in;top:.5in;width:.92in;height:2.0in;background:#0b0b0b;border-radius:.15in;padding:.035in;transform:rotate(7deg);box-shadow:-.03in .05in .14in rgba(0,0,0,.45)}}
.ph .s{{width:100%;height:100%;border-radius:.12in;overflow:hidden;background:{G}}}
.ph img{{display:block;width:100%}}
.ph .isl{{position:absolute;left:50%;top:.075in;width:.26in;height:.07in;margin-left:-.13in;background:#0b0b0b;border-radius:.05in}}
.badge{{position:absolute;left:2.12in;top:1.74in;background:#fff;color:{INK};border-radius:.08in;padding:.04in .07in;font-weight:900;font-size:.07in;display:flex;align-items:center;gap:.04in;box-shadow:0 .03in .08in rgba(0,0,0,.3);transform:rotate(-4deg)}}
.badge i{{width:.11in;height:.11in;border-radius:50%;background:{G};display:inline-flex;align-items:center;justify-content:center}}
.badge i svg{{width:.07in}}
</style></head><body><div class="card">
<div class="glow"></div>
<div class="pill"><svg viewBox="0 0 24 24" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8V6a2 2 0 0 1 2-2h2M16 4h2a2 2 0 0 1 2 2v2M20 16v2a2 2 0 0 1-2 2h-2M8 20H6a2 2 0 0 1-2-2v-2"/><circle cx="12" cy="12" r="3"/></svg>SNAP CHECKOUT</div>
<h1>Snap your<br>checkout.<br><em>Done.</em></h1>
<div class="sub">TipOut reads it and records your tips, hours and tip-out. Effortlessly.</div>
<div class="steps"><span><i>1</i>Snap</span><span class="ar">›</span><span><i>2</i>Logged</span><span class="ar">›</span><span><i>3</i>Paid</span></div>
<div class="rc"><img src="{rc}"><div class="hl"></div><div class="scan"></div></div>
<div class="frame"><b class="a"></b><b class="b"></b><b class="c"></b><b class="d"></b></div>
<div class="ph"><div class="s"><img src="{scr}"></div><div class="isl"></div></div>
<div class="badge"><i><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5 9-10"/></svg></i>Shift logged</div>
</div></body></html>"""

if __name__ == '__main__':
    for name, fn in [('front', front), ('back', back)]:
        open(f'{B}/{name}.html', 'w').write(fn())
    subprocess.run(['node', f'{B}/render.js', B, OUT], check=True)
