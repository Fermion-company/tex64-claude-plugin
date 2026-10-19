#!/usr/bin/env python3
"""Turn a table source into a first tabularray draft plus the cell data it came from.

Input (picked by extension)
  .csv .tsv           plain cells
  .xlsx               first sheet (or --sheet NAME): cached values with common decimal/percent display formats,
                      merged cells, bold fonts (--range A1:H9 supported)
  .md .markdown       the first pipe table
  .html .htm          the first <table> (rowspan / colspan kept)
  .pdf                words of one page (--page N, optional --crop X,Y,W,H in pt
                      from the top-left) grouped into rows and columns
  (none)              --rows R --cols C writes an empty skeleton to fill in by hand
                      (images: read them with grid.py and type the cells)

Output (next to --out, default: ./NAME.*)
  NAME.tblr           one tblr environment, nothing else
  NAME.preamble.tex   \\usepackage{tabularray} and the \\UseTblrLibrary lines it needs
  NAME.cells.json     the cells as read from the source -- build.py checks the
                      typeset table against it, so keep it unless the content changes
                      on purpose (then edit it, or delete it to skip the check)

The draft is a starting point.  It uses the three-rule (booktabs-like) style,
bolds the header row, and gives columns that are mostly numbers a siunitx S
column aligned on the decimal point.  Everything the user asked for (see
references/requests.md) is applied by editing NAME.tblr afterwards.

Usage
  draft.py SOURCE --name NAME [--out DIR] [--sheet NAME] [--range A1:H9] [--page N] [--crop X,Y,W,H]
           [--header-rows 1] [--no-numeric] [--force]
  draft.py --rows R --cols C --name NAME [--out DIR]

All text read from the source is TeX-escaped: nothing from a file reaches TeX as code.
"""
import argparse
import csv
from decimal import Decimal, ROUND_HALF_UP
import html.parser
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check_name, floats, read_text, run, tex_escape, write_text  # noqa: E402

NUM = re.compile(r"^[+\-−]?(\d{1,3}(,\d{3})+|\d+)?(\.\d+)?$")


# ---------------------------------------------------------------- grid model
# A grid is a list of rows; each row is a list of cells.  A cell is a dict
# {"text": str, "r": rowspan, "c": colspan, "bold": bool} or None when it is
# covered by a span from another cell.

def make_grid(rows, cols):
    return [[{"text": "", "r": 1, "c": 1, "bold": False} for _ in range(cols)] for _ in range(rows)]


def rect_grid(raw_rows):
    """Plain list of string lists -> grid (ragged rows padded)."""
    cols = max((len(r) for r in raw_rows), default=0)
    g = make_grid(len(raw_rows), cols)
    for i, r in enumerate(raw_rows):
        for j, t in enumerate(r):
            g[i][j]["text"] = t.strip()
    return g


def apply_span(g, i, j, r, c):
    g[i][j]["r"], g[i][j]["c"] = r, c
    for di in range(r):
        for dj in range(c):
            if di or dj:
                if i + di < len(g) and j + dj < len(g[0]):
                    g[i + di][j + dj] = None


# ---------------------------------------------------------------- readers
def read_csv(path, delim):
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        return rect_grid(list(csv.reader(f, delimiter=delim)))


def read_md(path):
    rows = []
    for line in read_text(path).splitlines():
        s = line.strip()
        if s.startswith("|"):
            if re.match(r"^\|?\s*:?-{2,}", s.replace(" ", "")):
                continue
            rows.append([c for c in re.split(r"(?<!\\)\|", s.strip("|"))])
        elif rows:
            break
    if not rows:
        sys.exit("error: no pipe table found in " + path)
    return rect_grid(rows)


class _HT(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.cell, self.depth, self.done = [], None, 0, False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.done:
            return
        if tag == "table":
            self.depth += 1
        elif self.depth == 1 and tag == "tr":
            self.rows.append([])
        elif self.depth == 1 and tag in ("td", "th") and self.rows:
            self.cell = {"text": "", "r": int(a.get("rowspan", 1) or 1), "c": int(a.get("colspan", 1) or 1),
                         "bold": tag == "th"}
        elif self.cell is not None and tag in ("b", "strong"):
            self.cell["bold"] = True
        elif self.cell is not None and tag == "br":
            self.cell["text"] += " "

    def handle_endtag(self, tag):
        if self.done:
            return
        if tag in ("td", "th") and self.cell is not None:
            self.rows[-1].append(self.cell)
            self.cell = None
        elif tag == "table":
            self.depth -= 1
            if self.depth == 0:
                self.done = True

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"] += data


def read_html(path):
    p = _HT()
    p.feed(read_text(path))
    if not p.rows:
        sys.exit("error: no <table> found in " + path)
    # place cells, skipping positions covered by earlier rowspans
    occupied, placed = set(), []
    for i, row in enumerate(p.rows):
        j = 0
        for cell in row:
            while (i, j) in occupied:
                j += 1
            placed.append((i, j, cell))
            for di in range(cell["r"]):
                for dj in range(cell["c"]):
                    occupied.add((i + di, j + dj))
            j += cell["c"]
    rows = max(i for i, _ in occupied) + 1
    cols = max(j for _, j in occupied) + 1
    g = make_grid(rows, cols)
    for i, j, cell in placed:
        g[i][j] = {"text": re.sub(r"\s+", " ", cell["text"]).strip(), "r": 1, "c": 1, "bold": cell["bold"]}
        if cell["r"] > 1 or cell["c"] > 1:
            apply_span(g, i, j, cell["r"], cell["c"])
    return g


def _col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group()
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1, int(ref[len(letters):]) - 1


def _xlsx_display(raw, fmt):
    """Common decimal/percent formats only; preserve exact cached values separately."""
    if not raw or fmt in ("General", "@"):
        return raw
    if not re.fullmatch(r"(?:#,##)?0(?:\.0+)?%?", fmt):
        print(f"warning: unsupported Excel format {fmt!r}; verify display against original", file=sys.stderr)
        return raw
    places = len(fmt.rstrip("%").split(".")[1]) if "." in fmt else 0
    value = Decimal(raw) * (100 if fmt.endswith("%") else 1)
    value = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
    return format(value, ("," if "," in fmt else "") + f".{places}f") + ("%" if fmt.endswith("%") else "")


def read_xlsx(path, sheet, cell_range=None):
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = {r.get("Id"): r.get("Target") for r in rels}
        sheets = wb.findall("m:sheets/m:sheet", ns)
        pick = next((s for s in sheets if s.get("name") == sheet), None) if sheet else sheets[0]
        if pick is None:
            sys.exit(f"error: no sheet {sheet!r}; sheets: " + ", ".join(s.get("name") for s in sheets))
        t = target[pick.get("{%s}id" % ns["r"])].lstrip("/")
        ws = ET.fromstring(z.read(t if t.startswith("xl/") else "xl/" + t))
        bold_xf = set()
        formats = {0: "General", 1: "0", 2: "0.00", 3: "#,##0", 4: "#,##0.00", 9: "0%", 10: "0.00%", 49: "@"}
        xf_formats = {0: "General"}
        bounds = None
        if cell_range:
            if not re.fullmatch(r"[A-Z]+[1-9][0-9]*:[A-Z]+[1-9][0-9]*", cell_range):
                sys.exit("error: --range must be an Excel range such as A1:H9")
            a, b = cell_range.split(":")
            (j0, i0), (j1, i1) = _col_index(a), _col_index(b)
            if i1 < i0 or j1 < j0:
                sys.exit("error: --range is reversed")
            bounds = (i0, j0, i1, j1)
        if "xl/styles.xml" in names:
            st = ET.fromstring(z.read("xl/styles.xml"))
            for nf in st.findall("m:numFmts/m:numFmt", ns):
                formats[int(nf.get("numFmtId"))] = nf.get("formatCode")
            fonts = st.findall("m:fonts/m:font", ns)
            bold_font = {k for k, f in enumerate(fonts) if f.find("m:b", ns) is not None}
            for k, xf in enumerate(st.findall("m:cellXfs/m:xf", ns)):
                fmt_id = int(xf.get("numFmtId", 0))
                xf_formats[k] = formats.get(fmt_id, f"unsupported-format-id:{fmt_id}")
                if int(xf.get("fontId", 0)) in bold_font:
                    bold_xf.add(k)
        vals = {}
        for c in ws.iter("{%s}c" % ns["m"]):
            j, i = _col_index(c.get("r"))
            if bounds and not (i0 <= i <= i1 and j0 <= j <= j1):
                continue
            v = c.find("m:v", ns)
            formula = c.find("m:f", ns)
            if c.get("t") == "e":
                sys.exit(f"error: Excel calculation error at {c.get('r')}: {v.text if v is not None else ''}")
            if formula is not None and (v is None or v.text is None):
                sys.exit(f"error: formula cache missing at {c.get('r')}; recalculate, save and reread")
            is_ = c.find("m:is", ns)
            if c.get("t") == "s" and v is not None:
                text = shared[int(v.text)]
            elif c.get("t") == "inlineStr" and is_ is not None:
                text = "".join(x.text or "" for x in is_.iter("{%s}t" % ns["m"]))
            else:
                text = v.text if v is not None else ""
            raw = v.text if v is not None and v.text is not None else ""
            fmt = xf_formats.get(int(c.get("s", 0)), "General")
            if c.get("t", "n") == "n" and raw:
                text = _xlsx_display(raw, fmt)
            if not bounds and not text and formula is None:
                continue  # Styled empty cells are not part of the data range.
            vals[(i, j)] = {"text": text or "", "bold": int(c.get("s", 0)) in bold_xf,
                            "address": c.get("r"), "raw": raw, "format": fmt,
                            "formula": formula.text if formula is not None else None}
        merges = [m.get("ref") for m in ws.findall("m:mergeCells/m:mergeCell", ns)]
    if not vals:
        sys.exit("error: the sheet is empty")
    if not bounds:
        i0 = j0 = 0
        i1, j1 = max(i for i, _ in vals), max(j for _, j in vals)
        for ref in merges:
            (_, _), (mj1, mi1) = [_col_index(x) for x in ref.split(":")]
            i1, j1 = max(i1, mi1), max(j1, mj1)
    g = make_grid(i1 - i0 + 1, j1 - j0 + 1)
    for (i, j), value in vals.items():
        g[i-i0][j-j0].update(value)
    for ref in merges:
        (mj0, mi0), (mj1, mi1) = [_col_index(x) for x in ref.split(":")]
        if mi1 < i0 or mi0 > i1 or mj1 < j0 or mj0 > j1:
            continue
        if not (i0 <= mi0 <= mi1 <= i1 and j0 <= mj0 <= mj1 <= j1):
            sys.exit(f"error: --range cuts merged cells {ref}")
        apply_span(g, mi0-i0, mj0-j0, mi1-mi0+1, mj1-mj0+1)
    return g


def read_pdf(path, page, crop):
    r = run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page), path, "-"])
    words = []
    for m in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>', r.stdout):
        x0, y0, x1, y1 = map(float, m.groups()[:4])
        if crop and not (crop[0] <= x0 and x1 <= crop[0] + crop[2] and crop[1] <= y0 and y1 <= crop[1] + crop[3]):
            continue
        t = html.unescape(m.group(5))
        words.append((x0, y0, x1, y1, t))
    if not words:
        sys.exit("error: no text found on that page/crop (scanned PDF? use grid.py on an image instead)")
    # rows: cluster by vertical centre
    words.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    hmed = sorted(w[3] - w[1] for w in words)[len(words) // 2]
    lines = []
    for w in words:
        yc = (w[1] + w[3]) / 2
        if lines and abs(yc - lines[-1][0]) < hmed * 0.6:
            lines[-1][1].append(w)
        else:
            lines.append([yc, [w]])
    # columns: x positions where (almost) no row has ink.  A caption or a
    # spanning heading crosses the gaps in one row only, so it does not hide them.
    x_lo = int(min(w[0] for w in words)) - 1
    x_hi = int(max(w[2] for w in words)) + 2
    cover = [0] * (x_hi - x_lo)
    for _, ws in lines:
        hit = set()
        for w in ws:
            hit.update(range(int(w[0]) - x_lo, int(w[2]) - x_lo + 1))
        for x in hit:
            cover[x] += 1
    limit = max(1, int(len(lines) * 0.15))
    cuts, run_start = [], None
    for x, n in enumerate(cover + [len(lines)]):
        if n <= limit and x < len(cover):
            run_start = x if run_start is None else run_start
        else:
            if run_start is not None and x - run_start >= hmed * 0.8 and run_start > 0 and x < len(cover):
                cuts.append(x_lo + (run_start + x) / 2)
            run_start = None
    raw = []
    for _, ws in lines:
        row = [[] for _ in range(len(cuts) + 1)]
        for w in sorted(ws, key=lambda w: w[0]):
            k = sum(1 for c in cuts if (w[0] + w[2]) / 2 > c)
            row[k].append(w[4])
        raw.append([" ".join(c) for c in row])
    return rect_grid(raw)


# ---------------------------------------------------------------- writer
def is_num(s):
    return bool(NUM.match(s.replace(" ", ""))) and any(ch.isdigit() for ch in s)


def table_format(vals):
    ints, decs, sign = 1, 0, False
    for v in vals:
        v = v.replace(",", "").replace("−", "-").replace(" ", "")
        sign |= v[:1] in "+-"
        v = v.lstrip("+-")
        a, _, b = v.partition(".")
        ints, decs = max(ints, len(a)), max(decs, len(b))
    return ("-" if sign else "") + "%d.%d" % (ints, decs)


def write_draft(g, name, out, header_rows, numeric, source):
    rows, cols = len(g), len(g[0]) if g else 0
    if not rows or not cols:
        sys.exit("error: the table is empty")
    numeric_cols = {}
    if numeric:
        for j in range(cols):
            body = [g[i][j]["text"] for i in range(header_rows, rows) if g[i][j] and g[i][j]["text"]]
            if len(body) >= 2 and sum(is_num(v) for v in body) >= 0.8 * len(body):
                numeric_cols[j] = table_format([v for v in body if is_num(v)])
    spec = []
    for j in range(cols):
        spec.append("S[table-format=%s]" % numeric_cols[j] if j in numeric_cols else "l")
    lines = ["\\begin{tblr}{",
             "  colspec = {%s}," % " ".join(spec),
             "  hline{1,Z} = {0.08em}," ,
             "  hline{%d} = {0.05em}," % (header_rows + 1) if header_rows else None,
             ("  row{%s} = {font=\\bfseries}," % (header_rows if header_rows == 1 else "1-%d" % header_rows))
             if header_rows else None,
             "}"]
    lines = [l for l in lines if l is not None]
    for i in range(rows):
        cells = []
        for j in range(cols):
            c = g[i][j]
            if c is None:
                cells.append("")
                continue
            t = tex_escape(c["text"])
            if j in numeric_cols and not is_num(c["text"]):
                t = "{{{%s}}}" % t if t else ""          # non-numbers in an S column
            elif j in numeric_cols:
                t = c["text"].replace(",", "").replace("−", "-")
            if c.get("bold") and i >= header_rows and t:
                t = "\\textbf{%s}" % t if j not in numeric_cols else t
            if c["r"] > 1 or c["c"] > 1:
                span = ",".join(x for x in ("r=%d" % c["r"] if c["r"] > 1 else "",
                                            "c=%d" % c["c"] if c["c"] > 1 else "") if x)
                t = "\\SetCell[%s]{c} %s" % (span, t)
            cells.append(t)
        lines.append("  " + " & ".join(cells) + " \\\\")
    lines.append("\\end{tblr}")
    pre = ["\\usepackage{tabularray}"]
    if numeric_cols:
        pre += ["\\usepackage{siunitx}", "\\UseTblrLibrary{siunitx}"]
    os.makedirs(out, exist_ok=True)
    base = os.path.join(out, name)
    for ext in (".tblr", ".preamble.tex", ".cells.json"):
        if os.path.exists(base + ext) and not ARGS.force:
            sys.exit(f"error: {base + ext} exists; pass --force to overwrite the draft")
    write_text(base + ".tblr", "\n".join(lines) + "\n")
    write_text(base + ".preamble.tex", "\n".join(pre) + "\n")
    cells = [[None if c is None else {k: v for k, v in c.items() if k != "bold"} for c in row] for row in g]
    write_text(base + ".cells.json", json.dumps({"source": source, "rows": rows, "cols": cols,
                                                 "header_rows": header_rows, "cells": cells},
                                                ensure_ascii=False, indent=1) + "\n")
    print(f"draft  {base}.tblr  ({rows} rows x {cols} cols"
          + (f"; numeric columns {', '.join(str(j + 1) for j in numeric_cols)} -> S" if numeric_cols else "")
          + ")")
    print(f"       {base}.preamble.tex\n       {base}.cells.json")
    print("next   write NAME.request.md (references/requests.md), apply it to the .tblr, then build.py")


def main():
    global ARGS
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("Usage", 1)[1])
    ap.add_argument("source", nargs="?")
    ap.add_argument("--name", required=True)
    ap.add_argument("--out", default=".")
    ap.add_argument("--sheet")
    ap.add_argument("--range", help="Excel range, e.g. A1:H9 (must not cut merged cells)")
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--crop")
    ap.add_argument("--rows", type=int)
    ap.add_argument("--cols", type=int)
    ap.add_argument("--header-rows", type=int, default=1)
    ap.add_argument("--no-numeric", action="store_true")
    ap.add_argument("--force", action="store_true")
    ARGS = a = ap.parse_args()
    check_name(a.name, "table name")
    if not a.source:
        if not (a.rows and a.cols):
            sys.exit("error: give a SOURCE, or --rows and --cols for an empty skeleton")
        g = make_grid(a.rows, a.cols)
        src = "skeleton"
    else:
        if not os.path.isfile(a.source):
            sys.exit(f"error: {a.source} not found")
        ext = os.path.splitext(a.source)[1].lower()
        src = os.path.basename(a.source)
        if ext == ".csv":
            g = read_csv(a.source, ",")
        elif ext in (".tsv", ".tab"):
            g = read_csv(a.source, "\t")
        elif ext in (".md", ".markdown"):
            g = read_md(a.source)
        elif ext in (".html", ".htm"):
            g = read_html(a.source)
        elif ext == ".xlsx":
            g = read_xlsx(a.source, a.sheet, a.range)
            src += f" [{a.sheet or 'first sheet'}!{a.range or 'used range'}]"
        elif ext == ".pdf":
            g = read_pdf(a.source, a.page, floats(a.crop, 4, "--crop") if a.crop else None)
        else:
            sys.exit(f"error: unsupported source {ext!r}. Images: read them with grid.py and "
                     "use --rows/--cols for a skeleton")
    write_draft(g, a.name, os.path.abspath(a.out), max(0, a.header_rows), not a.no_numeric, src)


if __name__ == "__main__":
    main()
