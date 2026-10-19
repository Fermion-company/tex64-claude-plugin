#!/usr/bin/env python3
"""Insert a built table into the user's own document.

LaTeX (.tex)
  * merges the table's \\usepackage / \\UseTblrLibrary needs into the host
    preamble (only what is missing; options are kept; one marked block;
    libraries always after \\usepackage{tabularray}).  Other preamble lines
    (e.g. \\sisetup{...}, \\SetTblrStyle) are added only if the host has no
    setting of the same kind; otherwise they are printed as a suggestion.
  * puts a table environment that \\input's the .tblr file
      - at the line containing --marker TEXT (the marker line is replaced), or
      - after line --line N of the document body, or
      - nowhere (default): the change is only previewed.
    A longtblr is \\input on its own (it carries its own caption and breaks pages).
Markdown (.md / .qmd / .markdown)
  * inserts ![caption](TAB.svg){#tbl:label} (Pandoc/Quarto style) the same way.

Before writing, a backup DOC.bak (DOC.bak.1, .2 ... if it exists) is made and
the diff is printed.  Nothing is copied or written when a check fails.

Usage
  insert.py --doc main.tex --tab tables/foo.tblr [--marker '%%TAB foo' | --line 120]
            [--caption TEXT] [--label tab:foo] [--placement htbp]
            [--copy-to tables] [--force] [--dry-run]

  --copy-to DIR  copy the bundle (.tblr .preamble.tex .pdf .svg .png) into DIR
                 (relative to the document; must stay inside the document's
                 folder) and reference it from there.
  --force        insert even if the label or the \\input is already present,
                 and overwrite differing files in --copy-to.
"""
import argparse
import difflib
import filecmp
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import posix_rel, read_text, strip_comments, write_text  # noqa: E402

PKG = re.compile(r"\\(?:usepackage|RequirePackage)\s*(\[[^\]]*\])?\s*\{([^}]*)\}")
LIB = re.compile(r"\\UseTblrLibrary\s*\{([^}]*)\}")
SETKEY = re.compile(r"\\(sisetup|SetTblrStyle|SetTblrInner|SetTblrOuter|NewTblrTheme)\b")
BEGIN_DOC = re.compile(r"\\begin\s*\{document\}")


def needs(preamble_text):
    pk, libs = [], []
    code = strip_comments(preamble_text)
    for m in PKG.finditer(code):
        for p in m.group(2).split(","):
            if p.strip():
                pk.append((p.strip(), re.sub(r"\s+", " ", m.group(1) or "")))
    for m in LIB.finditer(code):
        libs += [x.strip() for x in m.group(1).split(",") if x.strip()]
    rest = LIB.sub("", PKG.sub("", code))
    other = [l.rstrip() for l in rest.splitlines() if l.strip()]
    return pk, libs, other


def begin_document_line(lines):
    for i, l in enumerate(lines):
        if BEGIN_DOC.search(strip_comments(l)):
            return i
    return None


def backup_path(doc):
    b, n = doc + ".bak", 1
    while os.path.exists(b):
        b = f"{doc}.bak.{n}"
        n += 1
    return b


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("Usage", 1)[1])
    ap.add_argument("--doc", required=True)
    ap.add_argument("--tab", required=True)
    ap.add_argument("--marker")
    ap.add_argument("--line", type=int)
    ap.add_argument("--caption", default="")
    ap.add_argument("--label")
    ap.add_argument("--placement", default="htbp")
    ap.add_argument("--copy-to")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.marker and a.line is not None:
        sys.exit("error: give either --marker or --line, not both")
    doc = os.path.abspath(a.doc)
    if not os.path.isfile(doc):
        sys.exit(f"error: {a.doc} not found")
    tab = os.path.abspath(a.tab)
    if not os.path.isfile(tab):
        sys.exit(f"error: {a.tab} not found (build it with build.py first)")
    name = os.path.splitext(os.path.basename(tab))[0]
    label = a.label or "tab:" + name
    docdir = os.path.dirname(doc)
    long_table = bool(re.search(r"\\begin\s*\{longtblr\}", strip_comments(read_text(tab))))

    copies = []
    if a.copy_to:
        dest = os.path.realpath(os.path.join(docdir, a.copy_to))
        if os.path.commonpath([dest, os.path.realpath(docdir)]) != os.path.realpath(docdir):
            sys.exit(f"error: --copy-to {a.copy_to!r} points outside the document's folder")
        for ext_ in (".tblr", ".preamble.tex", ".pdf", ".svg", ".png"):
            srcf = os.path.splitext(tab)[0] + ext_
            dstf = os.path.join(dest, name + ext_)
            if not os.path.exists(srcf):
                continue
            if os.path.exists(dstf):
                if os.path.samefile(srcf, dstf) or filecmp.cmp(srcf, dstf, shallow=False):
                    continue
                if not a.force:
                    sys.exit(f"error: {dstf} exists and differs from {srcf}; not overwriting (use --force)")
            copies.append((srcf, dstf))
        tab_used = os.path.join(dest, name + ".tblr")
    else:
        tab_used = tab
    rel = posix_rel(tab_used, docdir)

    text = read_text(doc)
    lines = text.splitlines(keepends=True)
    code_all = strip_comments(text)
    is_md = os.path.splitext(doc)[1].lower() in (".md", ".qmd", ".markdown")
    target = os.path.splitext(rel)[0] + (".svg" if is_md else ".tblr")
    md_label = label.replace("tab:", "tbl:", 1) if is_md else label
    dup = re.search(r"\\label\s*\{%s\}|\{#%s\}" % (re.escape(label), re.escape(md_label)),
                    text if is_md else code_all)
    dup_input = (target in text) if is_md else re.search(r"\\input\s*\{%s\}" % re.escape(target), code_all)
    if (dup or dup_input) and not a.force:
        sys.exit(f"error: {label if dup else target} is already in {a.doc}; use --force to insert again")

    new_lines, suggestions, body_start = list(lines), [], 0
    if is_md:
        block = f"![{a.caption}]({target}){{#{md_label}}}\n"
    else:
        bd = begin_document_line(lines)
        if bd is None:
            sys.exit("error: no \\begin{document} in --doc; is this the main file?")
        head = strip_comments("".join(lines[:bd]))
        have_pk = {p.strip() for _, ps in PKG.findall(head) for p in ps.split(",")}
        have_lib = {l.strip() for ls in LIB.findall(head) for l in ls.split(",")}
        have_keys = {m.group(1) for m in SETKEY.finditer(head)}
        pre_path = os.path.splitext(tab)[0] + ".preamble.tex"
        pk, libs, other = needs(read_text(pre_path) if os.path.exists(pre_path) else "")
        if not any(p == "tabularray" for p, _ in pk):
            pk.insert(0, ("tabularray", ""))
        add = []
        for p, opt in pk:
            if p not in have_pk:
                add.append(f"\\usepackage{opt}{{{p}}}")
                have_pk.add(p)
        miss_lib = [l for l in libs if l not in have_lib]
        if miss_lib:
            add.append("\\UseTblrLibrary{%s}" % ",".join(miss_lib))
        for o in other:
            m = SETKEY.search(o)
            if m and m.group(1) in have_keys:
                suggestions.append(o)
            elif o.strip() not in head:
                add.append(o)
        if add:
            new_lines[bd:bd] = ["% tablify: added for " + name + "\n"] + [x + "\n" for x in add]
        body_start = bd + 1
        if long_table:
            block = "\\input{%s}\n" % target
            if a.caption or a.label:
                print("note: longtblr takes its caption and label in its own options: "
                      "\\begin{longtblr}[caption={...},label={%s}]" % label)
        else:
            block = ("\\begin{table}[%s]\n  \\centering\n  \\caption{%s}\n  \\label{%s}\n"
                     "  \\input{%s}\n\\end{table}\n" % (a.placement, a.caption, label, target))

    if a.marker:
        hits = [i for i, l in enumerate(new_lines) if a.marker in l]
        if len(hits) != 1:
            sys.exit(f"error: marker {a.marker!r} found {len(hits)} times; need exactly one")
        if not is_md and hits[0] < body_start + (len(new_lines) - len(lines)):
            sys.exit("error: the marker is in the preamble, not in the document body")
        new_lines[hits[0]:hits[0] + 1] = block.splitlines(keepends=True)
    elif a.line is not None:
        lo = body_start if not is_md else 0
        if not lo <= a.line <= len(lines):
            sys.exit(f"error: --line {a.line} must be between {lo} and {len(lines)} "
                     "(after \\begin{document} for LaTeX)")
        at = a.line + (len(new_lines) - len(lines))
        if at > 0 and not new_lines[at - 1].endswith("\n"):
            new_lines[at - 1] += "\n"
        new_lines[at:at] = block.splitlines(keepends=True)
    else:
        print("no --marker/--line: preview only\n")
        print(block)
        a.dry_run = True

    for s in suggestions:
        print(f"note: not adding {s.strip()!r}: the document already has a setting of this kind")
    if new_lines == lines:
        print("document already has everything; nothing changed")
        return
    sys.stdout.writelines(difflib.unified_diff(lines, new_lines, doc, doc + " (new)"))
    if a.dry_run:
        print("\n(dry run: nothing written)")
        return
    for srcf, dstf in copies:
        os.makedirs(os.path.dirname(dstf), exist_ok=True)
        shutil.copy(srcf, dstf)
    bak = backup_path(doc)
    shutil.copy(doc, bak)
    write_text(doc, "".join(new_lines))
    print(f"\nwritten {doc}  (backup: {bak})")
    if copies:
        print("copied  " + ", ".join(os.path.basename(d) for _, d in copies)
              + f" -> {posix_rel(os.path.dirname(copies[0][1]), docdir)}/")


if __name__ == "__main__":
    main()
