# SPDX-License-Identifier: MIT
"""Events dispatched by WaveCord nodes and players."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic

from .track import Track
from .type_variables import ClientT

if TYPE_CHECKING:
    from .player import Player
    from .typings import EventPayload

__all__ = (
    "WavecordEvent",
    "TrackStartEvent",
    "TrackEndEvent",
    "TrackExceptionEvent",
    "TrackStuckEvent",
    "WebSocketClosedEvent",
)


class WavecordEvent(Generic[ClientT]):
    """Base class for all WaveCord player events.

    Attributes
    ----------
    player : :class:`~wavecord.Player`
        The player the event occurred on.
    """

    __slots__ = ("player",)

    def __init__(self, *, player: Player[ClientT]) -> None:
        self.player: Player[ClientT] = player


class TrackStartEvent(WavecordEvent[ClientT]):
    """Dispatched when a track starts playing.

    Attributes
    ----------
    player : :class:`~wavecord.Player`
    track : :class:`~wavecord.Track`
        The track that started playing.
    """

    __slots__ = ("track",)

    def __init__(self, *, player: Player[ClientT], track: Track) -> None:
        super().__init__(player=player)
        self.track: Track = track

    def __repr__(self) -> str:
        return f"<TrackStartEvent track={self.track!r}>"


class TrackEndEvent(WavecordEvent[ClientT]):
    """Dispatched when a track finishes or is stopped.

    Attributes
    ----------
    player : :class:`~wavecord.Player`
    track : :class:`~wavecord.Track`
        The track that ended.
    reason : str
        The end reason from Lavalink.
        Common values: ``finished``, ``loadFailed``, ``stopped``,
        ``replaced``, ``cleanup``.
    may_start_next : bool
        Whether it is appropriate to start the next queued track.
        This is ``False`` when the reason is ``replaced`` or ``cleanup``.
    """

    __slots__ = ("may_start_next", "reason", "track")

    _MAY_START_NEXT = frozenset({"finished", "loadFailed"})

    def __init__(
        self,
        *,
        player: Player[ClientT],
        track: Track,
        payload: EventPayload,
    ) -> None:
        super().__init__(player=player)
        self.track: Track = track
        self.reason: str = payload.get("reason", "finished")
        self.may_start_next: bool = self.reason in self._MAY_START_NEXT

    def __repr__(self) -> str:
        return (
            f"<TrackEndEvent track={self.track!r} "
            f"reason={self.reason!r} "
            f"may_start_next={self.may_start_next}>"
        )


class TrackExceptionEvent(WavecordEvent[ClientT]):
    """Dispatched when an exception occurs during track playback.

    Attributes
    ----------
    player : :class:`~wavecord.Player`
    track : :class:`~wavecord.Track`
        The track that caused the exception.
    message : str
        The human-readable error message.
    severity : str
        Lavalink severity: ``common``, ``suspicious``, or ``fault``.
    cause : str
        The root cause string from Lavalink.
    """

    __slots__ = ("cause", "message", "severity", "track")

    def __init__(
        self,
        *,
        player: Player[ClientT],
        track: Track,
        payload: EventPayload,
    ) -> None:
        super().__init__(player=player)
        self.track: Track = track
        exc = payload.get("exception") or {}
        self.message: str = exc.get("message", "")
        self.severity: str = exc.get("severity", "fault")
        self.cause: str = exc.get("cause", "")

    def __repr__(self) -> str:
        return (
            f"<TrackExceptionEvent track={self.track!r} "
            f"severity={self.severity!r} "
            f"message={self.message!r}>"
        )


class TrackStuckEvent(WavecordEvent[ClientT]):
    """Dispatched when Lavalink detects that a track is stuck.

    Attributes
    ----------
    player : :class:`~wavecord.Player`
    track : :class:`~wavecord.Track`
        The track that got stuck.
    threshold_ms : int
        How long the track was stuck before Lavalink gave up, in milliseconds.
    """

    __slots__ = ("threshold_ms", "track")

    def __init__(
        self,
        *,
        player: Player[ClientT],
        track: Track,
        payload: EventPayload,
    ) -> None:
        super().__init__(player=player)
        self.track: Track = track
        self.threshold_ms: int = payload.get("thresholdMs", 0)

    def __repr__(self) -> str:
        return (
            f"<TrackStuckEvent track={self.track!r} threshold_ms={self.threshold_ms}>"
        )


class WebSocketClosedEvent(WavecordEvent[ClientT]):
    """Dispatched when Discord closes the voice WebSocket connection.

    Attributes
    ----------
    player : :class:`~wavecord.Player`
    code : int
        The RFC 6455 WebSocket close code.
    reason : str
        The close reason string.
    by_remote : bool
        Whether Discord (the remote) initiated the close.
    """

    __slots__ = ("by_remote", "code", "reason")

    def __init__(
        self,
        *,
        player: Player[ClientT],
        payload: EventPayload,
    ) -> None:
        super().__init__(player=player)
        self.code: int = payload.get("code", 0)
        self.reason: str = payload.get("reason", "")
        self.by_remote: bool = payload.get("byRemote", False)

    def __repr__(self) -> str:
        return (
            f"<WebSocketClosedEvent code={self.code} "
            f"reason={self.reason!r} "
            f"by_remote={self.by_remote}>"
        )
