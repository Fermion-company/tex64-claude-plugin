# TeX64 plugin for Claude

TeX64 turns course material into Japanese lecture notes, exam summaries,
exercise sheets and simple academic reports, typeset with LuaLaTeX and returned
as a PDF. Users describe the result in ordinary language; the page design,
fonts and production details are handled by TeX64. No TeX installation is
needed: when there is none, the document is typeset on the TeX64 server and a
temporary PDF link with page previews comes back.

This plugin bundles:

- **The TeX64 MCP server** (`https://mcp.tex64.com/mcp`, Streamable HTTP, no
  account or authentication).
- **The `create-japanese-document` skill**, which walks Claude through choosing
  a document type, filling the skeleton, checking it and typesetting it.

## Tools

| Tool | What it does | Annotation |
|---|---|---|
| `doc_types` | Lists the document types (lecture note, exam summary, exercise set, past exam, language note, cram sheet, handout, academic report) | read-only |
| `scaffold_document` | Returns a compilable `.tex` skeleton for a type | read-only |
| `check_document` | Checks a source's structure: exercise/answer pairing, numbering, forbidden notation | read-only |
| `get_style_files` | Returns the style files for building locally | read-only |
| `compile_guide` | Describes how to build and check a document locally | read-only |
| `known_issues` | Looks up known jlreq / luatexja / LuaLaTeX combination problems | read-only |
| `prepare_compile` | Issues the one-time token for a single server-side compile | read-only |
| `compile_document` | Typesets a `.tex` source on the server and returns a temporary PDF link and page images | write (creates a temporary file) |

## Example prompts

- 「この講義資料から、B5 の講義ノートを PDF で作って」
  (Make a B5 lecture-note PDF from these slides.)
- 「来週の試験範囲をシケプリにまとめて。黒背景で」
  (Summarise next week's exam range as a cram sheet, on a black background.)
- 「TeX は入れていないけど、この実験結果を A4 のレポートにして」
  (I don't have TeX — turn these lab results into an A4 report.)
- 「この問題と解答で演習プリントを作って」
  (Make an exercise sheet from these problems and answers.)

## Privacy Policy

TeX64's privacy policy is at <https://mcp.tex64.com/privacy> (full policy:
<https://tex64.com/privacy>). In short:

- **Collection:** no account or sign-in. TeX64 receives only what a tool call
  sends: the tool arguments, and for `compile_document` the document source and
  any files passed with it. It does not read conversation history or other data.
- **Use and storage:** the read-only tools do not persist prompts, document
  source or tool results. `compile_document` writes the source to a throwaway
  directory that is deleted as soon as the build ends.
- **Retention:** the resulting PDF and page images are kept only long enough to
  download them — under an hour. Anyone holding the returned link can download
  them until they expire, so treat the link as the document itself.
- **Third parties:** infrastructure providers may process transient network and
  security data needed to operate the service. Do not submit secrets or
  personal information.
- **Contact:** <https://mcp.tex64.com/support>

Terms of service: <https://mcp.tex64.com/terms>

## Support

<https://mcp.tex64.com/support> — Fermion Inc. (<https://fermion.company/>)

## License

MIT
