# tabularray（tblr）の書き方の要点

公式マニュアル：`texdoc tabularray`。ここには表を起こすときによく使うものだけを書く。

## 骨組み

```latex
\begin{tblr}{
  colspec = {l X[l] S[table-format=3.1] Q[r]},   % 列の型
  width = \linewidth,                             % X 列があるときの全体幅
  hline{1,Z} = {0.08em}, hline{2} = {0.05em},     % 三線表（Z は最後）
  row{1} = {font=\bfseries, c},                   % 見出し行
  rowsep = 2pt, colsep = 6pt,
}
  見出し & 見出し & {{{数値}}} & 値 \\
  a & b & 12.5 & 3 \\
\end{tblr}
```

- **区切り**：セルは `&`、行の終わりは `\\`。最後の行の `\\` はあってもなくてもよい。
- **キーの書き方**：`{...}` の中に `キー = 値` をコンマで並べる（inner spec）。キャプションなど表の外側の設定は `[...]` に書く（outer spec、`longtblr` / `talltblr` で使う）。

## 列の型

| 型 | 意味 |
|---|---|
| `l` `c` `r` | 左・中央・右揃え。幅は中身に合わせる |
| `Q[l, wd=3cm]` | 幅を指定した列。`Q[r]`、`Q[c, m]`（縦も中央）など |
| `X[l]` `X[2, l]` | 残りの幅を分け合う列。`width=` と一緒に使う。数字は配分の比 |
| `S[table-format=3.2]` | 小数点揃え（`\UseTblrLibrary{siunitx}`）。整数部 3 桁、小数部 2 桁。負の数がある列は `-3.2` |

## 行・列・セルの指定

- `row{1} = {...}` `row{2-4}` `row{even}` `row{Z}`（最後）、`column{2} = {...}`、`cell{2}{3} = {...}`
- 主なキー：
  - 揃え：`halign=l|c|r`、`valign=m|t|b`
  - 書体：`font=\bfseries`
  - 色：`fg=`、`bg=`
  - 中身の前後：`preto=`、`appto=`
  - 計算：`cmd=`

## 結合

```latex
\SetCell[r=2]{c} 学年 & \SetCell[c=2]{c} 得点 & \\     % 横に 2 つ結合しても、隠れる位置の & は残す
                     & 数学 & 物理 \\
```

- 結合で隠れた位置も、空のセルとして `&` を書く。数が合わないと列がずれる。build.py は各行のセル数を数えて警告する。
- 部分的な横罫は `\cline{2-3}` ではなく、`hline{3} = {2-3}{0.05em}`。booktabs ライブラリがあれば `\cmidrule{2-3}` も使える。

## 罫線

- 横罫：`hline{1,Z} = {0.08em}`。番号は行の上の線（`Z` は最後の行の下）。
- 縦罫：`vline{2-Y} = {...}`（`Y` は最後の列の右）。
- 書式：`dashed`、`fg=gray`、`leftpos=...`。
- booktabs の命令を使うときは `\UseTblrLibrary{booktabs}` を書き、行の前に `\toprule` `\midrule` `\bottomrule` を置く。

## 数値（siunitx ライブラリ）

- 数値でないセルは `{{{...}}}` で包む。見出し、`—`、`n/a` など。包まないと siunitx がエラーを出す。
- 桁区切りのカンマは入力から外す。表示に区切りが要るなら `\sisetup{group-separator={,}, group-minimum-digits=4}`。
- 単位は `\unit{g/cm^3}`、数と単位は `\qty{9.8}{m/s^2}`。

## 大きな表

- **幅が本文幅を超える**：`width=\linewidth` と `X` 列にする。それでも足りなければ `cells={font=\small}` で文字を小さくする。`\resizebox` は文字が本文と揃わなくなるので最後の手段。
- **ページをまたぐ**：`longtblr` を使う。

  ```latex
  \begin{longtblr}[caption={金属の性質}, label={tab:metals}]{
    colspec={l S[table-format=1.2]}, rowhead=1, hline{1,Z}={0.08em}, hline{2}={0.05em},
  }
  ```

  `rowhead=1` で見出しを各ページに繰り返す。キャプションと表番号は `[...]` に書く（table 環境で包まない）。
- **横長**：`rotating` の `sidewaystable` で包む。tblr は縦組みに対応していない。

## 色

`bg=gray9` のような ninecolors の名前は `\usepackage{ninecolors}` が要る。xcolor の混色（`teal!10`、`black!6`）なら追加のパッケージは要らない。白黒印刷を想定するときは濃淡だけで区別する。
