/* ==========================================================================
   ドット絵のチャトラ — PixelCat（D案 Data Lab 用）
   22x14 のドットを canvas に等倍描画して歩かせる小さなエンジン。
   使い方: PixelCat.mount({ scale: 5, ground: 26 })
   ========================================================================== */
(function (global) {
  'use strict';

  var COLS = 22, ROWS = 14;

  var PALETTE = {
    '.': null,
    o: '#f2a93b',   // 地の毛
    d: '#c9761a',   // 縞
    c: '#fbe7be',   // クリーム（腹・足先）
    k: '#1c1710',   // 目・輪郭
    g: '#8cbf3f',   // 瞳
    p: '#e8897d'    // 鼻
  };

  /* 胴体〜頭（0〜10 行目）。脚だけ差し替えて歩かせる */
  var BODY = [
    '......................',
    '...............o..o...',
    'o..............oo.oo..',
    'oo............oooooooo',
    '.o............oogoogoo',
    '.o...........ooooooooo',
    '.ooooooooooooooocpcooo',
    '.odoodoodooooooccccooo',
    '.oooooooooooooooooooo.',
    '.occcccccccccccooooo..',
    '..ooooooooooooooooo...'
  ];

  /* 脚（11〜13 行目）の 4 コマ */
  var LEGS = [
    ['..oo...oo....oo..oo...', '..oo...oo....oo..oo...', '..cc...cc....cc..cc...'],
    ['...oo.oo......oo.oo...', '...oo.oo......oo.oo...', '...cc.cc......cc.cc...'],
    ['.oo.....oo..oo.....oo.', '.oo.....oo..oo.....oo.', '.cc.....cc..cc.....cc.'],
    ['...oo.oo......oo.oo...', '...oo.oo......oo.oo...', '...cc.cc......cc.cc...']
  ];

  /* お座り */
  var SIT = [
    '......................',
    '...............o..o...',
    'o..............oo.oo..',
    'oo............oooooooo',
    '.o............oogoogoo',
    '.o...........ooooooooo',
    '.oo.........oooocpcooo',
    '.ooo........ooooccccoo',
    '..ooo......ooooooooooo',
    '..oooooooooooooooooo..',
    '..occcccccccccccccoo..',
    '...oooooooooo...oo....',
    '...cccccccccc...oo....',
    '................cc....'
  ];

  /* 丸くなって就寝 */
  var SLEEP = [
    '......................',
    '......................',
    '..o.o.................',
    '.ooooo......oooooo....',
    'ooooooo..ooooooooooo..',
    'okkookoooooooooooooooo',
    'opccoooooodoooodoooooo',
    '.occooooooooooooooooo.',
    '..oooooooooooooooooo..',
    '..cccccccccccccccccc..',
    '...occcccccccccccco...',
    '....oooooooooooooo....',
    '......................',
    '......................'
  ];

  function rand(min, max) { return min + Math.random() * (max - min); }
  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }

  function paint(ctx, rows, scale) {
    ctx.clearRect(0, 0, COLS * scale, ROWS * scale);
    for (var y = 0; y < rows.length; y++) {
      var row = rows[y];
      for (var x = 0; x < row.length; x++) {
        var col = PALETTE[row.charAt(x)];
        if (!col) continue;
        ctx.fillStyle = col;
        ctx.fillRect(x * scale, y * scale, scale, scale);
      }
    }
  }

  function mount(options) {
    var opt = Object.assign({
      host: document.body, scale: 5, ground: 24, speak: 'nya',
      idleToSleep: 45000, walkSpeed: 54, runSpeed: 150
    }, options || {});

    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var dpr = Math.min(3, window.devicePixelRatio || 1);
    var W = COLS * opt.scale, H = ROWS * opt.scale;

    var stage = document.createElement('div');
    stage.className = 'pixcat-stage';
    stage.setAttribute('aria-hidden', 'true');

    var wrap = document.createElement('div');
    wrap.className = 'pixcat';
    wrap.style.width = W + 'px';
    wrap.style.height = H + 'px';
    wrap.style.bottom = opt.ground + 'px';

    var bubble = document.createElement('div');
    bubble.className = 'pixcat__bubble';
    bubble.textContent = opt.speak;

    var inner = document.createElement('div');
    inner.className = 'pixcat__inner';

    var canvas = document.createElement('canvas');
    canvas.width = W * dpr;
    canvas.height = H * dpr;
    canvas.style.width = W + 'px';
    canvas.style.height = H + 'px';
    inner.appendChild(canvas);
    wrap.appendChild(bubble);
    wrap.appendChild(inner);
    stage.appendChild(wrap);
    opt.host.appendChild(stage);

    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    ctx.imageSmoothingEnabled = false;

    var state = 'walk', dir = 1, x = 0, target = null;
    var frame = 0, frameTime = 0, raf = null, last = 0, timer = null, bubbleTimer = null;
    var minX = 6, maxX = 100;
    var lastActivity = performance.now();

    function measure() {
      minX = 6;
      maxX = Math.max(minX, window.innerWidth - W - 6);
      x = clamp(x, minX, maxX);
    }

    function render() {
      if (state === 'sleep') { paint(ctx, SLEEP, opt.scale); return; }
      if (state === 'sit') { paint(ctx, SIT, opt.scale); return; }
      paint(ctx, BODY.concat(LEGS[frame % LEGS.length]), opt.scale);
    }

    function apply() {
      wrap.style.transform = 'translate3d(' + x.toFixed(1) + 'px,0,0)';
      wrap.style.setProperty('--sx', dir);
      inner.style.transform = 'scaleX(' + dir + ')';
    }

    function setState(next) {
      if (state === next) return;
      state = next;
      wrap.classList.toggle('is-sleep', next === 'sleep');
      render();
    }

    function schedule(sec) {
      clearTimeout(timer);
      timer = setTimeout(decide, sec * 1000);
    }

    function decide() {
      if (state === 'sleep') return;
      if (state === 'walk' || state === 'run') {
        if (Math.random() < 0.45) { setState('sit'); schedule(rand(1.6, 3.2)); }
        else schedule(rand(3, 6));
      } else {
        if (Math.random() < 0.4) dir = -dir;
        setState('walk');
        schedule(rand(3.5, 7));
      }
    }

    function goTo(clientX) {
      if (reduce) return;
      if (state === 'sleep') wake();
      var t = clamp(clientX - W / 2, minX, maxX);
      if (Math.abs(t - x) < 20) return;
      target = t;
      dir = t > x ? 1 : -1;
      setState(Math.abs(t - x) > 320 ? 'run' : 'walk');
      clearTimeout(timer);
    }

    function speak(text) {
      if (text) bubble.textContent = text;
      wrap.classList.add('is-talking');
      clearTimeout(bubbleTimer);
      bubbleTimer = setTimeout(function () { wrap.classList.remove('is-talking'); }, 1700);
    }

    function wake() {
      if (state !== 'sleep') return;
      setState('sit');
      schedule(1.2);
    }

    function tick(now) {
      raf = requestAnimationFrame(tick);
      var dt = Math.min(0.05, (now - last) / 1000);
      last = now;

      if (state === 'walk' || state === 'run') {
        var sp = state === 'run' ? opt.runSpeed : opt.walkSpeed;
        x += dir * sp * dt;

        if (target !== null && ((dir > 0 && x >= target) || (dir < 0 && x <= target))) {
          x = target; target = null;
          setState('sit');
          schedule(rand(1.4, 2.6));
        }
        if (x >= maxX) { x = maxX; dir = -1; }
        else if (x <= minX) { x = minX; dir = 1; }

        frameTime += dt;
        var step = state === 'run' ? 0.085 : 0.15;
        if (frameTime >= step) { frameTime = 0; frame++; render(); }
        apply();
      }

      if (state !== 'sleep' && now - lastActivity > opt.idleToSleep) {
        target = null;
        clearTimeout(timer);
        setState('sleep');
      }
    }

    function activity() {
      lastActivity = performance.now();
      if (state === 'sleep') wake();
    }
    ['pointerdown', 'pointermove', 'keydown', 'wheel', 'touchstart'].forEach(function (ev) {
      window.addEventListener(ev, activity, { passive: true });
    });

    inner.addEventListener('click', function (e) {
      e.stopPropagation();
      activity();
      if (!reduce) {
        wrap.classList.add('is-hop');
        setTimeout(function () { wrap.classList.remove('is-hop'); }, 520);
      }
      speak(opt.speak);
    });

    document.addEventListener('click', function (e) {
      if (e.target.closest('a, button, input, textarea, select, label, .pixcat__inner')) return;
      goTo(e.clientX);
    });

    window.addEventListener('resize', function () { measure(); apply(); });
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) { cancelAnimationFrame(raf); raf = null; }
      else if (!raf && !reduce) { last = performance.now(); raf = requestAnimationFrame(tick); }
    });

    measure();
    x = rand(minX + 40, Math.max(minX + 41, maxX * 0.55));
    apply();
    render();

    if (reduce) {
      setState('sit');
    } else {
      schedule(rand(4, 7));
      last = performance.now();
      raf = requestAnimationFrame(tick);
    }

    return {
      el: wrap,
      goTo: goTo,
      speak: speak,
      setState: setState,
      destroy: function () { cancelAnimationFrame(raf); clearTimeout(timer); stage.remove(); }
    };
  }

  global.PixelCat = { mount: mount, COLS: COLS, ROWS: ROWS };
})(window);
