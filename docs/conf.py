# SPDX-License-Identifier: MIT
"""Sphinx configuration for WaveCord documentation."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

# Project info
project = "WaveCord"
copyright = "2024-present Crowby Inc."
author = "Crowby Inc."
release = "1.0.0"
version = "1.0.0"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.trio",
    "sphinx_inline_tabs",
]

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_rtype = False
napoleon_use_param = False

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiohttp": ("https://docs.aiohttp.org/en/stable", None),
    "discord": ("https://discordpy.readthedocs.io/en/stable", None),
}

# Theme
html_theme = "furo"
html_title = "WaveCord"

html_theme_options = {
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "source_repository": "https://github.com/Crowby-HQ/wavecord",
    "source_branch": "main",
    "source_directory": "docs/",
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
default_role = "py:obj"
