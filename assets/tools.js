/* Bar split: pool card and cash, take tip-out out in proportion, split by hours to the cent. */
(function () {
  var root = document.querySelector('[data-barsplit]');
  if (!root) return;
  var people = [['Maya', 8], ['Jess', 7], ['Marcus', 6.5], ['Steve', 5.5]];
  var list = root.querySelector('[data-people]');
  var money = function (c) { return '$' + (c / 100).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); };
  var cents = function (v) { var n = parseFloat(String(v).replace(/[^0-9.]/g, '')); return isFinite(n) ? Math.round(n * 100) : 0; };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };

  // Largest-remainder split so the parts always add up to the whole.
  function share(total, weights) {
    var sum = weights.reduce(function (a, b) { return a + b; }, 0);
    if (!sum) return weights.map(function () { return 0; });
    var raw = weights.map(function (w) { return total * w / sum; });
    var base = raw.map(Math.floor), left = total - base.reduce(function (a, b) { return a + b; }, 0);
    raw.map(function (r, i) { return [r - base[i], i]; }).sort(function (a, b) { return b[0] - a[0]; })
      .slice(0, left).forEach(function (x) { base[x[1]]++; });
    return base;
  }

  function render() {
    list.innerHTML = people.map(function (p, i) {
      return '<div class="inp f-hours"><input class="name" aria-label="Name" value="' + esc(p[0]) + '" data-i="' + i + '" data-f="0">' +
        '<input class="hrs" inputmode="decimal" aria-label="Hours for ' + esc(p[0]) + '" value="' + p[1] + '" data-i="' + i + '" data-f="1"><span>hrs</span>' +
        '<button class="x" type="button" aria-label="Remove ' + esc(p[0]) + '" data-rm="' + i + '">×</button></div>';
    }).join('');
    calc();
  }

  function calc() {
    var card = cents(root.querySelector('[data-k=card]').value);
    var cash = cents(root.querySelector('[data-k=cash]').value);
    var out = Math.min(cents(root.querySelector('[data-k=tipout]').value), card + cash);
    var outCard = card + cash ? Math.round(out * card / (card + cash)) : 0;
    var netCard = card - outCard, netCash = cash - (out - outCard);
    var hrs = people.map(function (p) { return Math.max(0, parseFloat(p[1]) || 0); });
    var totalH = hrs.reduce(function (a, b) { return a + b; }, 0);
    var c = share(netCard, hrs), k = share(netCash, hrs);
    var pool = netCard + netCash;
    root.querySelector('[data-pool]').textContent = 'Pool ' + money(pool) + ' · ' + totalH + ' hrs';
    root.querySelector('[data-each]').textContent = totalH ? 'Each bartender makes ' + money(Math.round(pool / totalH)) + '/hr' : 'Add some hours';
    root.querySelector('[data-results]').innerHTML = people.map(function (p, i) {
      return '<div class="result-row"><span>' + esc(p[0] || 'Bartender ' + (i + 1)) + '</span><b>' + money(c[i] + k[i]) + '</b>' +
        '<small>' + hrs[i] + ' hrs · ' + money(c[i]) + ' card · ' + money(k[i]) + ' cash</small></div>';
    }).join('');
  }

  root.addEventListener('input', function (e) {
    var t = e.target;
    if (t.hasAttribute('data-i')) {
      people[+t.getAttribute('data-i')][+t.getAttribute('data-f')] = t.value;
      if (t.getAttribute('data-f') === '0') { /* names update results only */ }
    }
    calc();
  });
  root.addEventListener('click', function (e) {
    var rm = e.target.closest('[data-rm]');
    if (rm) { people.splice(+rm.getAttribute('data-rm'), 1); render(); }
    if (e.target.closest('[data-addp]')) { people.push(['Bartender ' + (people.length + 1), 6]); render(); }
  });
  render();
})();
