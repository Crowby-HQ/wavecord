# SPDX-License-Identifier: MIT
"""Node selection strategy system."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from enum import Enum, auto
from logging import getLogger
from random import choice
from typing import TYPE_CHECKING, List, Optional, Union

from .region import VoiceRegion
from .type_variables import ClientT

if TYPE_CHECKING:
    from .node import Node

__all__ = ("Strategy", "StrategyCallable", "call_strategy")

_log = getLogger(__name__)

# A strategy callable receives (nodes, guild_id, shard_count, endpoint)
# and returns the filtered list of nodes.
StrategyCallable = Callable[
    [List["Node[ClientT]"], int, Optional[int], Optional[str]],  # type: ignore[name-defined]
    List["Node[ClientT]"],  # type: ignore[name-defined]
]
"""Type alias for a custom strategy function.

Signature: ``(nodes, guild_id, shard_count, endpoint) -> nodes``
"""

StrategyList = Union[
    StrategyCallable,
    Sequence["Strategy"],
    Sequence[StrategyCallable],
    Sequence[Union["Strategy", StrategyCallable]],
]
"""Accepted type for the ``default_strategies`` parameter on
:class:`~wavecord.NodePool`.
"""

# Match Discord voice endpoint hostnames, e.g. ``us-east1.discord.media``
_REGION_RE = re.compile(r"(?:vip-)?(?P<region>[a-z-]{1,15})\d{1,5}\.discord\.media")


class Strategy(Enum):
    """Built-in node selection strategies.

    Pass one or more of these (or custom callables) as ``default_strategies``
    to :class:`~wavecord.NodePool`.
    """

    LOCATION = auto()
    """Pick nodes whose :attr:`~wavecord.Node.regions` match the guild's
    voice region.
    """

    RANDOM = auto()
    """Pick a node at random from the remaining candidates."""

    SHARD = auto()
    """Pick nodes whose :attr:`~wavecord.Node.shard_ids` include the guild's shard."""

    USAGE = auto()
    """Pick the node with the lowest :attr:`~wavecord.Node.weight`."""


# Individual strategy implementations
def _shard_strategy(
    nodes: list,
    guild_id: int,
    shard_count: Optional[int],
    _endpoint: Optional[str],
) -> list:
    """Filter nodes by shard ID."""
    if shard_count is None:
        shard_count = 1

    shard_id = (guild_id >> 22) % shard_count

    filtered = [n for n in nodes if n.shard_ids is None or shard_id in n.shard_ids]
    return filtered or nodes


def _location_strategy(
    nodes: list,
    _guild_id: int,
    _shard_count: Optional[int],
    endpoint: Optional[str],
) -> list:
    """Filter nodes by voice region derived from the Discord endpoint."""
    if endpoint is None:
        return nodes

    match = _REGION_RE.match(endpoint)
    if not match:
        _log.warning(
            "Failed to extract region from endpoint %r; using all nodes.", endpoint
        )
        return nodes

    region_str = match.group("region")
    try:
        voice_region = VoiceRegion(region_str)
    except ValueError:
        _log.warning(
            "Unknown voice region %r from endpoint %r; using all nodes.",
            region_str,
            endpoint,
        )
        return nodes

    regional = [n for n in nodes if n.regions is not None and voice_region in n.regions]
    if not regional:
        _log.warning(
            "No nodes configured for region %r; falling back to all nodes.",
            voice_region.value,
        )
        return nodes

    return regional


def _usage_strategy(
    nodes: list,
    _guild_id: int,
    _shard_count: Optional[int],
    _endpoint: Optional[str],
) -> list:
    """Filter to the node(s) with the lowest weight score."""
    lowest: Optional[float] = None

    for node in nodes:
        w = node.weight
        if lowest is None or w < lowest:
            lowest = w

    if lowest is None:
        return nodes

    return [n for n in nodes if n.weight == lowest]


def _random_strategy(
    nodes: list,
    _guild_id: int,
    _shard_count: Optional[int],
    _endpoint: Optional[str],
) -> list:
    """Return a single randomly chosen node."""
    return [choice(nodes)]


# Public dispatcher
def call_strategy(
    strategy: Strategy,
    nodes: list,
    guild_id: int,
    shard_count: Optional[int],
    endpoint: Optional[str],
) -> list:
    """Dispatch a built-in :class:`Strategy` to its implementation.

    Parameters
    ----------
    strategy : Strategy
        The strategy variant to run.
    nodes : list
        Candidate nodes to filter.
    guild_id : int
        The Discord guild ID.
    shard_count : int or None
        Total shard count of the bot.
    endpoint : str or None
        The Discord voice server endpoint hostname.

    Returns
    -------
    list
        The filtered list of nodes (may be identical to *nodes* if nothing matched).
    """
    if strategy is Strategy.SHARD:
        return _shard_strategy(nodes, guild_id, shard_count, endpoint)
    elif strategy is Strategy.LOCATION:
        return _location_strategy(nodes, guild_id, shard_count, endpoint)
    elif strategy is Strategy.USAGE:
        return _usage_strategy(nodes, guild_id, shard_count, endpoint)
    elif strategy is Strategy.RANDOM:
        return _random_strategy(nodes, guild_id, shard_count, endpoint)
    else:
        msg = f"Unknown strategy: {strategy!r}"
        raise ValueError(msg)
