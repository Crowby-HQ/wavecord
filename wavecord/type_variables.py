# SPDX-License-Identifier: MIT
"""Generic TypeVar used for the Discord client type."""

from __future__ import annotations

from typing import TypeVar

from .__libraries import Client

__all__ = ("ClientT",)

ClientT = TypeVar("ClientT", bound=Client)
"""TypeVar bound to a Discord :class:`~discord.Client` subclass.

All public generics in WaveCord use this variable so that type checkers can
propagate the concrete client type through :class:`~wavecord.NodePool`,
:class:`~wavecord.Node`, and :class:`~wavecord.Player`.
"""
