#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""高解像度ドット絵チャトラのスプライト生成器。
40x26 グリッド。文字 = パレットキー。'.' は透明。
実行すると ASCII プレビューと preview.html（拡大表示）と sprites.json を出力する。
"""
import json, os, copy

W, H = 40, 26

PALETTE = {
    '.': None,
    'b': '#7c4a12',   # 輪郭（自動生成）
    'o': '#f2a93b',   # 地の毛
    'h': '#f9c168',   # 背のハイライト
    'f': '#dd9128',   # 奥側の毛（陰）
    'd': '#d8821e',   # 縞
    's': '#c96f14',   # 濃い縞・陰
    'c': '#fbe7be',   # クリーム
    'n': '#ecd3a0',   # クリームの陰（脚の分かれ目）
    'g': '#8cbf3f',   # 瞳の緑
    'k': '#241a10',   # 目・鼻すじ
    'p': '#f0a49a',   # 耳の内・鼻
}

def new():
    return [['.'] * W for _ in range(H)]

def put(g, r, c, s):
    for i, ch in enumerate(s):
        if ch != ' ' and 0 <= r < H and 0 <= c + i < W:
            g[r][c + i] = ch

def hline(g, r, c1, c2, ch):
    for c in range(c1, c2 + 1):
        if 0 <= r < H and 0 <= c < W:
            g[r][c] = ch

def outline(g):
    """シルエットの外周 1px に輪郭色 b を足す"""
    o = copy.deepcopy(g)
    for r in range(H):
        for c in range(W):
            if g[r][c] == '.':
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    rr, cc = r+dr, c+dc
                    if 0 <= rr < H and 0 <= cc < W and g[rr][cc] not in '.b':
                        o[r][c] = 'b'
                        break
    return o

# ---------------------------------------------------------------- 歩き（右向き）
def walk_body(g, yo):
    """胴体・頭・尻尾。yo は上下ボブ（-1 で 1px 浮く）"""
    def P(r, c, s): put(g, r + yo, c, s)
    def L(r, c1, c2, ch): hline(g, r + yo, c1, c2, ch)

    # 尻尾（左へ、先端が上がる）リング縞＋クリームの先
    P(2, 3, 'cc')
    P(3, 2, 'ccc')
    P(4, 2, 'dd')
    P(5, 2, 'ddo')
    P(6, 3, 'oo')
    P(7, 3, 'ooo')
    P(8, 4, 'ddd')
    P(9, 5, 'ddo')
    P(10, 6, 'oo')

    # 胴体シルエット
    L(7, 12, 24, 'h')
    L(8, 10, 26, 'o'); P(8, 10, 'hh')
    L(9, 9, 27, 'o')
    for r in range(10, 15):
        L(r, 8, 27, 'o')
    L(15, 8, 26, 'o')
    L(16, 9, 26, 'o')
    L(17, 11, 24, 'o')

    # 腹のクリーム
    L(14, 12, 24, 'c')
    L(15, 10, 26, 'c')
    L(16, 9, 26, 'c')
    L(17, 11, 24, 'c')

    # 胴体の縞（縦にうねる）
    for base, top, bot in ((12, 8, 13), (15, 8, 14), (18, 8, 14), (21, 8, 13), (24, 8, 11)):
        for r in range(top, bot + 1):
            kink = 1 if (r - top) in (2, 3) else 0
            P(r, base + kink, 'd')
    # 肩・尻の曲線縞
    P(9, 10, 'd'); P(10, 9, 'd'); P(11, 9, 'd')
    P(9, 25, 'd'); P(10, 26, 'd')

    # 頭
    P(4, 29, 'ooooo')
    P(5, 28, 'oooooooo')
    P(6, 27, 'oooooooooo')
    P(7, 27, 'oooooooooo')
    P(8, 27, 'ooooooooooo')
    P(9, 27, 'ooooooooooo')
    P(10, 27, 'ooooooooooo')
    P(11, 28, 'ooooooooo')
    P(12, 29, 'ooooooo')
    P(13, 30, 'oooo')

    # 耳（手前＝右上、奥＝左）: 先端 1px から広がる三角
    P(1, 35, 'o')
    P(2, 34, 'oo')
    P(3, 33, 'opoo')
    P(2, 28, 'f')
    P(3, 27, 'ff')

    # 首のつなぎを滑らかに
    P(7, 25, 'oo')
    P(6, 26, 'o')

    # 頭頂のハイライトと額の M 模様
    P(4, 29, 'hhhhh')
    P(4, 30, 'd'); P(4, 32, 'd')
    P(5, 31, 'd'); P(5, 29, 'd')

    # 目（横顔・片目：上まぶた＋緑）
    P(6, 31, 'kk')
    P(7, 31, 'gg'); P(7, 33, 'k')

    # マズル（クリーム）と鼻・口
    P(8, 34, 'ccc')
    P(9, 33, 'ccccc')
    P(10, 33, 'ccccc')
    P(11, 33, 'ccc')
    P(8, 36, 'pp')
    P(9, 37, 'k')

    # 胸のクリーム
    P(12, 26, 'cc')
    P(13, 26, 'cc')

def leg(g, hip_col, slant, color, lift=0):
    """rows16-22 の脚。slant=+2 前へ / -2 後ろへ。lift で浮かせる"""
    rows = list(range(16, 23 - lift))
    n = len(rows) - 1
    for i, r in enumerate(rows):
        off = round(slant * i / n) if n else 0
        c = hip_col + off
        paw = r >= rows[-1] - 1
        ch = 'c' if paw else color
        put(g, r, c, ch + ch)
    # 足先を進行方向へ 1px
    last_off = slant
    put(g, rows[-1], hip_col + last_off + (2 if slant >= 0 else -1), 'c')

def walk_frame(i):
    g = new()
    yo = -1 if i % 2 == 1 else 0
    # 奥側の脚（先に描いて背面へ）
    if i == 0:
        leg(g, 13, +2, 'f'); leg(g, 21, -2, 'f')
    elif i == 1:
        leg(g, 13, 0, 'f', lift=1); leg(g, 21, 0, 'f', lift=1)
    elif i == 2:
        leg(g, 13, -2, 'f'); leg(g, 21, +2, 'f')
    else:
        leg(g, 13, 0, 'f'); leg(g, 21, 0, 'f')
    walk_body(g, yo)
    # 手前側の脚
    if i == 0:
        leg(g, 11, -2, 'o'); leg(g, 24, +2, 'o')
    elif i == 1:
        leg(g, 11, 0, 'o'); leg(g, 24, 0, 'o')
    elif i == 2:
        leg(g, 11, +2, 'o'); leg(g, 24, -2, 'o')
    else:
        leg(g, 11, 0, 'o', lift=1); leg(g, 24, 0, 'o', lift=1)
    return outline(g)

# ---------------------------------------------------------------- お座り（正面）
def sit_frame(blink=False):
    g = new()
    # 尻尾（右へ巻く）
    put(g, 20, 27, 'oo')
    put(g, 21, 27, 'oodoc')
    put(g, 22, 28, 'odocc')

    # 胴体（下すぼまりの台形）
    hline(g, 12, 16, 23, 'o')
    hline(g, 13, 15, 24, 'o')
    hline(g, 14, 15, 24, 'o')
    hline(g, 15, 14, 25, 'o')
    hline(g, 16, 14, 25, 'o')
    hline(g, 17, 13, 26, 'o')
    hline(g, 18, 13, 26, 'o')
    hline(g, 19, 12, 27, 'o')
    hline(g, 20, 12, 27, 'o')
    hline(g, 21, 12, 27, 'o')
    hline(g, 22, 13, 26, 'o')

    # 胸〜前脚のクリーム
    for r, c1, c2 in ((13,17,22),(14,17,22),(15,16,23),(16,16,23),
                      (17,16,23),(18,15,24),(19,15,24),(20,15,24),
                      (21,14,25),(22,14,25)):
        hline(g, r, c1, c2, 'c')
    # 前脚の分かれ目とつま先
    for r in range(17, 23):
        put(g, r, 19, 'nn')
    put(g, 22, 15, 'n'); put(g, 22, 24, 'n')

    # 脇腹の縞
    for r, c in ((14,14),(15,13),(16,13),(17,12),(18,12),
                 (14,25),(15,26),(16,26),(17,27),(18,27)):
        if g[r][c] == 'o':
            g[r][c] = 'd'
    put(g, 19, 13, 'd'); put(g, 19, 26, 'd')

    # 頭
    hline(g, 2, 15, 24, 'o')
    hline(g, 3, 14, 25, 'o')
    for r in range(4, 10):
        hline(g, r, 13, 26, 'o')
    hline(g, 10, 14, 25, 'o')
    hline(g, 11, 15, 24, 'o')

    # 耳＋内側のピンク
    put(g, 0, 14, 'o'); put(g, 0, 25, 'o')
    put(g, 1, 13, 'oo'); put(g, 1, 24, 'oo')
    put(g, 2, 13, 'opo'); put(g, 2, 24, 'opo')
    put(g, 1, 14, 'p'); put(g, 1, 25, 'p')

    # 額の M
    for c in (17, 19, 21):
        put(g, 3, c, 'd')
    for c in (16, 18, 20, 22):
        put(g, 4, c, 'd')

    # 頬の縞
    put(g, 6, 13, 'd'); put(g, 7, 13, 'd')
    put(g, 6, 26, 'd'); put(g, 7, 26, 'd')

    # 目
    if blink:
        put(g, 7, 16, 'kk'); put(g, 7, 22, 'kk')
    else:
        put(g, 6, 16, 'gg'); put(g, 7, 16, 'gg')
        put(g, 6, 22, 'gg'); put(g, 7, 22, 'gg')
        put(g, 6, 17, 'k'); put(g, 7, 17, 'k')
        put(g, 6, 22, 'k'); put(g, 7, 22, 'k')

    # マズル・鼻・口
    for r, c1, c2 in ((8,16,23),(9,16,23),(10,16,23),(11,16,23)):
        hline(g, r, c1, c2, 'c')
    put(g, 8, 19, 'pp')
    put(g, 9, 18, 'k'); put(g, 9, 21, 'k')

    return outline(g)

# ---------------------------------------------------------------- 就寝（丸まり）
def sleep_frame(exhale=False):
    g = new()
    top = 11 if exhale else 10

    # 胴体の楕円
    rows = [
        (10, 13, 25), (11, 10, 28), (12, 8, 30), (13, 7, 31),
        (14, 6, 32), (15, 6, 32), (16, 6, 32), (17, 6, 32), (18, 6, 32),
        (19, 7, 31), (20, 8, 30), (21, 10, 28), (22, 13, 25),
    ]
    for r, c1, c2 in rows:
        if r < top:
            continue
        if exhale and r == 11:
            c1, c2 = 12, 26
        hline(g, r, c1, c2, 'o')

    # 背の縞（弧）
    for base in (18, 22, 26):
        for i, r in enumerate(range(top + 1, 16)):
            put(g, r, base + (1 if i > 2 else 0), 'd')
    put(g, 12, 29, 'd'); put(g, 13, 30, 'd'); put(g, 14, 30, 'd')

    # 腹のクリーム
    hline(g, 19, 9, 29, 'c')
    hline(g, 20, 9, 29, 'c')
    hline(g, 21, 11, 27, 'c')
    hline(g, 22, 14, 24, 'c')

    # 頭（左）
    for r, c1, c2 in ((11,8,14),(12,7,15),(13,6,15),(14,6,16),
                      (15,6,16),(16,6,16),(17,6,16),(18,7,15),(19,8,14)):
        hline(g, r, c1, c2, 'o')
    # 頭と胴の境の陰
    put(g, 12, 15, 's'); put(g, 13, 16, 's'); put(g, 14, 16, 's'); put(g, 15, 16, 's')

    # 耳
    put(g, 9, 8, 'o')
    put(g, 10, 7, 'opo')

    # 閉じた目・鼻・頬
    hline(g, 16, 8, 13, 'c')
    hline(g, 17, 8, 13, 'c')
    put(g, 15, 8, 'kk'); put(g, 15, 13, 'kk')
    put(g, 16, 10, 'pp')

    # 尻尾（右から手前をぐるり、先はクリーム）
    put(g, 15, 31, 'oo')
    put(g, 16, 31, 'do')
    put(g, 17, 31, 'do')
    put(g, 18, 30, 'oo')
    put(g, 19, 29, 'oo')
    hline(g, 20, 16, 29, 'o')
    hline(g, 21, 14, 28, 'o')
    put(g, 20, 20, 'dd'); put(g, 20, 25, 'dd')
    put(g, 21, 18, 'dd'); put(g, 21, 23, 'dd')
    put(g, 21, 14, 'cc'); put(g, 20, 16, 'cc')

    return outline(g)

# ---------------------------------------------------------------- 出力
def to_rows(g):
    return [''.join(r) for r in g]

sprites = {
    'walk': [to_rows(walk_frame(i)) for i in range(4)],
    'sit': [to_rows(sit_frame(False)), to_rows(sit_frame(True))],
    'sleep': [to_rows(sleep_frame(False)), to_rows(sleep_frame(True))],
}

# 行長の検証
for name, frames in sprites.items():
    for i, f in enumerate(frames):
        assert len(f) == H, (name, i, len(f))
        for r in f:
            assert len(r) == W, (name, i, r)

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'sprites.json'), 'w') as fp:  # cat-pixel.js の FRAMES に手で反映する
    json.dump({'palette': PALETTE, 'W': W, 'H': H, 'sprites': sprites}, fp)

# ASCII プレビュー
def show(name, rows):
    print('---', name, '-' * 30)
    for r in rows:
        print(r.replace('.', ' '))

show('walk f0', sprites['walk'][0])
show('sit', sprites['sit'][0])
show('sleep', sprites['sleep'][0])

# 拡大プレビュー HTML
cells = []
for name, frames in sprites.items():
    for i, f in enumerate(frames):
        cells.append((f'{name}[{i}]', f))
html = ['<!DOCTYPE html><meta charset="utf-8"><body style="background:#0b0f14;display:flex;flex-wrap:wrap;gap:14px;padding:14px;font:12px monospace;color:#889">']
for label, f in cells:
    html.append(f'<div><div>{label}</div><canvas data-rows=\'{json.dumps(f)}\' width="{W*8}" height="{H*8}" style="image-rendering:pixelated;background:#11161d;border:1px solid #333"></canvas></div>')
html.append('<script>const PAL=' + json.dumps(PALETTE) + ';')
html.append('''document.querySelectorAll('canvas').forEach(cv=>{const rows=JSON.parse(cv.dataset.rows);const x=cv.getContext('2d');rows.forEach((row,r)=>{for(let c=0;c<row.length;c++){const col=PAL[row[c]];if(!col)continue;x.fillStyle=col;x.fillRect(c*8,r*8,8,8);}});});</script>''')
with open(os.path.join(here, 'preview.html'), 'w') as fp:
    fp.write('\n'.join(html))
print('written: sprites.json / preview.html')
