# SPDX-License-Identifier: MIT
"""Lyra — A modern, async-first Lavalink v4 client for Python Discord libraries.

:copyright: (c) 2024-Present Crowby Inc.
:license: MIT, see LICENSE for more details.
"""

from __future__ import annotations

import logging

from .errors import (
    HTTPBadRequest,
    HTTPException,
    HTTPNotFound,
    HTTPUnauthorized,
    LyraError,
    MultipleCompatibleLibraries,
    NoCompatibleLibraries,
    NoNodesAvailable,
    NodeAlreadyConnected,
    NodeAlreadyExists,
    NodeNotConnected,
    PlayerNotConnected,
    TrackLoadException,
)
from .events import (
    LyraEvent,
    TrackEndEvent,
    TrackExceptionEvent,
    TrackStartEvent,
    TrackStuckEvent,
    WebSocketClosedEvent,
)
from .filter import (
    ChannelMix,
    Distortion,
    Equalizer,
    Filter,
    Karaoke,
    LowPass,
    Rotation,
    Timescale,
    Tremolo,
    Vibrato,
)
from .ip import (
    BalancingIPRoutePlannerStatus,
    BaseIPRoutePlannerStatus,
    FailingAddress,
    IPBlock,
    IPBlockType,
    IPRoutePlannerType,
    NanoIPRoutePlannerStatus,
    RotatingIPRoutePlannerStatus,
    RotatingNanoIPRoutePlannerStatus,
    RoutePlannerStatus,
)
from .node import Node
from .player import Player
from .playlist import Playlist
from .plugin import Plugin
from .pool import NodePool
from .region import Group, Region, VoiceRegion
from .search_type import SearchType
from .stats import CPUStats, FrameStats, MemoryStats, NodeStats
from .strategy import Strategy, StrategyCallable, StrategyList
from .track import Track
from .warnings import UnknownVersionWarning, UnsupportedVersionWarning

__title__ = "wavecord"
__author__ = "Crowby Inc."
__license__ = "MIT"
__copyright__ = "Copyright 2024-Present Crowby Inc."
__version__ = "1.0.0"

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = (
    # Core
    "Node",
    "NodePool",
    "Player",
    "Playlist",
    "Plugin",
    "SearchType",
    "Track",
    # Filters
    "ChannelMix",
    "Distortion",
    "Equalizer",
    "Filter",
    "Karaoke",
    "LowPass",
    "Rotation",
    "Timescale",
    "Tremolo",
    "Vibrato",
    # Regions
    "Group",
    "Region",
    "VoiceRegion",
    # Strategy
    "Strategy",
    "StrategyCallable",
    "StrategyList",
    # Stats
    "CPUStats",
    "FrameStats",
    "MemoryStats",
    "NodeStats",
    # IP Route Planner
    "BalancingIPRoutePlannerStatus",
    "BaseIPRoutePlannerStatus",
    "FailingAddress",
    "IPBlock",
    "IPBlockType",
    "IPRoutePlannerType",
    "NanoIPRoutePlannerStatus",
    "RotatingIPRoutePlannerStatus",
    "RotatingNanoIPRoutePlannerStatus",
    "RoutePlannerStatus",
    # Events
    "LyraEvent",
    "TrackEndEvent",
    "TrackExceptionEvent",
    "TrackStartEvent",
    "TrackStuckEvent",
    "WebSocketClosedEvent",
    # Errors
    "HTTPBadRequest",
    "HTTPException",
    "HTTPNotFound",
    "HTTPUnauthorized",
    "LyraError",
    "MultipleCompatibleLibraries",
    "NoCompatibleLibraries",
    "NoNodesAvailable",
    "NodeAlreadyConnected",
    "NodeAlreadyExists",
    "NodeNotConnected",
    "PlayerNotConnected",
    "TrackLoadException",
    # Warnings
    "UnknownVersionWarning",
    "UnsupportedVersionWarning",
)
