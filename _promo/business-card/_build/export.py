# Copies renders from _build into the deliverables: per-side PDFs, 2-page print PDF, bleed + trim PNGs, preview.
import shutil, os
from PIL import Image, ImageDraw, ImageFilter
from pypdf import PdfWriter
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
w = PdfWriter()
for s in ['front', 'back']: w.append(f'_build/{s}.pdf')
w.write('TipOut-card-print-2sided.pdf')
B = 75  # 0.125in at 600dpi
tr = {}
for s in ['front', 'back']:
    shutil.copy(f'_build/{s}.pdf', f'TipOut-card-{s}.pdf')
    im = Image.open(f'_build/{s}-bleed-600dpi.png').convert('RGB'); im.save(f'TipOut-card-{s}-bleed-600dpi.png')
    t = im.crop((B, B, im.width - B, im.height - B)); t.save(f'TipOut-card-{s}-trim.png'); tr[s] = t
W, H = 1600, 1900; bg = Image.new('RGB', (W, H), '#EDEAE4')
for i, s in enumerate(['front', 'back']):
    c = tr[s].resize((1260, 720), Image.LANCZOS)
    m = Image.new('L', c.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, *c.size), 28, fill=255)
    x, y = 170, 160 + i * 860
    sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).rounded_rectangle((x + 10, y + 24, x + 1270, y + 744), 30, fill=110); sh = sh.filter(ImageFilter.GaussianBlur(26))
    bg.paste(Image.new('RGB', (W, H), '#8a8378'), (0, 0), sh); bg.paste(c, (x, y), m)
bg.save('TipOut-card-preview.jpg', quality=90)
