# 入力の種類ごとの取り込み方

| 入力 | 経路 | 注意 |
|---|---|---|
| CSV / TSV | `draft.py data.csv --name x` | 文字コードは UTF-8（BOM 付きも可）。Excel の CSV が Shift_JIS なら、先に `iconv -f SHIFT_JIS -t UTF-8` で変換する |
| Excel (.xlsx) | `draft.py book.xlsx --sheet 集計 --name x` | 表示されている値（キャッシュされた値）と結合セル、太字を読む。式そのものは読まない。書式（%、通貨、桁区切り）は再現されないので、依頼表に「表示形式」の行を立てて揃える |
| Markdown | `draft.py notes.md --name x` | 最初のパイプ表だけを読む |
| HTML | `draft.py page.html --name x` | 最初の `<table>`。`rowspan` / `colspan` と `<th>`（太字扱い）を読む |
| PDF（文字が埋め込まれた表） | `draft.py paper.pdf --page 3 --crop X,Y,W,H --name x` | 単語の位置から行と列を推定する。`--crop` は pt 単位で、左上が原点。範囲は `pdftotext -bbox -f 3 -l 3 paper.pdf -` の出力か、ページ画像から読む。キャプションや脚注が混ざったら、下書きから消す |
| 画像（スクショ、写真、スキャン） | `grid.py` で cm の格子を重ねて読み、`draft.py --rows R --cols C --name x` で空の骨組みを作ってセルを打ち込む | 罫線の位置は `measure.py --row Y`（縦線）/ `--col X`（横線）で測ると、列幅の比が分かる |
| Word / PowerPoint の表 | 文字が取れるなら HTML か PDF に書き出して上の経路へ。無理ならスクショで画像の経路 | 結合セルは書き出した HTML の方が正確 |
| 手書きの表 | 画像の経路。`grid.py --clean` | 読めない字は推測で埋めない。「?」のまま残し、最後に確認する |

## 下書きのあとに必ずすること

1. **cells.json を確かめる**：中身が元の表と合っているかを見る。build.py は、これにあるセルがすべて出力にあるかを調べる。依頼で中身を変えるとき（並べ替え、単位の書き換え）は、cells.json も直すか、依頼表に「内容を変えた」と書く。
2. **見出しの行数を確かめる**：`--header-rows` の値が合っていないと、太字と三線の位置がずれる。
3. **数値の列を確かめる**：`S` 列になったかどうかを確認する。数値に見えても ID や年（2024）のように揃えるべきでない列は、`l` か `c` に戻す。
