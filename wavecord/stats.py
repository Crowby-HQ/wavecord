# SPDX-License-Identifier: MIT
"""Node statistics models."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .typings import CPU, FrameStats as FrameStatsPayload, Memory, Stats

__all__ = (
    "CPUStats",
    "FrameStats",
    "MemoryStats",
    "NodeStats",
)


class CPUStats:
    """CPU statistics reported by the Lavalink node.

    Attributes
    ----------
    cores : int
        Number of CPU cores available on the host.
    system_load : float
        Total system CPU load as a fraction (0.0–1.0+).
    lavalink_load : float
        CPU load used specifically by Lavalink (0.0–1.0+).
    """

    __slots__ = ("cores", "lavalink_load", "system_load")

    def __init__(self, payload: CPU) -> None:
        self.cores: int = payload["cores"]
        self.system_load: float = payload["systemLoad"]
        self.lavalink_load: float = payload["lavalinkLoad"]

    def __repr__(self) -> str:
        return (
            f"<CPUStats cores={self.cores} "
            f"system={self.system_load:.2%} "
            f"lavalink={self.lavalink_load:.2%}>"
        )


class MemoryStats:
    """Memory statistics reported by the Lavalink node.

    Attributes
    ----------
    free : int
        Bytes of free memory.
    used : int
        Bytes of used memory.
    allocated : int
        Bytes of allocated memory.
    reservable : int
        Maximum reservable bytes (set by ``-Xmx`` in the JVM).
    """

    __slots__ = ("allocated", "free", "reservable", "used")

    def __init__(self, payload: Memory) -> None:
        self.free: int = payload["free"]
        self.used: int = payload["used"]
        self.allocated: int = payload["allocated"]
        self.reservable: int = payload["reservable"]

    @property
    def usage_ratio(self) -> float:
        """Current memory usage as a fraction of :attr:`reservable` (0.0–1.0)."""
        if self.reservable == 0:
            return 0.0
        return self.used / self.reservable

    def __repr__(self) -> str:
        return (
            f"<MemoryStats used={self.used // 1024 // 1024}MB "
            f"/ {self.reservable // 1024 // 1024}MB "
            f"({self.usage_ratio:.1%})>"
        )


class FrameStats:
    """Audio frame statistics reported by the Lavalink node.

    These are per-minute averages.

    Attributes
    ----------
    sent : int
        Number of audio frames sent.
    nulled : int
        Number of frames filled with silence (no audio data available).
    deficit : int
        Number of frames that arrived too late to be sent.
    """

    __slots__ = ("deficit", "nulled", "sent")

    def __init__(self, payload: FrameStatsPayload) -> None:
        self.sent: int = payload["sent"]
        self.nulled: int = payload["nulled"]
        self.deficit: int = payload["deficit"]

    def __repr__(self) -> str:
        return (
            f"<FrameStats sent={self.sent} "
            f"nulled={self.nulled} "
            f"deficit={self.deficit}>"
        )


class NodeStats:
    r"""All statistics for a Lavalink node.

    Received periodically via the WebSocket ``stats`` op.

    Attributes
    ----------
    player_count : int
        Total number of players on this node.
    playing_player_count : int
        Number of currently playing players.
    uptime : :class:`datetime.timedelta`
        How long the Lavalink server has been running.
    memory : :class:`MemoryStats`
        Memory statistics.
    cpu : :class:`CPUStats`
        CPU statistics.
    frame_stats : :class:`FrameStats` or None
        Per-minute frame statistics, or ``None`` if unavailable.
    """

    __slots__ = (
        "cpu",
        "frame_stats",
        "memory",
        "player_count",
        "playing_player_count",
        "uptime",
    )

    def __init__(self, data: Stats) -> None:
        self.player_count: int = data["players"]
        self.playing_player_count: int = data["playingPlayers"]
        self.uptime: timedelta = timedelta(milliseconds=data["uptime"])
        self.memory: MemoryStats = MemoryStats(data["memory"])
        self.cpu: CPUStats = CPUStats(data["cpu"])
        self.frame_stats: Optional[FrameStats] = (
            FrameStats(data["frameStats"])
            if data.get("frameStats") is not None
            else None
        )

    def __repr__(self) -> str:
        return (
            f"<NodeStats players={self.player_count} "
            f"playing={self.playing_player_count} "
            f"uptime={self.uptime}>"
        )
