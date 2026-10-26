# US Letter home-print sheet: 10 cards (2x5, 3.5x2in, butted) per page, crop marks in the margins.
# Page 1 = fronts, page 2 = backs. The grid is centred, so it lines up for duplex printing (flip on long edge).
import os, subprocess
B = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(B)
X0, Y0, CW, CH = 0.75, 0.5, 3.5, 2.0
def page(img):
    cards = ''.join(f'<img src="{OUT}/{img}" style="left:{X0+c*CW}in;top:{Y0+r*CH}in">' for r in range(5) for c in range(2))
    marks = ''
    for x in [X0 + i*CW for i in range(3)]:
        marks += f'<i style="left:{x-.004}in;top:.1in;width:.008in;height:.3in"></i><i style="left:{x-.004}in;bottom:.1in;width:.008in;height:.3in"></i>'
    for y in [Y0 + i*CH for i in range(6)]:
        marks += f'<i style="top:{y-.004}in;left:.25in;height:.008in;width:.4in"></i><i style="top:{y-.004}in;right:.25in;height:.008in;width:.4in"></i>'
    return f'<div class="pg">{cards}{marks}</div>'
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@page{{size:8.5in 11in;margin:0}} html,body{{margin:0}}
.pg{{position:relative;width:8.5in;height:11in;overflow:hidden;page-break-after:always}}
.pg img{{position:absolute;width:{CW}in;height:{CH}in}}
.pg i{{position:absolute;background:#000}}
</style></head><body>{page('TipOut-card-front-trim.png')}{page('TipOut-card-back-trim.png')}</body></html>"""
open(f'{B}/sheet.html', 'w').write(html)
js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://{B}/sheet.html');await p.waitForTimeout(500);
await p.pdf({{path:'{OUT}/TipOut-cards-letter-sheet.pdf',width:'8.5in',height:'11in',printBackground:true}});await b.close()}})();"""
open(f'{B}/sheet.js', 'w').write(js)
subprocess.run(['node', f'{B}/sheet.js'], check=True)
