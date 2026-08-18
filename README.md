# tomokazu-rikioka.github.io

Rick（データサイエンティスト）のプロフィールサイト。
X / LinkedIn / Zenn / GitHub / Kaggle へのリンクを 1 枚にまとめたもの。

公開先: <https://tomokazu-rikioka.github.io/>

## 構成

```
index.html              トップページ（ターミナル窓のレイアウト）
404.html                存在しないページ用
assets/
  css/style.css         全スタイル（配色は :root の CSS 変数に集約）
  js/cat-pixel.js       ドット絵のチャトラ（歩行・お座り・就寝・クリック追従）
  js/visitors.js        訪問者カウンター
  img/                  アイコン・ファビコン・OGP 画像
robots.txt / sitemap.xml
```

ビルド不要の静的サイト。ローカルで見るには:

```sh
python3 -m http.server 4173
# → http://localhost:4173/
```

## 猫について

`assets/js/cat-pixel.js` が 22×14 のドットを canvas に描いて動かしている。

- 歩く／立ち止まる を自動で切り替える
- 画面の余白をクリックすると、その位置まで歩いてくる（遠いと走る）
- 猫をクリックすると跳ねて鳴く
- 45 秒操作がないと丸くなって寝る（何か操作すると起きる）
- `prefers-reduced-motion: reduce` の環境では動かず、お座りのまま

ドット絵は `BODY` / `LEGS` / `SIT` / `SLEEP` の文字グリッドで定義してある。
1 文字が 1 ドットで、`PALETTE` の記号（`o` 地の毛 / `d` 縞 / `c` クリーム / `g` 瞳 / `p` 鼻 / `k` 目・輪郭 / `.` 透明）に対応する。
**各行は必ず 22 文字**にすること（ずれると絵が崩れる）。

## 訪問者カウンター

静的サイトなのでカウント自体は外部の無料 API に置いている。

- エンドポイント: `https://abacus.jasoncameron.dev/hit/tomokazu-rikioka-github-io/visits-live`
- 初回訪問時に採番した番号を `localStorage` に保存し、次回以降はその番号を表示する（リロードで増えない）
- API が落ちている場合はカウンターのブロックごと非表示になる（ページ自体は壊れない）

数え直したい場合は `assets/js/visitors.js` の `ENDPOINT` の末尾（キー名）を別の文字列に変えると 1 から始まる。

## 更新するとき

- リンクやプロフィール文言 … `index.html`
- 配色 … `assets/css/style.css` 冒頭の `:root`
- アイコン … `assets/img/` を差し替え（`sips` でリサイズ可能）
