#!/usr/bin/env python3
"""Verify the retail executable and configure reccmp; optionally fetch MSVC SP5."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from inspect_binary import inspect
from toolchain import DEFAULT_TOOLCHAIN, ROOT, TOOLCHAIN_COMMIT, TOOLCHAIN_URL, validate
from originals import REFERENCE_SHA256, SUPPORTED_ORIGINALS, configured_original

# Reference (European) executable; see originals.py for every supported build.
ORIGINAL_SHA256 = REFERENCE_SHA256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, default=configured_original())
    parser.add_argument("--fetch-toolchain", action="store_true")
    parser.add_argument("--toolchain", type=Path, default=Path(os.environ.get("MSVC6_ROOT", DEFAULT_TOOLCHAIN)))
    args = parser.parse_args()
    original = args.original.resolve()
    identity = inspect(original)
    if identity["sha256"] not in SUPPORTED_ORIGINALS:
        parser.error(f"Unsupported original SHA-256: {identity['sha256']}. See docs/compiler.md.")
    if identity["machine"] != "0x014c" or not identity["rich"]["checksum_valid"]:
        parser.error("Expected an x86 PE32 with an intact Rich header")

    if args.fetch_toolchain and not args.toolchain.exists():
        args.toolchain.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--no-checkout", TOOLCHAIN_URL, str(args.toolchain)], check=True)
        subprocess.run(["git", "-C", str(args.toolchain), "checkout", "--detach", TOOLCHAIN_COMMIT], check=True)
    if args.fetch_toolchain or args.toolchain.exists():
        validate(args.toolchain)
        print(f"Verified MSVC SP5: {args.toolchain.resolve()}")

    # JSON strings are valid YAML scalars, including Windows paths and apostrophes.
    user = "targets:\n  LEGORACERS2:\n    path: " + json.dumps(str(original)) + "\n"
    (ROOT / "reccmp-user.yml").write_text(user, encoding="utf-8")
    print(f"Verified original ({SUPPORTED_ORIGINALS[identity['sha256']]}): {original}\nSHA-256: {identity['sha256']}")
    print("Wrote reccmp-user.yml. See README.md for building and comparison.")


if __name__ == "__main__":
    main()
