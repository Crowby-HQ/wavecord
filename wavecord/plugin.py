# SPDX-License-Identifier: MIT
"""Plugin model returned by the Lavalink plugins endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .typings import PluginData

__all__ = ("Plugin",)


class Plugin:
    """Represents a Lavalink server plugin.

    Attributes
    ----------
    name : str
        The plugin name.
    version : str
        The plugin version string.
    """

    __slots__ = ("name", "version")

    def __init__(self, data: PluginData) -> None:
        self.name: str = data["name"]
        self.version: str = data["version"]

    def __repr__(self) -> str:
        return f"<Plugin name={self.name!r} version={self.version!r}>"
