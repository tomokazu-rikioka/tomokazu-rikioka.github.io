/* ==========================================================================
   訪問者カウンター
   静的サイトなので、カウント自体は外部の無料 API（abacus）に置いている。
   - 初回訪問時に /hit で採番し、その番号を localStorage に保存
   - 2 回目以降は保存した番号をそのまま表示（毎回増えたりしない）
   - API が落ちている場合はブロックごと非表示（壊れた表示を出さない）
   ========================================================================== */
(function () {
  'use strict';

  var ENDPOINT = 'https://abacus.jasoncameron.dev/hit/tomokazu-rikioka-github-io/visits-live';
  var STORE_KEY = 'rick.visitor.no';

  var box = document.getElementById('visitor');
  var out = document.getElementById('visitor-num');
  if (!box || !out) return;

  var saved = null;
  try { saved = localStorage.getItem(STORE_KEY); } catch (e) { /* プライベートモード等 */ }

  if (saved && /^[1-9]\d*$/.test(saved)) {
    show(Number(saved));
    return;
  }

  fetch(ENDPOINT, { cache: 'no-store' })
    .then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.json();
    })
    .then(function (data) {
      var n = Number(data && data.value);
      if (!isFinite(n) || n < 1) throw new Error('invalid value');
      try { localStorage.setItem(STORE_KEY, String(n)); } catch (e) {}
      show(n);
    })
    .catch(function () { /* 取得できなければ何も出さない */ });

  function show(n) {
    box.hidden = false;
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce || n < 2) {
      out.textContent = n.toLocaleString('ja-JP');
      return;
    }
    var dur = 900;
    var t0 = performance.now();
    requestAnimationFrame(function step(t) {
      var p = Math.min(1, (t - t0) / dur);
      var eased = 1 - Math.pow(1 - p, 3);
      out.textContent = Math.round(n * eased).toLocaleString('ja-JP');
      if (p < 1) requestAnimationFrame(step);
    });
  }
})();
