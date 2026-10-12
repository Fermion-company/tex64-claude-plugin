# TeX64 branding

The next Anthropic and OpenAI distributions use the same purple Σ TeX64 icon.
These PNGs are copied without modification from the desktop app's icon set:

| Packaged file | Source under `TeX64-Pro/Resources/icons/tex64.iconset/` |
|---|---|
| `logo-512.png` | `icon_512x512.png` (512 × 512) |
| `icon-64.png` | `icon_32x32@2x.png` (64 × 64) |

The plugin manifest's `icon` references `./assets/logo-512.png` for Anthropic's
directory. Include the file in the package and verify the directory preview
before release. Keep these files in sync with `tex64-openai-plugin/assets/`
when the product icon changes.
