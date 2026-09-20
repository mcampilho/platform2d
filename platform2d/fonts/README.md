# Bundled interface fonts

Original, unmodified Noto binaries. `sources.json` records upstream commit URLs,
byte sizes and SHA-256 checksums. No font download is needed at runtime.

- Noto Sans: `OFL-Latin-Arabic.txt` (upstream archive general license).
- Noto Naskh Arabic: `OFL-Arabic.txt` (Google Fonts distribution, including Latin).
  The variable font has the local filename `NotoNaskhArabic-Regular.ttf`; its
  bytes are unchanged and the default weight is used.
- Noto Sans CJK SC and JP: `OFL-CJK.txt`.

These fonts use SIL Open Font License 1.1, not the project's MIT license.
Preserve the notices when redistributing them, including in an executable.
Coverage is checked with FreeType, not SDL_ttf's fallback-box metrics.

These copies are packaged with Platform2D so games and the common controls
panel can display all eight languages without importing any tutorial code.
