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

## Connect from Claude Code

For the MCP tools, run this in your project directory:

```sh
claude mcp add --transport http tex64 https://mcp.tex64.com
claude mcp list
```

Start Claude Code in that directory and open `/mcp` to check that `tex64` is
connected. No TeX64 account or API key is needed. This connects the server's
tools; it does not install the skills in this repository. See the official
[Claude Code MCP guide](https://code.claude.com/docs/en/mcp).

To load the bundled skills and MCP configuration together for a Claude Code
session, use this route instead:

```sh
git clone https://github.com/Fermion-company/tex64-claude-plugin.git
claude --plugin-dir ./tex64-claude-plugin
```

The directory contains the plugin manifest, `.mcp.json`, and the skills. In that
session, check `/plugin` and `/mcp`. This repository is a plugin directory, not a
marketplace; see the official [plugin guide](https://code.claude.com/docs/en/plugins).

## Connect from Claude on the web or desktop

In Claude's connector settings, add a custom remote connector with this URL:

```text
https://mcp.tex64.com
```

Use Streamable HTTP if your client asks for a transport. Custom connectors must
be available on your Claude plan and allowed by your organization. The connector
adds MCP tools; it does not load this repository's local skills. The
[public server guide](https://mcp.tex64.com) and
[TeX64 MCP product page](https://tex64.com/mcp) describe the service.

## Make and save a first document

Try: “Use TeX64 to turn these notes into a one-page Japanese lecture-note PDF.”
Check the page previews, then download the PDF immediately: its temporary link
expires within one hour.

To keep editing, ask Claude to save the LaTeX source it used, all referenced
chapter files and images, and the matching style files returned by
`get_style_files`. Keep them in one project folder. Open that folder in
[TeX64](https://tex64.com/download); follow the
[project guide](https://tex64.com/docs/getting-started) to edit and build locally.
The PDF link does not provide a downloadable source project, so keep the source
from the conversation or workspace as well.

## Tools

| Tool | What it does | Annotation |
|---|---|---|
| `doc_types` | Lists the document types (lecture note, exam summary, exercise set, past exam, language note, cram sheet, handout, academic report) | read-only |
| `scaffold_document` | Returns a compilable `.tex` skeleton for a type | read-only |
| `check_document` | Checks a source's structure: exercise/answer pairing, numbering, forbidden notation, unfilled scaffold slots; follows `\input` into staged chapters | read-only |
| `get_style_files` | Returns the style files for building locally | read-only |
| `visualization_guide` | Explains how to turn source material into tables, diagrams, and plots | read-only |
| `create_visualization` | Returns editable source for a table, diagram, or numeric plot | read-only |
| `compile_guide` | Describes how to build and check a document locally | read-only |
| `known_issues` | Looks up known jlreq / luatexja / LuaLaTeX combination problems | read-only |
| `prepare_compile` | Issues the one-time token for a single server-side compile | write (allocates one-time token) |
| `stage_file` | Places one chapter file of a long document on the server, kept in memory for 60 minutes after the last write | write (holds the file in memory) |
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
  directory that is deleted as soon as the build ends. Chapter files placed with
  `stage_file` for a long document are held in server memory only and are
  discarded 60 minutes after the last write.
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

## Source-based visualizations

The package now includes `tikzify` and `tablify`, with their local scripts, templates, references and licenses. The document skill routes source material through `visualization_guide` and `create_visualization` for tables, node/edge diagrams and numeric plots, preserves source locators and intentional transformations, then uses the existing PDF compilation flow. Source reading/OCR remains the client's responsibility; no additional AI service is called. The matching server 0.8.1 is deployed at the existing endpoint. OpenAI MCP scanning passed with all 11 tools published; package 1.4.0 has passed metadata and all three skill checks and awaits final submission consent. This does not mean directory package approval.
