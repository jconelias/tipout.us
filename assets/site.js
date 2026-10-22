/* TipOut site. Edit CONFIG to swap links. */
var CONFIG = {
  appStore: 'https://apps.apple.com/app/tipout-track-your-tips/id6817116243',
  // Until this moment the App Store buttons say "Coming Monday" and scroll to the countdown.
  // Set launched: true to switch every button to the App Store link right away.
  releaseAt: '2026-10-26T09:00:00-04:00',
  launched: false,
  socials: {
    instagram: 'https://instagram.com/tipout_us',
    tiktok: '',   // paste the TikTok profile URL here when it exists
    youtube: ''   // paste the YouTube channel URL here when it exists
  }
};

(function () {
  var doc = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var isLive = function () { return CONFIG.launched || Date.now() >= Date.parse(CONFIG.releaseAt); };
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---- Socials: one config, quiet everywhere ---- */
  var NAMES = { instagram: 'Instagram', tiktok: 'TikTok', youtube: 'YouTube' };
  $$('[data-social]').forEach(function (a) {
    var key = a.getAttribute('data-social');
    var url = CONFIG.socials[key];
    if (url) {
      a.href = url; a.target = '_blank'; a.rel = 'noopener';
      a.classList.remove('soon');
      if (a.hasAttribute('data-tip')) a.setAttribute('data-tip', key === 'instagram' ? '@tipout_us' : NAMES[key]);
    } else {
      a.removeAttribute('href');
      a.classList.add('soon');
      a.setAttribute('aria-disabled', 'true');
      a.setAttribute('data-tip', NAMES[key] + ' · soon');
      a.setAttribute('aria-label', NAMES[key] + ', coming soon');
    }
  });

  /* ---- App Store buttons ---- */
  function applyCTA() {
    var live = isLive();
    doc.classList.toggle('is-live', live);
    $$('[data-appstore]').forEach(function (a) {
      var t = a.querySelector('[data-cta-text]');
      var s = a.querySelector('[data-cta-sub]');
      if (live) {
        a.href = CONFIG.appStore; a.target = '_blank'; a.rel = 'noopener';
        if (t) t.textContent = t.getAttribute('data-live') || 'App Store';
        if (s) s.textContent = s.getAttribute('data-live') || 'Download on the';
      } else {
        a.href = a.getAttribute('data-soon-href') || '/#launch';
        a.removeAttribute('target');
        if (t) t.textContent = t.getAttribute('data-soon') || 'Monday, Oct 26';
        if (s) s.textContent = s.getAttribute('data-soon') || 'Coming to the App Store';
      }
    });
    $$('[data-live-only]').forEach(function (el) { el.hidden = !live; });
    $$('[data-soon-only]').forEach(function (el) { el.hidden = live; });
  }
  applyCTA();

  /* ---- Nav: hide on scroll down, mobile menu ---- */
  var nav = $('.nav'), lastY = 0;
  var rail = $('.rail'), status = $('.status');
  function onScroll() {
    var y = window.scrollY;
    if (nav && !doc.classList.contains('nav-open')) nav.classList.toggle('hide', y > 240 && y > lastY + 4);
    if (y < lastY - 4 && nav) nav.classList.remove('hide');
    lastY = y;
    var nearEnd = y + window.innerHeight > document.documentElement.scrollHeight - 420;
    if (rail) rail.classList.toggle('show', y > 300 && !nearEnd);
    if (status) status.classList.toggle('show', y > 300 && !nearEnd);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  var toggle = $('.nav-toggle');
  if (toggle) toggle.addEventListener('click', function () {
    var open = doc.classList.toggle('nav-open');
    toggle.setAttribute('aria-expanded', open);
    document.body.style.overflow = open ? 'hidden' : '';
  });
  $$('.menu a').forEach(function (a) { a.addEventListener('click', function () { doc.classList.remove('nav-open'); document.body.style.overflow = ''; }); });

  /* ---- Split headings into words ---- */
  $$('.split-words').forEach(function (el) {
    var i = 0;
    (function walk(node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(' ')); return; }
            var w = document.createElement('span'); w.className = 'w';
            var s = document.createElement('span'); s.textContent = part; s.style.setProperty('--i', i++);
            w.appendChild(s); frag.appendChild(w);
          });
          n.parentNode.replaceChild(frag, n);
        } else if (n.nodeType === 1 && !n.classList.contains('w')) walk(n);
      });
    })(el);
  });

  /* ---- Reveal on scroll ---- */
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -8% 0px', threshold: .12 });
  $$('.rv, .split-words, .hl').forEach(function (el) { io.observe(el); });

  /* ---- Videos: play only while visible ---- */
  var vio = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      var v = e.target;
      if (e.isIntersecting) {
        if (v.preload === 'none') { v.preload = 'auto'; }
        var p = v.play(); if (p && p.catch) p.catch(function () {});
      } else v.pause();
    });
  }, { threshold: .2 });
  $$('video[data-auto]').forEach(function (v) {
    v.muted = true;
    v.addEventListener('playing', function () { v.classList.add('ready'); });
    if (!reduce) vio.observe(v);
  });

  /* ---- Count-up numbers ---- */
  function money(n, dp) { return '$' + n.toLocaleString('en-US', { minimumFractionDigits: dp, maximumFractionDigits: dp }); }
  var cio = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      cio.unobserve(e.target);
      var el = e.target, to = parseFloat(el.getAttribute('data-count')), dp = +(el.getAttribute('data-dp') || 0);
      var pre = el.getAttribute('data-pre') || '', suf = el.getAttribute('data-suf') || '';
      if (reduce) { el.textContent = pre + to.toLocaleString('en-US', { minimumFractionDigits: dp, maximumFractionDigits: dp }) + suf; return; }
      var t0 = performance.now(), dur = 1600;
      (function f(t) {
        var k = Math.min(1, (t - t0) / dur), v = to * (1 - Math.pow(1 - k, 4));
        el.textContent = pre + v.toLocaleString('en-US', { minimumFractionDigits: dp, maximumFractionDigits: dp }) + suf;
        if (k < 1) requestAnimationFrame(f);
      })(t0);
    });
  }, { threshold: .5 });
  $$('[data-count]').forEach(function (el) { cio.observe(el); });

  /* ---- Boot screen (home, once per visit) ---- */
  var boot = $('.boot');
  if (boot) {
    var seen = false;
    try { seen = sessionStorage.getItem('tipout-boot') === '1'; } catch (e) {}
    if (seen || reduce) { boot.remove(); }
    else {
      doc.classList.add('js-booting');
      var amt = $('.amt', boot), bar = $('.bar i', boot), pct = $('[data-pct]', boot);
      var target = 1981.75, t0 = performance.now(), dur = 1500, finished = false;
      var finish = function () {
        if (finished) return; finished = true;
        boot.classList.add('done'); doc.classList.remove('js-booting');
        try { sessionStorage.setItem('tipout-boot', '1'); } catch (e) {}
        document.dispatchEvent(new Event('tipout:booted'));
        setTimeout(function () { boot.remove(); }, 1000);
      };
      boot.addEventListener('click', finish);
      (function f(t) {
        if (finished) return;
        var k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
        amt.textContent = money(target * e, 2);
        bar.style.width = (e * 100) + '%';
        pct.textContent = String(Math.round(e * 100)).padStart(3, '0') + '%';
        if (k < 1) requestAnimationFrame(f); else setTimeout(finish, 250);
      })(t0);
    }
  }

  /* ---- Feature story: sticky phone swaps clips ---- */
  var story = $('.story');
  if (story) {
    var phone = $('.story-phone .phone'), sv = $('.story-phone video'), simg = $('.story-phone img'), halo = $('.story-phone .halo');
    var steps = $$('.step', story), current = null;
    function activate(step) {
      if (step === current) return; current = step;
      steps.forEach(function (s) { s.classList.toggle('active', s === step); });
      var clip = step.getAttribute('data-clip');
      if (!sv) return;
      phone.classList.add('swap');
      setTimeout(function () { phone.classList.remove('swap'); }, 350);
      simg.src = '/media/posters/screen-' + clip + '.jpg';
      sv.classList.remove('ready');
      sv.poster = simg.src;
      sv.src = '/media/screens/' + clip + '.mp4';
      if (!reduce) { var p = sv.play(); if (p && p.catch) p.catch(function () {}); }
      if (halo) halo.style.setProperty('--halo', step.getAttribute('data-halo') || 'rgba(50,214,123,.45)');
    }
    var sio = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) activate(e.target); });
    }, { rootMargin: '-45% 0px -45% 0px' });
    steps.forEach(function (s) { sio.observe(s); });
    if (sv) sv.addEventListener('playing', function () { sv.classList.add('ready'); });
  }

  /* ---- Reels: hover / tap to preview, click to open ---- */
  var lb = $('.lightbox');
  $$('.reel').forEach(function (r) {
    var v = $('video', r);
    function start() { if (!v || reduce) return; if (v.preload === 'none') v.preload = 'auto'; v.muted = true; v.currentTime = 0; var p = v.play(); if (p && p.catch) p.catch(function () {}); r.classList.add('playing'); }
    function stop() { if (!v) return; v.pause(); r.classList.remove('playing'); }
    r.addEventListener('mouseenter', start);
    r.addEventListener('mouseleave', stop);
    r.addEventListener('click', function () {
      if (!lb) return;
      stop();
      var lv = $('video', lb);
      lv.src = r.getAttribute('data-src'); lv.poster = $('img', r).src;
      $('.cap span', lb).textContent = r.getAttribute('data-title') || '';
      lb.classList.add('open'); lb.setAttribute('aria-hidden', 'false');
      var p = lv.play(); if (p && p.catch) p.catch(function () {});
      $('.x', lb).focus();
    });
  });
  if (lb) {
    var close = function () { lb.classList.remove('open'); lb.setAttribute('aria-hidden', 'true'); var lv = $('video', lb); lv.pause(); };
    $('.x', lb).addEventListener('click', close);
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  }

  /* ---- Countdown ---- */
  var cd = $('.countdown');
  if (cd) {
    var tgt = Date.parse(CONFIG.releaseAt);
    var tickCd = function () {
      var ms = Math.max(0, tgt - Date.now());
      var d = Math.floor(ms / 864e5), h = Math.floor(ms / 36e5) % 24, m = Math.floor(ms / 6e4) % 60, s = Math.floor(ms / 1e3) % 60;
      $('[data-d]', cd).textContent = d; $('[data-h]', cd).textContent = String(h).padStart(2, '0');
      $('[data-m]', cd).textContent = String(m).padStart(2, '0'); $('[data-s]', cd).textContent = String(s).padStart(2, '0');
      if (ms === 0 && !doc.classList.contains('is-live')) applyCTA();
    };
    tickCd(); setInterval(tickCd, 1000);
  }

  /* ---- Falling tips in the launch panel ---- */
  $$('.coins').forEach(function (box) {
    if (reduce) return;
    var glyphs = ['$', '$', '$', '¢', '5', '20', '$1', '%'];
    for (var i = 0; i < 26; i++) {
      var s = document.createElement('span');
      s.textContent = glyphs[i % glyphs.length];
      s.style.left = (Math.random() * 100) + '%';
      s.style.fontSize = (18 + Math.random() * 46) + 'px';
      s.style.animationDuration = (9 + Math.random() * 12) + 's';
      s.style.animationDelay = (-Math.random() * 20) + 's';
      box.appendChild(s);
    }
  });

  /* ---- Footer word: letters wiggle on hover ---- */
  $$('.footer .word').forEach(function (w) {
    w.innerHTML = w.textContent.split('').map(function (c) { return '<span>' + c + '</span>'; }).join('');
  });

  /* ---- Real hourly calculator ---- */
  $$('[data-hourly]').forEach(function (root) {
    var f = {};
    $$('input[type=range]', root).forEach(function (inp) { f[inp.name] = inp; });
    var C = 2 * Math.PI * 160;
    var segs = { card: $('[data-seg=card]', root), cash: $('[data-seg=cash]', root), wage: $('[data-seg=wage]', root) };
    function fill(inp) { inp.style.setProperty('--p', ((inp.value - inp.min) / (inp.max - inp.min) * 100) + '%'); }
    function update() {
      var hrs = +f.hours.value, card = +f.card.value, cash = +f.cash.value, rate = +f.wage.value, out = +f.tipout.value;
      var wages = rate * hrs, gross = card + cash + wages, take = Math.max(0, gross - out), hourly = hrs ? take / hrs : 0;
      $$('[data-out]', root).forEach(function (o) {
        var k = o.getAttribute('data-out');
        var v = { hours: hrs.toFixed(1) + ' hrs', card: money(card, 2), cash: money(cash, 2), wage: money(rate, 2) + '/hr', tipout: '−' + money(out, 2),
          take: money(take, 2), hourly: money(hourly, 2) + '/hr', tips: money(card + cash, 0), tipsHr: money(hrs ? (card + cash) / hrs : 0, 2) + '/hr', wages: money(wages, 2) }[k];
        if (v != null) o.textContent = v;
      });
      var off = 0, gap = 6;
      ['card', 'cash', 'wage'].forEach(function (k) {
        var val = k === 'wage' ? wages : (k === 'card' ? card : cash);
        var len = gross ? Math.max(0, val / gross * C - gap) : 0;
        segs[k].setAttribute('stroke-dasharray', len + ' ' + C);
        segs[k].setAttribute('stroke-dashoffset', -off);
        off += val / gross * C;
      });
      $$('[data-pct]', root).forEach(function (o) {
        var k = o.getAttribute('data-pct'), val = { card: card, cash: cash, wage: wages, tipout: out }[k];
        o.textContent = gross ? Math.round(val / gross * 100) + '%' : '0%';
      });
      Object.keys(f).forEach(function (k) { fill(f[k]); });
    }
    Object.keys(f).forEach(function (k) { f[k].addEventListener('input', update); });
    update();
  });
})();
