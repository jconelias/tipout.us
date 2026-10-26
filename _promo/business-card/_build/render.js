// node render.js <build dir> <out dir>: 600 dpi PNG (with bleed) + vector PDF per side, plus a 2-page PDF.
const { chromium } = require('playwright');
const [B, OUT] = process.argv.slice(2);
(async () => {
  const br = await chromium.launch();
  const pg = await br.newPage({ viewport: { width: 360, height: 216 }, deviceScaleFactor: 6.25 });
  for (const s of ['front', 'back']) {
    await pg.goto('file://' + B + '/' + s + '.html'); await pg.waitForTimeout(300);
    await pg.screenshot({ path: `${B}/${s}-bleed-600dpi.png` });
    await pg.pdf({ path: `${B}/${s}.pdf`, width: '3.75in', height: '2.25in', printBackground: true, pageRanges: '1' });
  }
  await br.close();
})();
