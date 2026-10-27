/* وجوه العيش — تصفية الأصل + لغة القراءة + التنقل بالأسهم */
(function () {
  'use strict';
  var AR = '٠١٢٣٤٥٦٧٨٩';
  function arDigits(n) { return String(n).replace(/\d/g, function (d) { return AR[d]; }); }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) {} return null; }

  // ———— الرئيسية: تصفية حسب الأصل ————
  var chips = document.querySelectorAll('.chip');
  if (chips.length) {
    var tiles = document.querySelectorAll('.tile');
    var shown = document.getElementById('shown');
    function apply(g) {
      var n = 0;
      tiles.forEach(function (t) {
        var ok = !g || t.getAttribute('data-group') === g;
        t.hidden = !ok;
        if (ok) n++;
      });
      chips.forEach(function (c) { c.classList.toggle('is-on', c.getAttribute('data-g') === g); });
      if (shown) shown.textContent = arDigits(n);
      if (history.replaceState) history.replaceState(null, '', g ? '#g=' + g : location.pathname + location.search);
    }
    chips.forEach(function (c) {
      c.addEventListener('click', function () { apply(c.getAttribute('data-g') || ''); });
    });
    var m = /#g=([a-z]+)/.exec(location.hash);
    if (m && document.querySelector('.chip[data-g="' + m[1] + '"]')) apply(m[1]);
  }

  // ———— صفحة الوجه: لغة القراءة ————
  var rd = document.getElementById('reading');
  if (rd) {
    var btns = rd.querySelectorAll('.langbar button');
    function setLang(l) {
      rd.setAttribute('data-lang', l);
      btns.forEach(function (b) { b.classList.toggle('is-on', b.getAttribute('data-l') === l); });
    }
    var saved = store('wa-lang');
    if (saved === 'ar' || saved === 'en' || saved === 'both') setLang(saved);
    btns.forEach(function (b) {
      b.addEventListener('click', function () { var l = b.getAttribute('data-l'); setLang(l); store('wa-lang', l); });
    });
  }

  // ———— التنقل بالأسهم (الصفحة عربية: اليسار = التالي) ————
  var face = document.querySelector('.face');
  if (face) {
    document.addEventListener('keydown', function (e) {
      if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      var t = e.target && e.target.tagName;
      if (t === 'INPUT' || t === 'TEXTAREA' || t === 'SELECT') return;
      var id = e.key === 'ArrowLeft' ? face.getAttribute('data-next')
             : e.key === 'ArrowRight' ? face.getAttribute('data-prev') : '';
      if (id) location.href = '../' + id + '/';
    });
  }
})();
