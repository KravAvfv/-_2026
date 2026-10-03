#!/usr/bin/env bash
# Convert a .docx to .pdf headlessly via the OnlyOffice x2t converter (no LibreOffice on this machine).
# Usage: tools/docx2pdf.sh <input.docx> [output.pdf]
set -euo pipefail
in="$(realpath "$1")"
out="$(realpath -m "${2:-${1%.docx}.pdf}")"
X2T_DIR=/opt/onlyoffice/desktopeditors/converter
FONTS="$HOME/.local/share/onlyoffice/desktopeditors/data/fonts/AllFonts.js"
[[ -x "$X2T_DIR/x2t" ]] || { echo "x2t not found at $X2T_DIR" >&2; exit 2; }
[[ -f "$FONTS" ]] || { echo "OnlyOffice font cache missing: $FONTS (open OnlyOffice once to build it)" >&2; exit 2; }
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
# x2t chokes on non-ASCII paths in some builds — work on ASCII-named copies.
cp "$in" "$tmp/in.docx"
cat > "$tmp/task.xml" <<XML
<?xml version="1.0" encoding="utf-8"?>
<TaskQueueDataConvert>
<m_sFileFrom>$tmp/in.docx</m_sFileFrom>
<m_sFileTo>$tmp/out.pdf</m_sFileTo>
<m_nFormatTo>513</m_nFormatTo>
<m_sFontDir>/usr/share/fonts</m_sFontDir>
<m_sAllFontsPath>$FONTS</m_sAllFontsPath>
<m_bIsNoBase64>true</m_bIsNoBase64>
</TaskQueueDataConvert>
XML
( cd "$X2T_DIR" && LD_LIBRARY_PATH=. ./x2t "$tmp/task.xml" >"$tmp/log" 2>&1 ) || { cat "$tmp/log" >&2; exit 1; }
[[ -s "$tmp/out.pdf" ]] || { echo "conversion produced no PDF" >&2; cat "$tmp/log" >&2; exit 1; }
mv "$tmp/out.pdf" "$out"
echo "$out"
