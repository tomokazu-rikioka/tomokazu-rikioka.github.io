/* ==========================================================================
   ドット絵のチャトラ — PixelCat
   40x24 のドット絵（gen_sprites.py で生成）を canvas に描画して動かす。
   使い方: PixelCat.mount({ scale: 4, ground: 25 })
   フレーム: walk x4（歩行サイクル） / sit x2（まばたき） / sleep x2（呼吸）
   ========================================================================== */
(function (global) {
  'use strict';

  var COLS = 40, ROWS = 24;

  var PALETTE = {
    '.': null,
    'b': '#7c4a12',
    'o': '#f2a93b',
    'h': '#f9c168',
    'f': '#dd9128',
    'd': '#d8821e',
    's': '#c96f14',
    'c': '#fbe7be',
    'n': '#ecd3a0',
    'g': '#8cbf3f',
    'k': '#241a10',
    'p': '#f0a49a'
};

  var FRAMES = {
    walk: [[
    '...................................b....',
    '...bb.......................b.....bob...',
    '..bccb.....................bfb...boob...',
    '.bcccb....................bffbbbbopoob..',
    '.bddb......................bbhdhdhbbb...',
    '.bddob....................bbododoooob...',
    '..boob......bbbbbbbbbbbbbboooookkoooob..',
    '..booob...bbhhhhhhhhhhhhhooooooggkooob..',
    '...bdddb.bhhdoodoodoodoodoooooooooccppb.',
    '....bddobododoodoodoodooddooooooocccckb.',
    '.....booodooodoodoodoodooddoooooocccccb.',
    '......bbodooodoodoodoodoodooooooocccob..',
    '.......boooodoodoodoodooooccbooooooob...',
    '.......boooodoodoodoodooooccbboooobb....',
    '.......boooocccdccdccccccooob.bbbb......',
    '.......boocccccccccccccccccb............',
    '........bccoocccccccccccoocb............',
    '.........bboocccccccccccoob.............',
    '.........boobbffbbbbffbbboob............',
    '.........boobbffb..bffb.boob............',
    '.........boobbffb..bffb.boob............',
    '........bccb..bccbbccb...bccb...........',
    '.......bcccb..bccccccb...bcccb..........',
    '........bbb....bbbbbb.....bbb...........'
  ], [
    '...bb.......................b.....bob...',
    '..bccb.....................bfb...boob...',
    '.bcccb....................bffbbbbopoob..',
    '.bddb......................bbhdhdhbbb...',
    '.bddob....................bbododoooob...',
    '..boob......bbbbbbbbbbbbbboooookkoooob..',
    '..booob...bbhhhhhhhhhhhhhooooooggkooob..',
    '...bdddb.bhhdoodoodoodoodoooooooooccppb.',
    '....bddobododoodoodoodooddooooooocccckb.',
    '.....booodooodoodoodoodooddoooooocccccb.',
    '......bbodooodoodoodoodoodooooooocccob..',
    '.......boooodoodoodoodooooccbooooooob...',
    '.......boooodoodoodoodooooccbboooobb....',
    '.......boooocccdccdccccccooob.bbbb......',
    '.......boocccccccccccccccccb............',
    '........bccccccccccccccccccb............',
    '.........bboocccccccccccoob.............',
    '..........booffbbbbbbffboob.............',
    '..........booffb....bffboob.............',
    '..........booffb....bffboob.............',
    '..........booccb....bccboob.............',
    '..........bcccccb...bcccccb.............',
    '..........bcccbb.....bbbcccb............',
    '...........bbb..........bbb.............'
  ], [
    '...................................b....',
    '...bb.......................b.....bob...',
    '..bccb.....................bfb...boob...',
    '.bcccb....................bffbbbbopoob..',
    '.bddb......................bbhdhdhbbb...',
    '.bddob....................bbododoooob...',
    '..boob......bbbbbbbbbbbbbboooookkoooob..',
    '..booob...bbhhhhhhhhhhhhhooooooggkooob..',
    '...bdddb.bhhdoodoodoodoodoooooooooccppb.',
    '....bddobododoodoodoodooddooooooocccckb.',
    '.....booodooodoodoodoodooddoooooocccccb.',
    '......bbodooodoodoodoodoodooooooocccob..',
    '.......boooodoodoodoodooooccbooooooob...',
    '.......boooodoodoodoodooooccbboooobb....',
    '.......boooocccdccdccccccooob.bbbb......',
    '.......boocccccccccccccccccb............',
    '........bccoocccccccccccoocb............',
    '.........bboocccccccccccoob.............',
    '...........boobbbbbbbbfoob..............',
    '...........boob......bfoob..............',
    '...........boob......bfoob..............',
    '..........bccccb.....bcccb..............',
    '.........bccccccb...bcccccb.............',
    '..........bbbbbb.....bbbbb..............'
  ], [
    '...bb.......................b.....bob...',
    '..bccb.....................bfb...boob...',
    '.bcccb....................bffbbbbopoob..',
    '.bddb......................bbhdhdhbbb...',
    '.bddob....................bbododoooob...',
    '..boob......bbbbbbbbbbbbbboooookkoooob..',
    '..booob...bbhhhhhhhhhhhhhooooooggkooob..',
    '...bdddb.bhhdoodoodoodoodoooooooooccppb.',
    '....bddobododoodoodoodooddooooooocccckb.',
    '.....booodooodoodoodoodooddoooooocccccb.',
    '......bbodooodoodoodoodoodooooooocccob..',
    '.......boooodoodoodoodooooccbooooooob...',
    '.......boooodoodoodoodooooccbboooobb....',
    '.......boooocccdccdccccccooob.bbbb......',
    '.......boocccccccccccccccccb............',
    '........bccccccccccccccccccb............',
    '.........bboocccccccccccoob.............',
    '..........booffbbbbbbffboob.............',
    '..........booffb....bffboob.............',
    '..........booffb....bffboob.............',
    '..........bccffb....bffbccb.............',
    '..........bccccb....bccbcccb............',
    '...........bbcccb...bcccbbb.............',
    '.............bbb.....bbb................'
  ]],
    sit: [[
    '.............bob........bob.............',
    '............bopbbbbbbbbbopb.............',
    '............bopoooooooooopob............',
    '.............booodododoooob.............',
    '............booododododoooob............',
    '............boooooooooooooob............',
    '............bdoogkooookgoodb............',
    '............bdoogkooookgoodb............',
    '............booocccppcccooob............',
    '............booocckcckccooob............',
    '.............booccccccccoob.............',
    '..............boccccccccob..............',
    '...............boooooooob...............',
    '..............booccccccoob..............',
    '..............booccccccoob..............',
    '.............booccccccccoob.............',
    '.............booccccccccoob.............',
    '............booocccnncccooob............',
    '............booccccnnccccoob............',
    '...........bodoccccnnccccodob...........',
    '...........boooccccnnccccoooobbb........',
    '...........boocccccnncccccooodocb.......',
    '............bocncccnncccncobodoccb......',
    '.............bbbbbbbbbbbbbb.bbbbb.......'
  ], [
    '.............bob........bob.............',
    '............bopbbbbbbbbbopb.............',
    '............bopoooooooooopob............',
    '.............booodododoooob.............',
    '............booododododoooob............',
    '............boooooooooooooob............',
    '............bdoooooooooooodb............',
    '............bdookkooookkoodb............',
    '............booocccppcccooob............',
    '............booocckcckccooob............',
    '.............booccccccccoob.............',
    '..............boccccccccob..............',
    '...............boooooooob...............',
    '..............booccccccoob..............',
    '..............booccccccoob..............',
    '.............booccccccccoob.............',
    '.............booccccccccoob.............',
    '............booocccnncccooob............',
    '............booccccnnccccoob............',
    '...........bodoccccnnccccodob...........',
    '...........boooccccnnccccoooobbb........',
    '...........boocccccnncccccooodocb.......',
    '............bocncccnncccncobodoccb......',
    '.............bbbbbbbbbbbbbb.bbbbb.......'
  ]],
    sleep: [[
    '........................................',
    '........................................',
    '........................................',
    '........................................',
    '........................................',
    '........................................',
    '........................................',
    '........................................',
    '........b...............................',
    '.......bob...bbbbbbbbbbbbb..............',
    '......bopobbbooooooooooooobbb...........',
    '.......boooooooooodooodooodoobb.........',
    '......boooooooosoodooodooodoodob........',
    '.....boooooooooosodooodooodooodob.......',
    '.....boooooooooosoodooodooodoodoob......',
    '.....bookkoookkosoodooodooodooooob......',
    '.....booccppccooooooooooooooooodob......',
    '.....booccccccooooooooooooooooodob......',
    '.....booooooooooooooooooooooooooob......',
    '......booooooooccccccccccccccooob.......',
    '.......bocccccccccooddoooddoooob........',
    '........bbocccccooddoooddoooobb.........',
    '..........bbbocccccccccccobbb...........',
    '.............bbbbbbbbbbbbb..............'
  ], [
    '........................................',
    '........................................',
    '........................................',
    '........................................',
    '........................................',
    '........................................',
    '........................................',
    '........................................',
    '........b...............................',
    '.......bob..............................',
    '......bopobbbbbbbbbbbbbbbbb.............',
    '.......booooooooooooooooooobbbb.........',
    '......boooooooosoodooodooodoodob........',
    '.....boooooooooosodooodooodooodob.......',
    '.....boooooooooosodooodooodooodoob......',
    '.....bookkoookkosoodooodooodooooob......',
    '.....booccppccooooooooooooooooodob......',
    '.....booccccccooooooooooooooooodob......',
    '.....booooooooooooooooooooooooooob......',
    '......booooooooccccccccccccccooob.......',
    '.......bocccccccccooddoooddoooob........',
    '........bbocccccooddoooddoooobb.........',
    '..........bbbocccccccccccobbb...........',
    '.............bbbbbbbbbbbbb..............'
  ]]
  };

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
      host: document.body, scale: 4, ground: 24, speak: 'nya',
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
    var blinkTime = 0, nextBlink = rand(2.5, 5);
    var minX = 6, maxX = 100;
    var lastActivity = performance.now();

    function measure() {
      minX = 6;
      maxX = Math.max(minX, window.innerWidth - W - 6);
      x = clamp(x, minX, maxX);
    }

    function render() {
      if (state === 'sleep') { paint(ctx, FRAMES.sleep[frame % 2], opt.scale); return; }
      if (state === 'sit') { paint(ctx, FRAMES.sit[frame % 2], opt.scale); return; }
      paint(ctx, FRAMES.walk[frame % 4], opt.scale);
    }

    function apply() {
      wrap.style.transform = 'translate3d(' + x.toFixed(1) + 'px,0,0)';
      wrap.style.setProperty('--sx', dir);
      inner.style.transform = 'scaleX(' + dir + ')';
    }

    function setState(next) {
      if (state === next) return;
      state = next;
      frame = 0;
      frameTime = 0;
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
        if (Math.random() < 0.45) { setState('sit'); schedule(rand(2, 4.5)); }
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
          schedule(rand(1.6, 3));
        }
        if (x >= maxX) { x = maxX; dir = -1; }
        else if (x <= minX) { x = minX; dir = 1; }

        frameTime += dt;
        var step = state === 'run' ? 0.08 : 0.14;
        if (frameTime >= step) { frameTime = 0; frame++; render(); }
        apply();
      } else if (state === 'sit') {
        // ときどきまばたき
        blinkTime += dt;
        if (frame % 2 === 1 && blinkTime > 0.15) {
          frame = 0; blinkTime = 0; nextBlink = rand(2.5, 5); render();
        } else if (frame % 2 === 0 && blinkTime > nextBlink) {
          frame = 1; blinkTime = 0; render();
        }
      } else if (state === 'sleep') {
        // ゆっくり呼吸
        frameTime += dt;
        if (frameTime >= 1.4) { frameTime = 0; frame++; render(); }
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

  global.PixelCat = { mount: mount, FRAMES: FRAMES, PALETTE: PALETTE, COLS: COLS, ROWS: ROWS };
})(window);
