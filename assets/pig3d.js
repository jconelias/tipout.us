/* The hero piggy bank: a 3D cloud of tips (digits and $ signs) you can spin.
   A nod to the hand of ones and zeros on conelias.com. */
(function () {
  var canvas = document.querySelector('[data-pig3d]');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var DPR = Math.min(2, window.devicePixelRatio || 1);
  var W = 0, H = 0, pts = [], sprites = {}, running = false, visible = true;
  var yaw = -0.4, spin = 0, pitch = 0.12, vYaw = 0, vPitch = 0, dragging = false, lastX = 0, lastY = 0, idle = 0;
  var mouse = { x: -9999, y: -9999 }, t0 = performance.now(), intro = 0;
  var GLYPHS = '0123456789$';

  function sprite(ch, color, weight) {
    var key = ch + color + weight;
    if (sprites[key]) return sprites[key];
    var s = 64, c = document.createElement('canvas');
    c.width = c.height = s;
    var g = c.getContext('2d');
    g.font = weight + ' 44px "JetBrains Mono", ui-monospace, Menlo, monospace';
    g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillStyle = color;
    g.fillText(ch, s / 2, s / 2 + 2);
    return (sprites[key] = c);
  }

  function build(img) {
    // Rasterize the pig, then estimate thickness from distance to the edge.
    var gw = 150, gh = Math.round(gw * img.height / img.width);
    var c = document.createElement('canvas'); c.width = gw; c.height = gh;
    var g = c.getContext('2d'); g.drawImage(img, 0, 0, gw, gh);
    var data = g.getImageData(0, 0, gw, gh).data;
    var inside = new Uint8Array(gw * gh);
    for (var i = 0; i < gw * gh; i++) inside[i] = data[i * 4 + 3] > 120 ? 1 : 0;
    // Holes (the $ cut into the pig): empty pixels not reachable from the border.
    var reach = new Uint8Array(gw * gh), stack = [];
    for (var x = 0; x < gw; x++) { stack.push(x, (gh - 1) * gw + x); }
    for (var y = 0; y < gh; y++) { stack.push(y * gw, y * gw + gw - 1); }
    while (stack.length) {
      var p = stack.pop();
      if (p < 0 || p >= gw * gh || reach[p] || inside[p]) continue;
      reach[p] = 1;
      var px = p % gw;
      stack.push(p - gw, p + gw);
      if (px > 0) stack.push(p - 1);
      if (px < gw - 1) stack.push(p + 1);
    }
    var body = new Uint8Array(gw * gh);
    for (i = 0; i < gw * gh; i++) body[i] = inside[i] || !reach[i] ? 1 : 0;
    // Chamfer distance transform on the filled body.
    var BIG = 1e6, d = new Float32Array(gw * gh);
    for (i = 0; i < gw * gh; i++) d[i] = body[i] ? BIG : 0;
    for (y = 0; y < gh; y++) for (x = 0; x < gw; x++) {
      i = y * gw + x; if (!d[i]) continue;
      if (x > 0) d[i] = Math.min(d[i], d[i - 1] + 1);
      if (y > 0) d[i] = Math.min(d[i], d[i - gw] + 1);
      if (x > 0 && y > 0) d[i] = Math.min(d[i], d[i - gw - 1] + 1.4142);
      if (x < gw - 1 && y > 0) d[i] = Math.min(d[i], d[i - gw + 1] + 1.4142);
    }
    for (y = gh - 1; y >= 0; y--) for (x = gw - 1; x >= 0; x--) {
      i = y * gw + x; if (!d[i]) continue;
      if (x < gw - 1) d[i] = Math.min(d[i], d[i + 1] + 1);
      if (y < gh - 1) d[i] = Math.min(d[i], d[i + gw] + 1);
      if (x < gw - 1 && y < gh - 1) d[i] = Math.min(d[i], d[i + gw + 1] + 1.4142);
      if (x > 0 && y < gh - 1) d[i] = Math.min(d[i], d[i + gw - 1] + 1.4142);
    }
    var dmax = 0; for (i = 0; i < gw * gh; i++) dmax = Math.max(dmax, d[i]);

    pts = [];
    var step = 3.7, cx = gw / 2, cy = gh / 2, scale = 1 / gw, depth = 0.17;
    for (y = 1; y < gh; y += step) for (x = 1; x < gw; x += step) {
      var jx = x + (Math.random() - .5) * step * .8, jy = y + (Math.random() - .5) * step * .8;
      var ix = Math.round(jx), iy = Math.round(jy);
      if (ix < 0 || iy < 0 || ix >= gw || iy >= gh) continue;
      i = iy * gw + ix;
      if (!body[i]) continue;
      var hole = !inside[i];
      var k = Math.sqrt(d[i] / dmax);        // 0 at the edge, 1 at the thickest point
      var z = k * depth;
      var nx = (jx - cx) * scale, ny = (jy - cy) * scale;
      if (hole) {
        // The $ is stamped on the front of the pig.
        pts.push(mk(nx, ny, z + 0.02, '$', true));
      } else {
        pts.push(mk(nx, ny, z, null, false));
        pts.push(mk(nx, ny, -z, null, false));
        if (k < .35) pts.push(mk(nx, ny, (Math.random() - .5) * z * 2, null, false));
      }
    }
    for (var n = 0; n < pts.length; n++) {
      var q = pts[n];
      q.sx = (Math.random() - .5) * 3; q.sy = (Math.random() - .5) * 3; q.sz = (Math.random() - .5) * 3;
    }
    start();
  }

  function mk(x, y, z, ch, isDollar) {
    var r = Math.random();
    return {
      x: x, y: y, z: z, ox: 0, oy: 0,
      ch: ch || (r < .2 ? '$' : GLYPHS[Math.floor(Math.random() * 10)]),
      dollar: isDollar, swap: Math.random() * 6, size: isDollar ? 1.1 : .75 + Math.random() * .5,
      tone: Math.random() < .12 ? 'mint' : 'white'
    };
  }

  function resize() {
    var r = canvas.getBoundingClientRect();
    W = r.width; H = r.height;
    canvas.width = Math.round(W * DPR); canvas.height = Math.round(H * DPR);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    if (!running) frame(performance.now());
  }

  var COLORS = { white: '#FFFFFF', mint: '#D4F5E2' };
  function frame(now) {
    var t = (now - t0) / 1000;
    intro = reduce ? 1 : Math.min(1, intro + 0.012);
    var ease = 1 - Math.pow(1 - intro, 3);
    if (!dragging) {
      // Sway around the side view so it always reads as a pig; a drag spins it, then it settles back.
      vYaw *= .95; vPitch *= .92;
      spin += vYaw;
      spin += (Math.round(spin / (2 * Math.PI)) * 2 * Math.PI - spin) * .015;
      var sway = reduce ? -.35 : Math.sin(t * .45) * .55 - .15;
      yaw += (sway + spin - yaw) * .06;
      pitch += vPitch + (0.12 + (reduce ? 0 : Math.sin(t * .3) * .08) - pitch) * .03;
    }
    ctx.clearRect(0, 0, W, H);
    var wide = W > 700, S = wide ? Math.min(W * .8, H * 1.15) : Math.min(W * .78, H * .9), cx = W * (wide ? .4 : .42), cy = H * (wide ? .42 : .36);
    var cyw = Math.cos(yaw), syw = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
    var bob = reduce ? 0 : Math.sin(t * 1.2) * .012;
    var list = [];
    for (var i = 0; i < pts.length; i++) {
      var p = pts[i];
      var x = p.x * ease + p.sx * (1 - ease), y = p.y * ease + p.sy * (1 - ease) + bob, z = p.z * ease + p.sz * (1 - ease);
      var x1 = x * cyw + z * syw, z1 = -x * syw + z * cyw;
      var y1 = y * cp - z1 * sp, z2 = y * sp + z1 * cp;
      var f = 2.6 / (2.6 + z2 * 1.2);
      var X = cx + x1 * S * f, Y = cy + y1 * S * f;
      // Cursor nudges tips aside.
      var dx = X - mouse.x, dy = Y - mouse.y, dd = dx * dx + dy * dy, R = 90 * 90;
      if (dd < R) { var push = (1 - dd / R) * 22; var l = Math.sqrt(dd) || 1; p.ox += (dx / l * push - p.ox) * .2; p.oy += (dy / l * push - p.oy) * .2; }
      else { p.ox *= .9; p.oy *= .9; }
      if (!reduce && (p.swap -= 0.016) < 0 && !p.dollar) { p.swap = 2 + Math.random() * 6; p.ch = Math.random() < .2 ? '$' : GLYPHS[Math.floor(Math.random() * 10)]; }
      list.push({ X: X + p.ox, Y: Y + p.oy, z: z2, f: f, p: p });
    }
    list.sort(function (a, b) { return b.z - a.z; });
    var base = S * .027;
    for (i = 0; i < list.length; i++) {
      var q = list[i], sz = base * q.p.size * q.f;
      var front = q.p.dollar ? 1 : Math.max(.18, Math.min(1, .62 - q.z * 2.4));
      ctx.globalAlpha = front * ease + (1 - ease) * .5;
      ctx.drawImage(sprite(q.p.ch, COLORS[q.p.tone], q.p.dollar ? 800 : 600), q.X - sz, q.Y - sz, sz * 2, sz * 2);
    }
    ctx.globalAlpha = 1;
    if (running) requestAnimationFrame(frame);
  }

  function start() {
    resize();
    if (reduce) { intro = 1; frame(performance.now()); return; }
    if (!running && visible) { running = true; requestAnimationFrame(frame); }
  }

  canvas.addEventListener('pointerdown', function (e) { dragging = true; lastX = e.clientX; lastY = e.clientY; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener('pointermove', function (e) {
    var r = canvas.getBoundingClientRect();
    mouse.x = e.clientX - r.left; mouse.y = e.clientY - r.top;
    if (!dragging) return;
    var dx = e.clientX - lastX, dy = e.clientY - lastY; lastX = e.clientX; lastY = e.clientY;
    vYaw = dx * .006; vPitch = dy * .004;
    yaw += vYaw; spin += vYaw; pitch = Math.max(-.6, Math.min(.8, pitch + vPitch));
    if (reduce) frame(performance.now());
  });
  var end = function () { dragging = false; };
  canvas.addEventListener('pointerup', end);
  canvas.addEventListener('pointercancel', end);
  canvas.addEventListener('pointerleave', function () { mouse.x = mouse.y = -9999; });

  new IntersectionObserver(function (es) {
    visible = es[0].isIntersecting;
    if (visible && !running && pts.length && !reduce) { running = true; requestAnimationFrame(frame); }
    if (!visible) running = false;
  }).observe(canvas);
  window.addEventListener('resize', resize);

  var img = new Image();
  img.onload = function () {
    var go = function () { build(img); };
    if (document.fonts && document.fonts.load) document.fonts.load('600 44px "JetBrains Mono"').then(go, go); else go();
  };
  img.src = '/pig.svg';
})();
