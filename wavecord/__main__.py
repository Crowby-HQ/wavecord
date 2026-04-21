# SPDX-License-Identifier: MIT
"""Run ``python -m wavecord`` to print version information."""

from __future__ import annotations

import platform
import sys

import aiohttp

from . import __version__


def _fmt(name: str, version: str) -> str:
    return f"- {name}: {version}"


lines = [
    f"WaveCord v{__version__}",
    _fmt("Python", sys.version.split()[0]),
    _fmt("aiohttp", aiohttp.__version__),
    _fmt("Platform", platform.platform()),
]

try:
    import orjson

    lines.append(_fmt("orjson", orjson.__version__) + "  ✓")
except ImportError:
    lines.append("- orjson: not installed (install wavecord[speedups] for faster JSON)")

print("\n".join(lines))
