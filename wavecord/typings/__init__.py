# SPDX-License-Identifier: MIT
"""TypedDicts and type aliases for Lavalink v4 payloads."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

__all__ = (
    "CPU",
    "Memory",
    "FrameStats",
    "Stats",
    "TrackInfo",
    "TrackData",
    "TrackWithInfo",
    "PlaylistInfo",
    "PlaylistData",
    "TrackLoadingResult",
    "ExceptionPayload",
    "PlayerUpdateState",
    "PlayerVoiceState",
    "PlayerData",
    "UpdatePlayerPayload",
    "UpdatePlayerParams",
    "UpdateSessionPayload",
    "VoicePayload",
    "EventPayload",
    "IncomingMessage",
    "OutgoingMessage",
    "IPBlock",
    "FailingIPAddress",
    "BaseDetails",
    "RotatingIPRouteDetails",
    "NanoIPRouteDetails",
    "RotatingNanoIPRouteDetails",
    "BalancingIPRouteDetails",
    "RoutePlannerStatus",
    "PluginData",
)

# Corouting alias
from typing import Coroutine

Coro = Coroutine[Any, Any, Any]


# Node Stats
class CPU(TypedDict):
    cores: int
    systemLoad: float
    lavalinkLoad: float


class Memory(TypedDict):
    free: int
    used: int
    allocated: int
    reservable: int


class FrameStats(TypedDict):
    sent: int
    nulled: int
    deficit: int


class Stats(TypedDict):
    players: int
    playingPlayers: int
    uptime: int
    memory: Memory
    cpu: CPU
    frameStats: Optional[FrameStats]


# Track
class TrackInfo(TypedDict):
    identifier: str
    isSeekable: bool
    author: str
    length: int
    isStream: bool
    position: int
    title: str
    uri: Optional[str]
    artworkUrl: Optional[str]
    isrc: Optional[str]
    sourceName: str


class TrackData(TypedDict):
    encoded: str
    info: TrackInfo
    pluginInfo: Dict[str, Any]


TrackWithInfo = TrackData


# Playlist
class PlaylistInfo(TypedDict):
    name: str
    selectedTrack: int


class PlaylistData(TypedDict):
    info: PlaylistInfo
    pluginInfo: Dict[str, Any]
    tracks: List[TrackData]


# Load result
class ExceptionPayload(TypedDict, total=False):
    message: str
    severity: str
    cause: str


class TrackLoadingResult(TypedDict, total=False):
    loadType: str
    data: Any


# Player
class PlayerUpdateState(TypedDict, total=False):
    time: int
    position: int
    connected: bool
    ping: int


class PlayerVoiceState(TypedDict):
    token: str
    endpoint: str
    sessionId: str


class PlayerData(TypedDict, total=False):
    guildId: str
    track: Optional[TrackData]
    volume: int
    paused: bool
    state: PlayerUpdateState
    voice: PlayerVoiceState
    filters: Dict[str, Any]


# REST payloads
class UpdatePlayerPayload(TypedDict, total=False):
    encodedTrack: Optional[str]
    identifier: str
    position: int
    endTime: int
    volume: int
    paused: bool
    filters: Dict[str, Any]
    voice: VoicePayload


class UpdatePlayerParams(TypedDict, total=False):
    noReplace: str


class UpdateSessionPayload(TypedDict, total=False):
    resuming: bool
    timeout: int
    resumingKey: str


class VoicePayload(TypedDict):
    token: str
    endpoint: str
    sessionId: str


# WebSocket events
class EventPayload(TypedDict, total=False):
    op: str
    type: str
    guildId: str
    track: TrackData
    reason: str
    thresholdMs: int
    exception: ExceptionPayload
    code: int
    byRemote: bool


class IncomingMessage(TypedDict, total=False):
    op: str
    guildId: str
    state: PlayerUpdateState
    type: str
    sessionId: str
    resumed: bool
    players: int
    playingPlayers: int
    uptime: int
    memory: Memory
    cpu: CPU
    frameStats: Optional[FrameStats]


OutgoingMessage = Dict[str, Any]


# Route planner
class IPBlock(TypedDict):
    type: str
    size: str


class FailingIPAddress(TypedDict):
    address: str
    failingTimestamp: int
    failingTime: str


class BaseDetails(TypedDict):
    ipBlock: IPBlock
    failingAddresses: List[FailingIPAddress]


class RotatingIPRouteDetails(BaseDetails):
    rotateIndex: str
    ipIndex: str
    currentAddress: str


class NanoIPRouteDetails(BaseDetails):
    currentAddressIndex: str


class RotatingNanoIPRouteDetails(BaseDetails):
    blockIndex: str
    currentAddressIndex: str


class BalancingIPRouteDetails(BaseDetails):
    pass


class RoutePlannerStatus(TypedDict, total=False):
    cls: Optional[str]
    details: Optional[BaseDetails]


# Plugin
class PluginData(TypedDict):
    name: str
    version: str
