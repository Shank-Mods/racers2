#!/bin/sh
# Reproduce research/ps2-symbols/ps2-name-map.csv from a user-supplied PS2 executable.
# Usage: tools/ps2/run.sh /path/to/SLUS_200.42 "/path/to/LEGO Racers 2.exe"
set -e
ELF="$1"; EXE="$2"; HERE=$(dirname "$0"); ROOT="$HERE/../.."; TMP=$(mktemp -d)
echo "4525f89a6a07c4c4a4af996cd279b1719b7179c679fd474f22b61f032a5bb810  $ELF" | sha256sum -c -
python "$HERE/xref_extract.py" "$ELF" "$EXE" "$ROOT/reccmp/function-inventory.csv" "$TMP/xrefs.json"
python "$HERE/namematch.py" "$TMP/xrefs.json" "$ROOT/reccmp/function-inventory.csv" "$TMP/matches.json"
python "$HERE/name_map.py" "$TMP/matches.json" "$ROOT/LEGO Racers 2/src" - "$ROOT/reccmp/function-inventory.csv" "$ROOT/research/ps2-symbols/ps2-name-map.csv"
