#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""参照イラスト（茶トラ猫・複数ポーズ）から高解像度ドット絵スプライトを生成する。

パイプライン:
  1. 各ポーズをクロップ → 背景(白)を除去し最大連結成分をマスク化
  2. マスク加重ボックス平均で縮小 → 毛色ランプへ量子化（redmean 距離）
  3. 顔・耳・肉球などをタッチアップ（座標指定）
  4. 歩行: 脚をシアー変形して4相サイクル / お座り: まばたき / 就寝(仰向け): 呼吸
  5. 1px の輪郭を付けて 88x56 キャンバスへ配置し assets/js/cat-sprites.js を出力

usage:
  python3 tools/build_cat_sprites.py <参照画像.jpeg> [--preview DIR] [--cache DIR]

参照画像はリポジトリに含めない（ローカルのみ）。
"""
import argparse
import json
import os
from collections import deque

import numpy as np
from PIL import Image, ImageDraw

# ---------------------------------------------------------------- 設定
CANVAS_W, CANVAS_H = 88, 56
SIT_TARGET_H = 54          # sit のコンテンツ高さ（+輪郭2 = 56）
COVERAGE = 0.42            # セルを不透明にするマスク被覆率
W_LUMINANCE = 236          # これ以上の輝度は 'W'（ほぼ白）へ

# 参照画像 (1024x1024) 内の各ポーズ
CROPS = {
    'walk':  (60, 20, 1000, 440),     # 上段: 歩行（右向き）
    'sit':   (30, 440, 370, 1000),    # 左下: お座り正面
    'belly': (650, 420, 1010, 1010),  # 右下: 仰向け → 90°回転して就寝ポーズに
}

PALETTE = {
    'W': '#fdf4dd',  # ほぼ白のクリーム（胸・マズルのハイライト）
    'c': '#f8e3b6',  # クリーム
    'n': '#eccf96',  # クリームの陰
    'h': '#f6c97f',  # 明るい毛
    'o': '#efb264',  # 地の毛
    'm': '#e39a4e',  # 中間の毛
    'd': '#d1813a',  # 縞
    's': '#b5682c',  # 濃い縞
    'r': '#96521f',  # 最暗の毛
    'g': '#8ca34f',  # 瞳の緑
    'k': '#2b1c10',  # 目・鼻・口の線
    'p': '#eab19b',  # 鼻・耳内・肉球のピンク
    'b': '#6d4213',  # 輪郭
}
FUR = ['c', 'n', 'h', 'o', 'm', 'd', 's', 'r']  # 自動マッピング対象（アクセント色は手作業）

# タッチアップ: (row, col, char) — 量子化後のコンテンツ座標系
TOUCHUP = {
    'walk': [
        # 耳の内側のピンク
        (2, 77, 'p'), (3, 77, 'p'), (3, 78, 'p'), (4, 78, 'p'),
        # 目（黒縁 + 緑の瞳）
        (9, 80, 'k'), (9, 81, 'k'), (9, 82, 'k'),
        (10, 80, 'k'), (10, 81, 'g'), (10, 82, 'k'),
        # 鼻と口元
        (12, 83, 'p'), (12, 84, 'p'), (13, 83, 'k'),
        (13, 81, 'W'), (14, 81, 'W'), (14, 82, 'W'),
    ],
    'sit': [
        # 耳の内側
        (2, 5, 'p'), (3, 5, 'p'), (3, 6, 'p'),
        (2, 16, 'p'), (3, 15, 'p'), (3, 16, 'p'),
        # 左目（緑の虹彩 + 瞳孔）
        (9, 6, 'g'), (9, 7, 'g'), (9, 8, 'g'),
        (10, 6, 'g'), (10, 7, 'k'), (10, 8, 'g'),
        # 右目
        (9, 13, 'g'), (9, 14, 'g'), (9, 15, 'g'),
        (10, 13, 'g'), (10, 14, 'k'), (10, 15, 'g'),
        # 眉間を明るく（縞の塊が眉のように見えるのを防ぐ）
        (9, 10, 'h'), (9, 11, 'h'), (10, 10, 'c'), (10, 11, 'c'),
        # 鼻と口
        (11, 10, 'p'), (11, 11, 'p'), (12, 10, 'k'), (12, 11, 'k'),
    ],
    'belly': [
        # 就寝ポーズ: 閉じた目（回転後は縦線になる）
        (4, 46, 'k'), (5, 46, 'k'),
        (8, 47, 'k'), (9, 47, 'k'),
        # 鼻
        (6, 49, 'p'), (7, 49, 'p'),
        # 耳の内側（上の耳と右の耳）
        (1, 43, 'p'), (2, 44, 'p'), (7, 51, 'p'), (8, 52, 'p'),
        # 上に向いた後ろ足の肉球
        (4, 17, 'p'), (4, 18, 'p'), (14, 21, 'p'), (15, 21, 'p'),
    ],
}

# sit のまばたきフレーム: 目の領域を上書き
SIT_BLINK = [
    (9, 6, 'o'), (9, 7, 'o'), (9, 8, 'o'),
    (10, 6, 'k'), (10, 7, 'k'), (10, 8, 'k'),
    (9, 13, 'o'), (9, 14, 'o'), (9, 15, 'o'),
    (10, 13, 'k'), (10, 14, 'k'), (10, 15, 'k'),
]

# 歩行の脚: (col1, col2, pivot_row) — pivot 以下をシアー
LEGS = {
    'hindTrail':  (18, 27, 26),   # 後ろへ蹴っている後脚
    'hindPlant':  (28, 47, 28),   # 体の下で接地している後脚
    'frontPlant': (52, 63, 25),   # 垂直に接地している前脚
    'frontFwd':   (64, 84, 24),   # 前へ伸ばした前脚
}
CONTENT_BOTTOM = 39  # walk コンテンツの最下行

# フレームごとの足元シフト量（+ = 前方/右）と持ち上げる脚
WALK_CYCLE = [
    {'shift': {'hindTrail': 0,  'hindPlant': 0,  'frontPlant': 0,  'frontFwd': 0},
     'lift': [], 'bob': 0},
    {'shift': {'hindTrail': 3,  'hindPlant': -2, 'frontPlant': 2,  'frontFwd': -3},
     'lift': ['hindTrail', 'frontFwd'], 'bob': 1},
    {'shift': {'hindTrail': 6,  'hindPlant': -4, 'frontPlant': 4,  'frontFwd': -6},
     'lift': [], 'bob': 0},
    {'shift': {'hindTrail': 3,  'hindPlant': -2, 'frontPlant': 2,  'frontFwd': -3},
     'lift': ['hindPlant', 'frontPlant'], 'bob': 1},
]
LIFT_DY = 2


# ---------------------------------------------------------------- マスク
def build_mask(rgb):
    """背景(ほぼ白)を除去し、最大連結成分を穴埋めして返す。1/2解像度で処理。"""
    mx = rgb.max(axis=-1)
    mn = rgb.min(axis=-1)
    mask = ~((mn > 225) & ((mx - mn) < 22))
    small = mask[::2, ::2]
    comp = _largest_component(small)
    comp = _fill_holes(comp)
    full = np.repeat(np.repeat(comp, 2, axis=0), 2, axis=1)
    return full[:mask.shape[0], :mask.shape[1]]


def _largest_component(mask):
    h, w = mask.shape
    seen = np.zeros_like(mask, dtype=bool)
    best = []
    for sy in range(h):
        for sx in range(w):
            if mask[sy, sx] and not seen[sy, sx]:
                q = deque([(sy, sx)])
                seen[sy, sx] = True
                comp = [(sy, sx)]
                while q:
                    y, x = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not seen[yy, xx]:
                            seen[yy, xx] = True
                            q.append((yy, xx))
                            comp.append((yy, xx))
                if len(comp) > len(best):
                    best = comp
    out = np.zeros_like(mask)
    ys, xs = zip(*best)
    out[list(ys), list(xs)] = True
    return out


def _fill_holes(mask):
    h, w = mask.shape
    bg = ~mask
    outside = np.zeros_like(mask)
    q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if bg[y, x] and not outside[y, x]:
                outside[y, x] = True
                q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if bg[y, x] and not outside[y, x]:
                outside[y, x] = True
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and bg[yy, xx] and not outside[yy, xx]:
                outside[yy, xx] = True
                q.append((yy, xx))
    return mask | (bg & ~outside)


# ---------------------------------------------------------------- 量子化
def _hex2rgb(hx):
    return np.array([int(hx[i:i + 2], 16) for i in (1, 3, 5)], dtype=np.float32)


_FUR_COLS = None


def _nearest_fur(px):
    global _FUR_COLS
    if _FUR_COLS is None:
        _FUR_COLS = np.stack([_hex2rgb(PALETTE[k]) for k in FUR])
    d = px[None, :] - _FUR_COLS
    rbar = (px[0] + _FUR_COLS[:, 0]) / 2
    dist = ((2 + rbar / 256) * d[:, 0] ** 2 + 4 * d[:, 1] ** 2
            + (2 + (255 - rbar) / 256) * d[:, 2] ** 2)
    return FUR[int(np.argmin(dist))]


def cellize(rgb, mask, tw, th):
    sh, sw = mask.shape
    grid = [[None] * tw for _ in range(th)]
    ys = np.linspace(0, sh, th + 1)
    xs = np.linspace(0, sw, tw + 1)
    for r in range(th):
        for c in range(tw):
            y1, y2 = int(ys[r]), max(int(ys[r]) + 1, int(ys[r + 1]))
            x1, x2 = int(xs[c]), max(int(xs[c]) + 1, int(xs[c + 1]))
            m = mask[y1:y2, x1:x2]
            if m.mean() < COVERAGE:
                continue
            # 平均ではなく40パーセンタイル採色で、細い縞・暗部を潰さず残す
            px = np.percentile(rgb[y1:y2, x1:x2][m], 40, axis=0)
            lum = 0.299 * px[0] + 0.587 * px[1] + 0.114 * px[2]
            grid[r][c] = 'W' if lum > W_LUMINANCE else _nearest_fur(px)
    return grid


def despeckle(grid):
    th, tw = len(grid), len(grid[0])
    res = [row[:] for row in grid]
    for r in range(th):
        for c in range(tw):
            v = grid[r][c]
            if v is None:
                continue
            nb = [grid[r + dr][c + dc] for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= r + dr < th and 0 <= c + dc < tw and grid[r + dr][c + dc] is not None]
            if len(nb) >= 3 and v not in nb and len(set(nb)) == 1:
                res[r][c] = nb[0]
    return res


# ---------------------------------------------------------------- 変形
def apply_touchup(grid, edits):
    res = [row[:] for row in grid]
    for r, c, ch in edits:
        if 0 <= r < len(res) and 0 <= c < len(res[0]):
            res[r][c] = ch
    return res


def shear_leg(grid, c1, c2, pivot, shift):
    """pivot 行以下・列 c1..c2 の画素を、行が下がるほど大きく水平シフトする。"""
    if shift == 0:
        return grid
    th, tw = len(grid), len(grid[0])
    res = [row[:] for row in grid]
    span = max(1, CONTENT_BOTTOM - pivot)
    moved = []
    for r in range(pivot, th):
        for c in range(c1, min(c2 + 1, tw)):
            if grid[r][c] is not None:
                off = round(shift * (r - pivot) / span)
                moved.append((r, c, off, grid[r][c]))
                res[r][c] = None
    for r, c, off, ch in moved:
        cc = c + off
        if 0 <= cc < tw:
            res[r][cc] = ch
    return res


def lift_leg(grid, c1, c2, pivot, dy, max_shift=6):
    """脚の画素列を dy 行だけ上へ詰める（足が浮く）。シアー後の位置も含める。"""
    th, tw = len(grid), len(grid[0])
    res = [row[:] for row in grid]
    lo = max(0, c1 - max_shift)
    hi = min(tw - 1, c2 + max_shift)
    for c in range(lo, hi + 1):
        col = [res[r][c] for r in range(pivot, th)]
        if not any(v is not None for v in col):
            continue
        col = col[dy:] + [None] * dy
        for i, v in enumerate(col):
            res[pivot + i][c] = v
    return res


def bob_up(grid, dy):
    if dy == 0:
        return grid
    th = len(grid)
    tw = len(grid[0])
    return [grid[r + dy][:] if r + dy < th else [None] * tw for r in range(th)]


def breathe(grid):
    """仰向けの呼吸: 腹の上側の輪郭ぎわを 1px 持ち上げる。"""
    th, tw = len(grid), len(grid[0])
    res = [row[:] for row in grid]
    for c in range(24, min(40, tw)):
        for r in range(th):
            if grid[r][c] is not None:
                if r > 0 and res[r - 1][c] is None:
                    res[r - 1][c] = grid[r][c]
                break
    return res


def outline(grid):
    th, tw = len(grid), len(grid[0])
    out = [[None] * (tw + 2) for _ in range(th + 2)]
    for r in range(th):
        for c in range(tw):
            out[r + 1][c + 1] = grid[r][c]
    res = [row[:] for row in out]
    for r in range(th + 2):
        for c in range(tw + 2):
            if out[r][c] is None:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < th + 2 and 0 <= cc < tw + 2 and out[rr][cc] not in (None, 'b'):
                        res[r][c] = 'b'
                        break
    return res


def place_on_canvas(grid):
    """輪郭付きグリッドをキャンバス下端・水平中央に配置して文字列化。"""
    th, tw = len(grid), len(grid[0])
    top = CANVAS_H - th
    left = (CANVAS_W - tw) // 2
    rows = []
    for r in range(CANVAS_H):
        line = ['.'] * CANVAS_W
        if r >= top:
            src = grid[r - top]
            for c in range(tw):
                if src[c] is not None and 0 <= left + c < CANVAS_W:
                    line[left + c] = src[c]
        rows.append(''.join(line))
    return rows


# ---------------------------------------------------------------- 出力
def emit_js(frames, path):
    lines = [
        '/* 自動生成: tools/build_cat_sprites.py（参照イラストから量子化）。手編集しない */',
        'window.PIXCAT_DATA = {',
        f'  cols: {CANVAS_W}, rows: {CANVAS_H},',
        '  palette: ' + json.dumps(
            {'.': None, **{k: v for k, v in PALETTE.items()}}, ensure_ascii=False) + ',',
        '  frames: {',
    ]
    for name, fs in frames.items():
        lines.append(f'    {name}: [')
        for f in fs:
            lines.append('      [')
            for row in f:
                lines.append(f"        '{row}',")
            lines.append('      ],')
        lines.append('    ],')
    lines += ['  }', '};', '']
    with open(path, 'w') as fp:
        fp.write('\n'.join(lines))


def save_preview(frames, path, zoom=6):
    total_w = sum(CANVAS_W + 2 for fs in frames.values() for _ in fs) + 2
    img = Image.new('RGB', (total_w * zoom, (CANVAS_H + 4) * zoom), (17, 22, 29))
    dr = ImageDraw.Draw(img)
    ox = 2
    for name, fs in frames.items():
        for i, f in enumerate(fs):
            dr.text((ox * zoom, 2), f'{name}[{i}]', fill=(140, 150, 170))
            for r, row in enumerate(f):
                for c, ch in enumerate(row):
                    if ch == '.':
                        continue
                    col = tuple(int(PALETTE[ch][j:j + 2], 16) for j in (1, 3, 5))
                    dr.rectangle([(ox + c) * zoom, (r + 2) * zoom,
                                  (ox + c + 1) * zoom - 1, (r + 3) * zoom - 1], fill=col)
            ox += CANVAS_W + 2
    img.save(path)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('source', help='参照画像 (1024x1024 の茶トラ4ポーズ)')
    ap.add_argument('--preview', help='プレビュー PNG の出力先ディレクトリ')
    ap.add_argument('--cache', help='マスクの npy キャッシュディレクトリ')
    args = ap.parse_args()

    im = np.asarray(Image.open(args.source).convert('RGB'), dtype=np.float32)

    # 各ポーズのマスクとコンテンツ bbox
    masks, bboxes = {}, {}
    for name, (x1, y1, x2, y2) in CROPS.items():
        cached = os.path.join(args.cache, f'mask_{name}.npy') if args.cache else None
        if cached and os.path.exists(cached):
            m = np.load(cached)
        else:
            m = build_mask(im[y1:y2, x1:x2])
            if cached:
                np.save(cached, m)
        ys, xs = np.where(m)
        masks[name] = m
        bboxes[name] = (xs.min(), ys.min(), xs.max(), ys.max())

    scale = SIT_TARGET_H / (bboxes['sit'][3] - bboxes['sit'][1] + 1)

    base = {}
    for name, (x1, y1, x2, y2) in CROPS.items():
        bx1, by1, bx2, by2 = bboxes[name]
        rgb = im[y1:y2, x1:x2][by1:by2 + 1, bx1:bx2 + 1]
        m = masks[name][by1:by2 + 1, bx1:bx2 + 1]
        if name == 'belly':  # 90°時計回り: 頭が右
            rgb = np.rot90(rgb, k=-1).copy()
            m = np.rot90(m, k=-1).copy()
        th = max(1, round(m.shape[0] * scale))
        tw = max(1, round(m.shape[1] * scale))
        g = despeckle(cellize(rgb, m, tw, th))
        base[name] = apply_touchup(g, TOUCHUP[name])
        print(f'{name}: {tw}x{th} cells')

    # 歩行 4 フレーム
    walk_frames = []
    for spec in WALK_CYCLE:
        g = base['walk']
        for leg, (c1, c2, pivot) in LEGS.items():
            g = shear_leg(g, c1, c2, pivot, spec['shift'][leg])
        for leg in spec['lift']:
            c1, c2, pivot = LEGS[leg]
            g = lift_leg(g, c1, c2, pivot, LIFT_DY)
        g = bob_up(g, spec['bob'])
        walk_frames.append(place_on_canvas(outline(g)))

    # お座り 2 フレーム（開眼 / まばたき）
    sit_open = base['sit']
    sit_blink = apply_touchup(sit_open, SIT_BLINK)
    sit_frames = [place_on_canvas(outline(sit_open)), place_on_canvas(outline(sit_blink))]

    # 就寝 2 フレーム（呼吸）
    sleep_a = base['belly']
    sleep_b = breathe(sleep_a)
    sleep_frames = [place_on_canvas(outline(sleep_a)), place_on_canvas(outline(sleep_b))]

    frames = {'walk': walk_frames, 'sit': sit_frames, 'sleep': sleep_frames}

    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(here, '..', 'assets', 'js', 'cat-sprites.js'))
    emit_js(frames, out)
    print('written:', out)

    if args.preview:
        os.makedirs(args.preview, exist_ok=True)
        save_preview({'walk': frames['walk']}, os.path.join(args.preview, 'sheet_walk.png'))
        save_preview({'sit': frames['sit'], 'sleep': frames['sleep']},
                     os.path.join(args.preview, 'sheet_sit_sleep.png'))
        print('preview:', args.preview)


if __name__ == '__main__':
    main()
