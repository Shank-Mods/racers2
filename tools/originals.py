"""Supported retail executables and where the configured one lives.

The European executable is the reference: its addresses, inventories and
reports define the project. The North American executable has the same size,
sections, imports, Rich header and code layout; it was linked two minutes
later (2001-08-13 10:20:09 UTC). Every measured function score and datacmp
result is identical against both. The only known difference is the region
flag returned through application dispatch slot 0x7c, which selects the
SLUS-20042 save name and the single American English language.
"""

import hashlib
import json
from pathlib import Path
import re

from toolchain import ROOT

EUROPE_SHA256 = "6ed248b0ee8e52669ca93f0a2d7eb4c4c2c7ed477550a5f488bfe029270d854d"
NORTH_AMERICA_SHA256 = "074899f5e94ecae323f4928b9bfed6d67d7c9414cd625ff506fe3bf4a748f168"

SUPPORTED_ORIGINALS = {
    EUROPE_SHA256: "Europe",
    NORTH_AMERICA_SHA256: "North America",
}
REFERENCE_SHA256 = EUROPE_SHA256

# Retail dispatch targets that differ from the reference inventories, keyed by
# executable hash, then (table, byte offset).
REGION_DISPATCH_TARGETS = {
    NORTH_AMERICA_SHA256: {("primary", 0x7C): 0x00486A70},
}

DEFAULT_ORIGINAL = ROOT.parent / "LEGO Racers 2" / "LEGO Racers 2.exe"


def sha256_of(data):
    return hashlib.sha256(data).hexdigest()


def require_supported(data):
    """Return the hash of a supported original or raise ValueError."""
    digest = sha256_of(data)
    if digest not in SUPPORTED_ORIGINALS:
        raise ValueError("Unsupported original executable SHA-256")
    return digest


def configured_original():
    """The original selected by tools/setup.py (reccmp-user.yml), else the default path."""
    user = ROOT / "reccmp-user.yml"
    if user.is_file():
        match = re.search(r"^\s*path:\s*(\".*\")\s*$", user.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            return Path(json.loads(match.group(1)))
    return DEFAULT_ORIGINAL
