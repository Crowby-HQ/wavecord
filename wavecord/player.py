# SPDX-License-Identifier: MIT
"""Player - controls audio playback for a single Discord guild."""

from __future__ import annotations

import asyncio
import warnings
from asyncio import Event
from collections import OrderedDict
from functools import reduce
from logging import getLogger
from operator import or_
from time import time
from typing import TYPE_CHECKING, Any, Generic, cast

from .__libraries import (
    MISSING,
    GuildChannel,
    StageChannel,
    VoiceChannel,
    VoiceProtocol,
)
from .errors import NoNodesAvailable, PlayerNotConnected
from .events import (
    TrackEndEvent,
    TrackExceptionEvent,
    TrackStartEvent,
    TrackStuckEvent,
    WebSocketClosedEvent,
)
from .filter import Filter
from .pool import NodePool
from .search_type import SearchType
from .track import Track
from .type_variables import ClientT
from .typings import TrackWithInfo

if TYPE_CHECKING:
    from .__libraries import (
        Connectable,
        Guild,
        GuildVoiceStatePayload,
        VoiceServerUpdatePayload,
    )
    from .node import Node
    from .playlist import Playlist
    from .typings import EventPayload, PlayerUpdateState

_log = getLogger(__name__)
__all__ = ("Player",)


class Player(VoiceProtocol, Generic[ClientT]):
    """Controls Lavalink audio playback for a single Discord guild.

    .. note::

        Do not instantiate this directly. Pass this class as the ``cls``
        argument to your channel's ``connect()`` method:

        .. code-block:: python

            player = await voice_channel.connect(cls=Player)

    Parameters
    ----------
    client : ClientT
        Your Discord client.
    channel : Connectable
        The voice channel to connect to.
    node : :class:`~wavecord.Node` or None
        A specific node to use. If ``None``, the best available node is chosen.

    Attributes
    ----------
    client : ClientT
    channel : Connectable
        The current voice channel.
    guild : Guild
        The guild this player is in.
    endpoint : str or None
        The Discord voice server endpoint, set after voice server update.
    """

    def __init__(
        self,
        client: ClientT,
        channel: Connectable,
        *,
        node: Node[ClientT] | None = None,
    ) -> None:
        self.client: ClientT = client
        self.channel: Connectable = channel

        if not isinstance(self.channel, GuildChannel):
            msg = "Voice channel must be a GuildChannel."
            raise TypeError(msg)

        self.guild: Guild = self.channel.guild
        self.endpoint: str | None = None

        self._node: Node[ClientT] | None = node

        self._guild_id: int = self.guild.id
        self._session_id: str | None = None
        self._server_state: VoiceServerUpdatePayload | None = None

        self._connected: bool = False
        self._position: int = 0
        self._last_update: int = 0
        self._ping: int = -1
        self._current: Track | None = None
        self._last_track: Track | None = None
        self._paused: bool = False
        self._volume: int = 100

        # Keyed by label — allows stacking multiple named filters.
        self._filters: OrderedDict[str, Filter] = OrderedDict()

        self._voice_state_update_event: Event = Event()
        self._voice_server_update_event: Event = Event()
        self._node_player_ready_event: Event = Event()

    # Properties
    @property
    def node(self) -> Node[ClientT]:
        """The :class:`~wavecord.Node` handling this player.

        Falls back to a random node if the player was not yet assigned one.
        """
        if self._node is None:
            _log.warning(
                "Player for guild %d has no node — using a random one.",
                self._guild_id,
            )
            return NodePool[ClientT].get_random_node()
        return self._node

    @property
    def connected(self) -> bool:
        """Whether the player is connected to a voice channel."""
        return self._connected

    @property
    def paused(self) -> bool:
        """Whether playback is currently paused."""
        return self._paused

    @property
    def current(self) -> Track | None:
        """The currently playing :class:`~wavecord.Track`, or ``None``."""
        return self._current

    @property
    def position(self) -> int:
        """Estimated playback position in milliseconds.

        Interpolated between WebSocket updates using wall-clock time.
        """
        pos = self._position
        if self._connected and self._current is not None:
            pos = min(
                self._current.length,
                pos + int(time() * 1000 - self._last_update),
            )
        return pos

    @property
    def ping(self) -> int:
        """Voice server round-trip latency in milliseconds. ``-1`` if unknown."""
        return self._ping

    @property
    def volume(self) -> int:
        """Current volume (0–1000)."""
        return self._volume

    # State helpers (called by Node)
    def set_state(self, state: Any) -> None:  # type: ignore[override]
        """Restore player state after a session resume.

        .. note::
            This is called internally and should not be needed in user code.
        """
        self._session_id = state["voice"]["sessionId"]
        self._ping = state["voice"].get("ping", -1)
        self._current = (
            Track.from_data_with_info(state["track"]) if state.get("track") else None
        )
        self._filters = OrderedDict(
            {"RESUME": Filter.from_payload(state.get("filters", {}))}
        )
        self._paused = state.get("paused", False)
        self._volume = state.get("volume", 100)
        self._server_state = {
            "token": state["voice"]["token"],
            "endpoint": state["voice"]["endpoint"],
            "guild_id": self._guild_id,
        }
        if state.get("track"):
            self._position = state["track"]["info"].get("position", 0)

    def update_state(self, state: PlayerUpdateState) -> None:
        """Apply a ``playerUpdate`` payload from the WebSocket.

        .. note::
            Called internally by the node listener.
        """
        if not self._node_player_ready_event.is_set():
            self._node_player_ready_event.set()

        self._last_update = state.get("time", 0)
        self._position = state.get("position", 0)
        self._connected = state.get("connected", False)
        self._ping = state.get("ping", -1)

    def dispatch_event(self, data: EventPayload) -> None:
        """Dispatch a Lavalink event to the Discord client.

        .. note::
            Called internally by the node listener.
        """
        event_type = data.get("type")

        if event_type == "TrackStartEvent":
            track = (
                self._current
                if self.node.version == 3
                else Track.from_data_with_info(cast(TrackWithInfo, data.get("track")))
            )
            if track is None:
                _log.error("TrackStartEvent received but no track found — discarding.")
                return
            event = TrackStartEvent(player=self, track=track)
            self.client.dispatch("track_start", event)
            self._last_track = track

        elif event_type == "TrackEndEvent":
            track = (
                self._last_track
                if self.node.version == 3
                else Track.from_data_with_info(cast(TrackWithInfo, data.get("track")))
            )
            if track is None:
                _log.error("TrackEndEvent received but no track found — discarding.")
                return
            event = TrackEndEvent(player=self, track=track, payload=data)
            self.client.dispatch("track_end", event)
            if data.get("reason") != "REPLACED":
                self._current = None

        elif event_type == "TrackExceptionEvent":
            track = (
                self._current
                if self.node.version == 3
                else Track.from_data_with_info(cast(TrackWithInfo, data.get("track")))
            )
            if track is None:
                _log.error("TrackExceptionEvent received but no track found.")
                return
            event = TrackExceptionEvent(player=self, track=track, payload=data)
            self.client.dispatch("track_exception", event)

        elif event_type == "TrackStuckEvent":
            track = (
                self._current
                if self.node.version == 3
                else Track.from_data_with_info(cast(TrackWithInfo, data.get("track")))
            )
            if track is None:
                _log.error("TrackStuckEvent received but no track found.")
                return
            event = TrackStuckEvent(player=self, track=track, payload=data)
            self.client.dispatch("track_stuck", event)

        elif event_type == "WebSocketClosedEvent":
            event = WebSocketClosedEvent(player=self, payload=data)
            self.client.dispatch("websocket_closed", event)

        else:
            _log.warning("Unknown event type %r.", event_type)

    # VoiceProtocol interface
    async def on_voice_state_update(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, data: GuildVoiceStatePayload
    ) -> None:
        """Handle a Discord voice state update.

        .. note::
            Called automatically by your Discord library.
        """
        before = self._session_id
        self._session_id = data["session_id"]

        channel_id = data.get("channel_id")
        if channel_id is None:
            await self.disconnect(force=True)
            return

        channel = self.guild.get_channel(int(channel_id))
        if not isinstance(channel, (VoiceChannel, StageChannel)):
            msg = "Received voice state update for an unrecognised channel type."
            raise TypeError(msg)

        self.channel = channel

        if self._session_id != before:
            await self._dispatch_player_update()

        self._voice_state_update_event.set()

    async def on_voice_server_update(self, data: VoiceServerUpdatePayload) -> None:
        """Handle a Discord voice server update.

        .. note::
            Called automatically by your Discord library.
        """
        if (
            self._node is None
            or self._server_state is None
            or self._server_state.get("endpoint") != data.get("endpoint")
        ):
            self._node = NodePool[ClientT].get_node(
                guild_id=data["guild_id"], endpoint=data.get("endpoint")
            )

        self._node.add_player(self._guild_id, self)
        self._guild_id = int(data["guild_id"])
        self.endpoint = data.get("endpoint")
        self._server_state = data

        await self._dispatch_player_update()
        self._voice_server_update_event.set()

    async def _dispatch_player_update(self) -> None:
        if self._node is None or self._session_id is None or self._server_state is None:
            return
        if not isinstance(self.channel, (VoiceChannel, StageChannel)):
            return

        await self._node.voice_update(
            guild_id=self._guild_id,
            session_id=self._session_id,
            data=self._server_state,
            channel_id=int(self.channel.id),
        )

    async def connect(
        self,
        *,
        timeout: float,
        reconnect: bool,
        self_mute: bool = False,
        self_deaf: bool = False,
    ) -> None:
        """Connect to the voice channel.

        Called automatically by your Discord library's ``connect()`` method.
        """
        if not isinstance(self.channel, (VoiceChannel, StageChannel)):
            msg = "Voice channel must be a VoiceChannel or StageChannel."
            raise TypeError(msg)

        if not NodePool.nodes:  # pyright: ignore
            self.cleanup()
            raise NoNodesAvailable

        await self.channel.guild.change_voice_state(
            channel=self.channel, self_mute=self_mute, self_deaf=self_deaf
        )

        futures = [
            self._voice_state_update_event.wait(),
            self._voice_server_update_event.wait(),
            self._node_player_ready_event.wait(),
        ]
        done, pending = await asyncio.wait(
            [asyncio.ensure_future(f) for f in futures],
            timeout=timeout,
            return_when=asyncio.ALL_COMPLETED,
        )
        if pending:
            await self.disconnect(force=True)
            raise asyncio.TimeoutError

        self._connected = True

    async def disconnect(self, *, force: bool = False) -> None:
        """Disconnect from the voice channel and destroy the Lavalink player.

        Parameters
        ----------
        force : bool
            Disconnect even if the player thinks it is not connected.
        """
        if not self._connected and not force:
            return
        if self.client.is_closed():
            return

        if self._node is not None:
            self._node.remove_player(self.guild.id)
            await self._node.destroy(guild_id=self.guild.id)

        try:
            await self.guild.change_voice_state(channel=None)
        finally:
            self.cleanup()
            self._connected = False

    def cleanup(self) -> None:
        """Reset all internal state. Called on disconnect."""
        self._current = None
        self._position = 0
        self._paused = False
        self._ping = 0
        self._connected = False
        return super().cleanup()

    def is_connected(self) -> bool:
        """Alias for :attr:`connected` (VoiceClient compatibility)."""
        return self._connected

    # Playback controls
    async def update(
        self,
        *,
        track: Track | str | None = MISSING,
        position: int | None = None,
        end_time: int | None = None,
        volume: int | None = None,
        pause: bool | None = None,
        filter: Filter | None = None,
        replace: bool = False,
    ) -> None:
        """Update the player's state on Lavalink.

        Parameters
        ----------
        track : :class:`~wavecord.Track`, str, or None
            Track to start. Pass ``None`` to stop. Pass a string identifier
            to load a track by ID directly (v4 only).
        position : int or None
            Seek position in milliseconds.
        end_time : int or None
            Stop time in milliseconds.
        volume : int or None
            Volume (0–1000).
        pause : bool or None
            Pause or resume.
        filter : :class:`~wavecord.filter.Filter` or None
            Filters to apply.
        replace : bool
            If ``True``, replace the currently playing track.

        Raises
        ------
        PlayerNotConnected
            If the player is not connected.
        """
        if self._node is None or not self._connected:
            raise PlayerNotConnected

        if track is not None and self.node.version == 3:
            if isinstance(track, str):
                msg = (
                    "Lavalink v3 does not support identifier-based loading. "
                    "Load a Track object instead."
                )
                raise TypeError(msg)
            self._current = track

        data = await self._node.update(
            guild_id=self._guild_id,
            track=track,
            position=position,
            end_time=end_time,
            volume=volume,
            pause=pause,
            filter=filter,
            no_replace=not replace,
        )

        if data and data.get("track"):
            self._current = Track.from_data_with_info(data["track"])
        if data:
            self._volume = data.get("volume", self._volume)
            self._paused = data.get("paused", self._paused)

    async def play(
        self,
        track: Track | str,
        /,
        *,
        start_time: int | None = None,
        end_time: int | None = None,
        volume: int | None = None,
        replace: bool = True,
        pause: bool | None = None,
    ) -> None:
        """Play a track.

        Parameters
        ----------
        track : :class:`~wavecord.Track` or str
            The track to play. A string is treated as a direct identifier
            (Lavalink v4 only).
        start_time : int or None
            Start position in milliseconds.
        end_time : int or None
            Stop position in milliseconds.
        volume : int or None
            Initial volume (0–1000).
        replace : bool
            Replace the currently playing track. Default ``True``.
        pause : bool or None
            Start paused.

        Raises
        ------
        PlayerNotConnected
            If the player is not connected.
        """
        await self.update(
            track=track,
            position=start_time,
            end_time=end_time,
            volume=volume,
            replace=replace,
            pause=pause,
        )

    async def stop(self) -> None:
        """Stop the current track.

        Raises
        ------
        PlayerNotConnected
        """
        await self.update(track=None, replace=True)

    async def pause(self, pause: bool = True) -> None:
        """Pause or unpause playback.

        Parameters
        ----------
        pause : bool
            ``True`` to pause, ``False`` to resume. Default ``True``.

        Raises
        ------
        PlayerNotConnected
        """
        await self.update(pause=pause)

    async def resume(self) -> None:
        """Resume playback.

        Raises
        ------
        PlayerNotConnected
        """
        await self.pause(False)

    async def seek(self, position: int, /) -> None:
        """Seek to a position in the current track.

        Parameters
        ----------
        position : int
            Target position in milliseconds.

        Raises
        ------
        PlayerNotConnected
        """
        await self.update(position=position)

    async def set_volume(self, volume: int, /) -> None:
        """Set the player volume.

        Parameters
        ----------
        volume : int
            Volume level from 0 to 1000. 100 is default.

        Raises
        ------
        PlayerNotConnected
        """
        await self.update(volume=volume)

    # Filter management
    async def _apply_filters(self, *, fast_apply: bool = False) -> None:
        combined = reduce(or_, self._filters.values()) if self._filters else Filter()
        await self.update(filter=combined)
        if fast_apply:
            await self.seek(self.position)

    async def add_filter(
        self, filter: Filter, /, *, label: str, fast_apply: bool = False
    ) -> None:
        """Add or replace a named filter.

        Parameters
        ----------
        filter : :class:`~wavecord.filter.Filter`
            The filter to apply.
        label : str
            A unique name for this filter. Used to remove it later.
        fast_apply : bool
            Seek to the current position after applying (clears Lavalink's buffer).

        Raises
        ------
        PlayerNotConnected
        """
        self._filters[label] = filter
        await self._apply_filters(fast_apply=fast_apply)

    async def remove_filter(self, label: str, *, fast_apply: bool = False) -> None:
        """Remove a named filter.

        Parameters
        ----------
        label : str
        fast_apply : bool

        Raises
        ------
        PlayerNotConnected
        ValueError
            If no filter with this label exists.
        """
        self._filters.pop(label)
        await self._apply_filters(fast_apply=fast_apply)

    async def clear_filters(self, *, fast_apply: bool = False) -> None:
        """Remove all active filters.

        Parameters
        ----------
        fast_apply : bool

        Raises
        ------
        PlayerNotConnected
        """
        self._filters.clear()
        await self._apply_filters(fast_apply=fast_apply)

    async def has_filter(self, label: str) -> bool:
        """Check whether a filter with *label* is active.

        Parameters
        ----------
        label : str

        Returns
        -------
        bool
        """
        return label in self._filters

    # Track search
    async def fetch_tracks(
        self,
        query: str,
        search_type: SearchType | str = SearchType.YOUTUBE,
    ) -> list[Track] | Playlist | None:
        r"""Search for tracks or load a URL.

        Parameters
        ----------
        query : str
            A search term or direct URL.
        search_type : :class:`~wavecord.SearchType` or str
            The search source when *query* is not a URL.

        Returns
        -------
        list[:class:`~wavecord.Track`]
            Search results or a single loaded track.
        :class:`~wavecord.Playlist`
            A loaded playlist.
        None
            Nothing found.

        Notes
        -----
        Uses a random node as fallback if the player is not yet connected.
        """
        raw_type = (
            search_type.value if isinstance(search_type, SearchType) else search_type
        )
        return await self.node.fetch_tracks(query, search_type=raw_type)

    # Node transfer
    async def transfer_to(self, node: Node[ClientT]) -> None:
        """Move this player to a different Lavalink node.

        All state (position, filters, volume, current track) is preserved.

        Parameters
        ----------
        node : :class:`~wavecord.Node`
            The target node.

        Raises
        ------
        PlayerNotConnected
        """
        if self._node is None:
            raise PlayerNotConnected

        if self._node is node:
            return

        state = await self._node.fetch_player(self.guild.id)  # type: ignore[attr-defined]

        self._node.remove_player(self.guild.id)
        old_node = self._node
        self._node = node
        self._node.add_player(self.guild.id, self)

        if self._session_id is None or self._server_state is None:
            msg = "Cannot transfer player: missing voice session data."
            raise RuntimeError(msg)

        if not isinstance(self.channel, (VoiceChannel, StageChannel)):
            _log.warning(
                "Cannot transfer: channel type is not VoiceChannel/StageChannel."
            )
            return

        await self._node.voice_update(
            guild_id=self._guild_id,
            session_id=self._session_id,
            data=self._server_state,
            channel_id=int(self.channel.id),
        )

        self._connected = True
        combined = reduce(or_, self._filters.values()) if self._filters else Filter()

        await self.update(
            track=self._current,
            position=self.position,
            volume=state.get("volume"),
            pause=self._paused,
            filter=combined,
            replace=True,
        )

        await old_node.destroy(guild_id=self.guild.id)

    # Deprecated
    async def destroy(self) -> None:
        warnings.warn(
            "Player.destroy() is deprecated and will be removed in a future release. "
            "Use Player.disconnect() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        await self.disconnect()

    # Dunder
    def __repr__(self) -> str:
        return (
            f"<Player guild_id={self._guild_id} "
            f"connected={self._connected} "
            f"paused={self._paused} "
            f"current={self._current!r}>"
        )
