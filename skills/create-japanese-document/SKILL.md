---
name: create-japanese-document
description: Create Japanese study notes, exam summaries, exercise sheets, or simple academic reports as typeset PDFs with the TeX64 tools. Use when the user asks to turn material into a Japanese PDF, study guide, シケプリ, 講義ノート, 問題集, 授業プリント, or レポート.
---

# Create a Japanese document with TeX64

TeX64 typesets Japanese documents with LuaLaTeX. The user does not need to know
that TeX is used, and does not need TeX installed.

## Choosing

1. Infer the document kind, study or report, and page size from the request.
   Study documents default to B5, reports to A4, unless the user named a size.
   If the kind is genuinely unclear, ask one short question in the user's own
   words — for example whether they want a structured study handout or a plain
   report. Use the client's structured question UI (such as `AskUserQuestion`)
   when it is available, one question at a time.
2. Production details — fonts, packages, engines, margins in millimetres — are
   decided from the arguments; they are not questions for the user. Translate
   wishes such as "soft", "formal", "compact" or "easy to read" into the
   document yourself.
3. `doc_types` lists the document types. The page design comes with the type;
   the one visual choice left is `theme`: `dark` for a black background,
   white-on-black or a dark theme, otherwise `light`.

## Writing

4. `scaffold_document` returns a compilable skeleton with a comment in each
   section saying what belongs there. Fill it with the user's material.
5. `check_document` checks the structure: exercise/answer pairing, numbering,
   forbidden notation, and scaffold slots left unfilled (`<ここに…>`
   placeholders, `% TODO` with nothing written under it). Fix what it reports
   before typesetting. While the skeleton is still being filled, `draft=true`
   sets the unfilled slots aside and only counts them.

## Typesetting

6. Pick the route the environment supports:
   - **Files can be written and `latexmk` runs locally** (Claude Code with
     TeX Live): `get_style_files` (start with `list=true`) returns the style
     files with their relative paths; `compile_guide` describes the build and
     how to check the pages.
   - **Otherwise** (no TeX, or no local shell): `prepare_compile` issues a
     one-time `compileToken`; pass it to `compile_document` together with the
     full source and the same `preset` / `paper` / `theme` as the scaffold. The
     server generates the styles, typesets, and returns a temporary PDF link
     and page images. Each compile needs a fresh token.
   - **Long documents** that do not fit in one call need not be shortened:
     `stage_file` places one chapter file per call (`append=true` continues a
     file) and returns an `uploadId`; the main source `\input`s the chapters,
     and the same `uploadId` goes to `check_document` (so the chapters are
     checked too) and `compile_document`. Staged files survive a retry, so only
     changed chapters are sent again.
7. Look at the returned page images — cover, Japanese glyphs, headings, boxes,
   page breaks — and fix the source before handing over something unchecked.

## Handing over

8. Give the user the PDF link and the page images, and mention that the server
   link expires within the hour so they should save the file.
9. Describe adjustable parts by how they look on the page. TeX logs, package
   names and error text are for fixing the document, not for the user.

## Limits

`compile_document` uses the fonts installed on the server, refuses paths
outside the document, and cannot install packages. If a build fails because
something is unavailable, rewrite the source with what is available.
