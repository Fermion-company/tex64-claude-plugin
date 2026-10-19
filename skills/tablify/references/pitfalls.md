# よくあるエラーと落とし穴

## コンパイルエラー

| メッセージ | 原因 | 直し方 |
|---|---|---|
| `Environment tblr undefined` | `tabularray` が読み込まれていない | `.preamble.tex` に `\usepackage{tabularray}`。build.py は無ければ自動で足す |
| `Undefined control sequence \UseTblrLibrary` | `\UseTblrLibrary` が `\usepackage{tabularray}` より前にある | 順番を入れ替える。build.py と insert.py は自動で後ろに回す |
| `Invalid number` や `siunitx error: "invalid-number"` | `S` 列に数値でないセルがある（見出し、`—`、`n/a`） | そのセルを `{{{...}}}` で包む |
| `Misplaced alignment tab character &` | セルの中身の `&`（社名の A&B など） | `\&` にする。draft.py はエスケープ済み |
| 列が右にずれる、行が短い | 結合で隠れた位置の `&` を書き忘れた | 隠れた位置も空のセルとして `&` を書く。build.py が行ごとのセル数を警告する |
| `Package xcolor Error: Undefined color` | `bg=gray9` などの ninecolors の色名 | `\usepackage{ninecolors}` を足すか、`black!6` のような混色にする |
| `Dimension too large` / 表がページからはみ出す | `X` 列なのに `width=` がない、または幅が大きすぎる | `width=\linewidth` を付ける。列の比を `X[2]` などで調整する |
| `Missing character: There is no あ` | pdfLaTeX で和文 | 文書側を LuaLaTeX（luatexja）か upLaTeX にする。build.py は和文があると luatexja を読む |
| 脚注 `\footnote` が出ない | tblr のセルの中の脚注 | `talltblr` の `note{a} = {...}` と、セルの中の `\TblrNote{a}` を使う |
| verbatim / `\verb` でエラー | tblr のセルは引数として読まれる | `\texttt` にする。どうしても必要なら `cell{i}{j}={cmd=...}` を使う |

## 見た目の落とし穴

- **縦罫**：日本の論文や教科書では縦罫を使わない三線表が標準。元の表に縦罫があっても、依頼がなければ「元のとおりにするか」を確認するより、元に合わせておいて報告で触れる。依頼があれば依頼に従う。
- **数値の揃え**：桁数の違う数を中央揃えにすると読みにくい。数値の列は `S` 列（小数点揃え）か右揃えにする。
- **見出しの改行**：長い見出しは `\SetCell{c} 密度\\(g/cm³)` ではなく、`{密度\\(g/cm³)}` と波括弧で包んで改行する。
- **元の表の太さ**：スクショの罫線の太さはそのまま写さない。三線表なら上下 0.08em、中 0.05em を基準にする。
- **色**：元の表の背景色は、印刷で潰れない濃さ（10% 前後）に抑える。色の依頼がなければ、色を使わない表を提案してもよい。報告で触れる。
