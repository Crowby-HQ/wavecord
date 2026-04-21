# SPDX-License-Identifier: MIT
# pyright: reportImportCycles=false
"""Node - manages a single Lavalink server connection."""

from __future__ import annotations

import re
import warnings
from asyncio import Event, TimeoutError, create_task, gather, sleep, wait_for
from logging import getLogger
from traceback import print_exc
from typing import TYPE_CHECKING, Any, Generic, Sequence, cast

import aiohttp
import yarl

from .__libraries import MISSING, ExponentialBackoff, dumps, loads
from .errors import (
    HTTPBadRequest,
    HTTPException,
    HTTPNotFound,
    HTTPUnauthorized,
    NodeAlreadyConnected,
    TrackLoadException,
)
from .ip import (
    BalancingIPRoutePlannerStatus,
    NanoIPRoutePlannerStatus,
    RotatingIPRoutePlannerStatus,
    RotatingNanoIPRoutePlannerStatus,
)
from .playlist import Playlist
from .plugin import Plugin
from .region import Group, Region, VoiceRegion
from .stats import NodeStats
from .track import Track
from .type_variables import ClientT
from .typings import (
    BalancingIPRouteDetails,
    NanoIPRouteDetails,
    RotatingIPRouteDetails,
    RotatingNanoIPRouteDetails,
    TrackWithInfo,
)
from .warnings import UnknownVersionWarning, UnsupportedVersionWarning

if TYPE_CHECKING:
    from asyncio import Task

    from aiohttp import ClientWebSocketResponse

    from .__libraries import VoiceServerUpdatePayload
    from .filter import Filter
    from .ip import RoutePlannerStatus
    from .player import Player
    from .typings import (
        Coro,
        EventPayload,
        IncomingMessage,
        OutgoingMessage,
        PluginData,
        RoutePlannerStatus as RoutePlannerStatusPayload,
        TrackLoadingResult,
        UpdatePlayerParams,
        UpdatePlayerPayload,
        UpdateSessionPayload,
    )

_log = getLogger(__name__)
_URL_RE = re.compile(r"https?://")

__all__ = ("Node",)


def _wrap_regions(
    regions: Sequence[Group | Region | VoiceRegion] | None,
) -> list[VoiceRegion] | None:
    r"""Convert mixed region/group inputs into a flat list of :class:`VoiceRegion`.

    Parameters
    ----------
    regions:
        A sequence of :class:`Group`, :class:`Region`, or :class:`VoiceRegion`
        instances, or ``None``.

    Returns
    -------
    list[:class:`VoiceRegion`] or None
    """
    if not regions:
        return None

    result: list[VoiceRegion] = []

    for item in regions:
        if isinstance(item, Group):
            for region in item.value:
                result.extend(region.value)
        elif isinstance(item, Region):
            result.extend(item.value)
        elif isinstance(item, VoiceRegion): # pyright: ignore[reportUnnecessaryIsInstance]
            result.append(item)
        else:
            msg = f"Expected Group, Region, or VoiceRegion — got {type(item)!r}."
            raise TypeError(msg)

    return result


class Node(Generic[ClientT]):
    r"""Represents a single Lavalink server.

    .. warning::

        Do not instantiate this directly.
        Use :meth:`NodePool.create_node` instead.

    Parameters
    ----------
    host : str
        Hostname of the Lavalink server.
    port : int
        Port of the Lavalink server.
    label : str
        Unique name used to identify this node within the pool.
    password : str
        Server password.
    client : ClientT
        Your Discord client instance.
    secure : bool
        Use HTTPS/WSS when ``True``.
    heartbeat : int
        WebSocket heartbeat interval in seconds. Default ``30``.
    timeout : float
        Seconds to wait for the node to become ready. Default ``10``.
    session : :class:`aiohttp.ClientSession` or None
        An existing aiohttp session to reuse, or ``None`` to create one.
    resume_key : str or None
        Key used to resume a Lavalink v3 session.
    regions : sequence of Group/Region/VoiceRegion, or None
        Voice regions this node should be preferred for.
    shard_ids : sequence of int, or None
        Shard IDs this node should handle.
    resuming_session_id : str or None
        Lavalink v4 session ID to resume.

    Attributes
    ----------
    regions : list[:class:`VoiceRegion`] or None
    shard_ids : sequence[int] or None
    """

    __slots__ = (
        "__password",
        "__session",
        "_available",
        "_checked_version",
        "_client",
        "_connect_task",
        "_event_queue",
        "_heartbeat",
        "_host",
        "_label",
        "_msg_tasks",
        "_players",
        "_port",
        "_ready",
        "_rest_uri",
        "_resume_key",
        "_resuming_session_id",
        "_secure",
        "_session_id",
        "_stats",
        "_timeout",
        "_version",
        "_ws",
        "_ws_task",
        "_ws_uri",
        "regions",
        "shard_ids",
    )

    def __init__(
        self,
        *,
        host: str,
        port: int,
        label: str,
        password: str,
        client: ClientT,
        secure: bool = False,
        heartbeat: int = 30,
        timeout: float = 10,
        session: aiohttp.ClientSession | None = None,
        resume_key: str | None = None,
        regions: Sequence[Group | Region | VoiceRegion] | None = None,
        shard_ids: Sequence[int] | None = None,
        resuming_session_id: str | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._label = label
        self.__password = password
        self._client = client
        self._secure = secure
        self._heartbeat = heartbeat
        self._timeout = timeout
        self.__session: aiohttp.ClientSession | None = session
        self.shard_ids: Sequence[int] | None = shard_ids
        self.regions: list[VoiceRegion] | None = _wrap_regions(regions)

        self._rest_uri = yarl.URL.build(
            scheme=f"http{'s' * secure}", host=host, port=port
        )
        self._ws_uri = yarl.URL.build(
            scheme=f"ws{'s' * secure}", host=host, port=port
        )
        self._resume_key: str = resume_key or f"{host}:{port}:{label}"
        self._resuming_session_id: str = resuming_session_id or ""

        self._ws: ClientWebSocketResponse | None = None
        self._ws_task: Task[None] | None = None
        self._connect_task: Task[None] | None = None
        self._msg_tasks: set[Task[None]] = set()

        self._available = False
        self._ready: Event = Event()
        self._event_queue: Event = Event()

        self._players: dict[int, Player[ClientT]] = {}
        self._stats: NodeStats | None = None
        self._session_id: str | None = None

        self._checked_version = False
        self._version: int = 3

    # Properties
    @property
    def host(self) -> str:
        """The Lavalink server host."""
        return self._host

    @property
    def port(self) -> int:
        """The Lavalink server port."""
        return self._port

    @property
    def label(self) -> str:
        """The unique label for this node."""
        return self._label

    @property
    def client(self) -> ClientT:
        """The Discord client this node belongs to."""
        return self._client

    @property
    def secure(self) -> bool:
        """Whether this node uses a secure (HTTPS/WSS) connection."""
        return self._secure

    @property
    def available(self) -> bool:
        """Whether this node is connected and ready to handle requests."""
        return self._available

    @property
    def session_id(self) -> str | None:
        """The current Lavalink session ID, or ``None`` if not connected."""
        return self._session_id

    @property
    def version(self) -> int:
        """The major Lavalink version (3 or 4)."""
        return self._version

    @property
    def stats(self) -> NodeStats | None:
        """The most recent :class:`~wavecord.NodeStats`, or ``None`` if unavailable."""
        return self._stats

    @property
    def players(self) -> list[Player[ClientT]]:
        """All players currently managed by this node."""
        return list(self._players.values())

    @property
    def weight(self) -> float:
        """Computed load score used by the :attr:`~wavecord.Strategy.USAGE` strategy.

        A lower value means less load. Nodes with no stats return a very high
        value so they are only chosen when nothing else is available.

        The score is calculated from:

        - Number of playing players
        - CPU load (exponential)
        - Nulled / deficit audio frames (exponential)
        - Memory pressure (exponential near capacity)
        """
        if self._stats is None:
            return 6.63e34 # enormous sentinel - treat as worst case

        s = self._stats

        players = s.playing_player_count
        cpu = 1.05 ** (100 * (s.cpu.system_load / max(s.cpu.cores, 1))) * 10 - 10

        fs = s.frame_stats
        if fs is None:
            null = deficit = 0.0
        else:
            null = 1.03 ** (fs.nulled / 6) * 600 - 600
            deficit = 1.03 ** (fs.deficit / 6) * 600 - 600

        mem = s.memory
        mem_score = (
            max(10 ** (100 * mem.usage_ratio - 96), 1) - 1
            if mem.reservable > 0
            else 0.0
        )

        return players + cpu + null + deficit + mem_score

    # Player helpers
    def get_player(self, guild_id: int) -> Player[ClientT] | None:
        r"""Return the player for a guild, or ``None``.

        Parameters
        ----------
        guild_id : int

        Returns
        -------
        :class:`~wavecord.Player` or None
        """
        return self._players.get(guild_id)

    def add_player(self, guild_id: int, player: Player[ClientT]) -> None:
        """Register a player with this node.

        Parameters
        ----------
        guild_id : int
        player : :class:`~wavecord.Player`
        """
        self._players[guild_id] = player

    def remove_player(self, guild_id: int) -> None:
        """Unregister a player from this node.

        .. note::
            This only removes the reference; it does **not** disconnect the
            player from voice or destroy it on Lavalink.

        Parameters
        ----------
        guild_id : int
        """
        self._players.pop(guild_id, None)

    # Connection lifecycle
    async def _create_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(json_serialize=dumps)

    async def _check_version(self) -> int:
        """Fetch and validate the Lavalink server version.

        Returns
        -------
        int
            The major version number (3 or 4).

        Raises
        ------
        RuntimeError
            If the version is unsupported (< 3.7 or >= 5).
        """
        if self._checked_version:
            return self._version

        if self.__session is None:
            self.__session = await self._create_session()

        async with self.__session.get(
            self._rest_uri / "version",
            headers={"Authorization": self.__password},
        ) as resp:
            version_str = await resp.text()

        try:
            major_s, minor_s, *_ = version_str.split(".", maxsplit=2)
            major, minor = int(major_s), int(minor_s)
        except (ValueError, AttributeError):
            if version_str.endswith("-SNAPSHOT"):
                major, minor = 4, 0
            else:
                major, minor = 3, 7
                warnings.warn(UnknownVersionWarning.message, UnknownVersionWarning, stacklevel=4)
        else:
            if major not in (3, 4) or (major == 3 and minor < 7):
                msg = (
                    f"Unsupported Lavalink version {version_str!r}. "
                    "WaveCord requires 3.7.x or 4.x.x."
                )
                raise RuntimeError(msg)

            if (major == 3 and minor > 7) or (major == 4 and minor > 0):
                warnings.warn(
                    UnsupportedVersionWarning.message,
                    UnsupportedVersionWarning,
                    stacklevel=4,
                )

        self._rest_uri = self._rest_uri / f"v{major}"
        self._ws_uri = self._ws_uri / f"v{major}/websocket"
        self._version = major
        self._checked_version = True
        return major

    async def _connect_to_websocket(
        self, headers: dict[str, str], session: aiohttp.ClientSession
    ) -> None:
        self._ws = await session.ws_connect( # pyright: ignore
            self._ws_uri,
            timeout=self._timeout,
            heartbeat=self._heartbeat,
            headers=headers,
        )

    async def connect(
        self,
        *,
        backoff: ExponentialBackoff | None = None,
        player_cls: type[Player[ClientT]] | None = None,
    ) -> None:
        """Connect to the Lavalink WebSocket.

        Parameters
        ----------
        backoff : :class:`ExponentialBackoff` or None
            Backoff strategy for reconnection attempts.
        player_cls : type[:class:`~wavecord.Player`] or None
            Player class to use when syncing resumed players.

        Raises
        ------
        NodeAlreadyConnected
            If the node is already connected.
        asyncio.TimeoutError
            If the node does not become ready within :attr:`timeout` seconds.
        """
        if self._ws is not None:
            raise NodeAlreadyConnected

        _log.info("Waiting for client to be ready…", extra={"label": self._label})
        await self._client.wait_until_ready()

        if self.__session is None:
            self.__session = await self._create_session()

        _log.debug("Checking Lavalink version…", extra={"label": self._label})
        version = await self._check_version()

        headers: dict[str, str] = {
            "Authorization": self.__password,
            "User-Id": str(self._client.user.id), # type: ignore[union-attr]
            "Client-Name": "WaveCord/1.0.0",
        }

        if version == 3:
            headers["Resume-Key"] = self._resume_key
        else:
            headers["Session-Id"] = self._resuming_session_id

        _log.info(
            "Connecting to Lavalink at %s…",
            self._rest_uri,
            extra={"label": self._label},
        )

        try:
            await self._connect_to_websocket(headers=headers, session=self.__session)
        except Exception as exc:
            _log.error(
                "Failed to connect to %s: %s",
                self._rest_uri,
                exc,
                extra={"label": self._label},
            )
            print_exc()
            backoff = backoff or ExponentialBackoff()
            delay = backoff.delay()
            _log.info("Retrying in %.2f s…", delay, extra={"label": self._label})
            await sleep(delay)
            task = create_task(self.connect(backoff=backoff))
            self._connect_task = task
            task.add_done_callback(lambda _: setattr(self, "_connect_task", None))
            return

        _log.info("WebSocket connected.", extra={"label": self._label})
        self._ws_task = create_task(
            self._ws_listener(), name=f"wavecord-node-{self._label}"
        )

        try:
            await wait_for(self._ready.wait(), timeout=self._timeout)
        except TimeoutError:
            _log.error("Timed out waiting for node ready.", extra={"label": self._label})
            raise

        _log.info("Node '%s' is ready.", self._label, extra={"label": self._label})
        await self.sync_players(player_cls=player_cls)
        self._event_queue.set()
        self._available = True
        self._client.dispatch("node_ready", self)

    async def close(self) -> None:
        """Gracefully close the WebSocket and HTTP session."""
        if self._ws is not None:
            await self._ws.close()
            self._ws = None

        if self.__session is not None:
            await self.__session.close()
            self.__session = None

        if self._ws_task is not None:
            self._ws_task.cancel()
            self._ws_task = None

        if self._connect_task is not None:
            self._connect_task.cancel()
            self._connect_task = None

        _log.info("Node '%s' closed.", self._label, extra={"label": self._label})
        self._cleanup()

    def _cleanup(self) -> None:
        self._available = False
        self._ws = None
        self._ws_task = None
        self._connect_task = None
        self.__session = None
        self._ready.clear()
        self._event_queue.clear()

    # WebSocket listener
    async def _ws_listener(self) -> None:
        if self._ws is None:
            msg = "WebSocket is not connected."
            raise RuntimeError(msg)

        backoff = ExponentialBackoff()

        while True:
            msg = await self._ws.receive()
            _type: aiohttp.WSMsgType = msg.type # pyright: ignore

            if _type is aiohttp.WSMsgType.CLOSED:
                self._available = False
                self._client.dispatch("node_unavailable", self)
                close_code = self._ws.close_code
                self._ready.clear()
                self._ws = None

                wait_time = backoff.delay()
                _log.warning(
                    "WS closed (code=%s) on node '%s'. Reconnecting in %.2fs…",
                    close_code,
                    self._label,
                    wait_time,
                    extra={"label": self._label},
                )
                await sleep(wait_time)
                task = create_task(self.connect(backoff=backoff))
                self._connect_task = task
                task.add_done_callback(lambda _: setattr(self, "_connect_task", None))
                return
            else:
                task = create_task(self._handle_msg(msg.json(loads=loads)))
                self._msg_tasks.add(task)
                task.add_done_callback(self._msg_tasks.discard)

    async def _handle_msg(self, data: IncomingMessage) -> None:
        _log.debug("Received op=%r from node '%s'", data.get("op"), self._label)

        if data["op"] != "ready":
            await self._event_queue.wait()

        op = data["op"]

        if op == "playerUpdate":
            guild_id = int(data["guildId"])
            player = self.get_player(guild_id)
            if player is None:
                if data.get("state", {}).get("connected"):
                    _log.error(
                        "playerUpdate for unknown guild %s — discarding.",
                        guild_id,
                    )
                return
            player.update_state(data["state"])

        elif op == "stats":
            self._stats = NodeStats(data) # type: ignore[arg-type]
            self._client.dispatch("node_stats", self)

        elif op == "event":
            await self._handle_event(data) # type: ignore[arg-type]

        elif op == "ready":
            resumed = data["resumed"]
            session_id = data["sessionId"]
            self._session_id = session_id

            if resumed:
                _log.info(
                    "Session resumed (id=%s).", session_id, extra={"label": self._label}
                )
            else:
                await self.configure_resuming()

            self._ready.set()

        else:
            _log.warning("Unknown op %r from node '%s'.", op, self._label)

    async def _handle_event(self, data: EventPayload) -> None:
        guild_id = int(data["guildId"])
        player = self.get_player(guild_id)

        if player is None:
            if data.get("type") == "WebSocketClosedEvent":
                guild = self._client.get_guild(guild_id)
                if guild is None:
                    return
                vc = guild.voice_client
                if vc is None:
                    return
                vc = cast("Player[ClientT]", vc)
                if vc.node is not self:
                    return
                _log.debug(
                    "WebSocketClosedEvent for guild %s — cleaning up.", guild_id
                )
                await vc.disconnect(force=True)
                return

            _log.error(
                "Event %r for unknown guild %s — discarding.",
                data.get("type"),
                guild_id,
            )
            return

        player.dispatch_event(data)

    # Voice / session helpers
    def voice_update(
        self,
        guild_id: int,
        session_id: str,
        data: VoiceServerUpdatePayload,
        channel_id: int,
    ) -> Coro[None]:
        """Forward a Discord voice server update to Lavalink.

        Parameters
        ----------
        guild_id : int
        session_id : str
            The **Discord** voice session ID.
        data : VoiceServerUpdatePayload
        channel_id : int
            Required by Lavalink ≥ 4.2.

        Raises
        ------
        ValueError
            If the endpoint in *data* is ``None``.
        """
        if data["endpoint"] is None:
            msg = "Discord did not provide a voice endpoint."
            raise ValueError(msg)

        return self.__request(
            "PATCH",
            f"sessions/{self._session_id}/players/{guild_id}",
            {
                "voice": {
                    "sessionId": session_id,
                    "endpoint": data["endpoint"],
                    "token": data["token"],
                    "channelId": str(channel_id),
                },
            },
        )

    def configure_resuming(self) -> Coro[None]:
        """Send session resuming configuration to Lavalink."""
        if self._version == 3:
            _log.info(
                "Configuring v3 resume with key %s.", self._resume_key,
                extra={"label": self._label},
            )
            payload: UpdateSessionPayload = {
                "resumingKey": self._resume_key,
                "timeout": 60,
            }
        else:
            _log.info(
                "Configuring v4 resume with session %s.", self._session_id,
                extra={"label": self._label},
            )
            payload = {"resuming": True, "timeout": 60}

        return self.__request("PATCH", f"sessions/{self._session_id}", payload)

    def destroy(self, guild_id: int) -> Coro[None]:
        """Send a DELETE request to destroy a player on Lavalink.

        Parameters
        ----------
        guild_id : int
        """
        return self.__request(
            "DELETE", f"sessions/{self._session_id}/players/{guild_id}"
        )

    def update(
        self,
        *,
        guild_id: int,
        track: Track | str | None = MISSING,
        position: int | None = None,
        end_time: int | None = None,
        volume: int | None = None,
        no_replace: bool | None = None,
        pause: bool | None = None,
        filter: Filter | None = None,
    ) -> Coro[Any]:
        """Send a PATCH request to update a player's state.

        Parameters
        ----------
        guild_id : int
        track : :class:`~wavecord.Track`, str, or None
            Track to load. Pass ``None`` to stop playback.
        position : int or None
            Seek position in milliseconds.
        end_time : int or None
            End time in milliseconds.
        volume : int or None
            Volume (0–1000).
        no_replace : bool or None
            Skip the update if a track is already playing.
        pause : bool or None
            Pause or unpause.
        filter : :class:`~wavecord.filter.Filter` or None
            Filters to apply.
        """
        payload: UpdatePlayerPayload = {}

        if track is not MISSING:
            if isinstance(track, Track) or track is None:
                payload["encodedTrack"] = track.id if track is not None else None
            else:
                payload["identifier"] = track

        if position is not None:
            payload["position"] = position
        if end_time is not None:
            payload["endTime"] = end_time
        if volume is not None:
            payload["volume"] = volume
        if pause is not None:
            payload["paused"] = pause
        if filter is not None:
            payload["filters"] = filter.payload

        params: UpdatePlayerParams | None = (
            {"noReplace": str(no_replace)} if no_replace is not None else None
        )

        return self.__request(
            "PATCH",
            f"sessions/{self._session_id}/players/{guild_id}",
            payload,
            params,
        )

    # REST - track loading
    async def fetch_tracks(
        self, query: str, *, search_type: str
    ) -> list[Track] | Playlist | None:
        r"""Load tracks or a playlist from Lavalink.

        Parameters
        ----------
        query : str
            A URL or a raw search term.
        search_type : str
            Search prefix (e.g. ``ytsearch``) applied when *query* is not a URL.

        Returns
        -------
        list[:class:`~wavecord.Track`]
            For single tracks or search results.
        :class:`~wavecord.Playlist`
            For playlist URLs.
        None
            If nothing was found.

        Raises
        ------
        :class:`~wavecord.TrackLoadException`
            If Lavalink reports a load error.
        """
        if not _URL_RE.match(query):
            query = f"{search_type}:{query}"

        data: TrackLoadingResult = await self.__request(
            "GET", "loadtracks", params={"identifier": query}
        )

        load_type: str = data.get("loadType", "empty")

        # Lavalink v4
        if load_type == "track":
            return [Track.from_data_with_info(data["data"])]
        elif load_type == "search":
            return [Track.from_data_with_info(t) for t in data["data"]]
        elif load_type == "playlist":
            return Playlist(
                info=data["data"]["info"],
                tracks=data["data"]["tracks"],
                plugin_info=data["data"].get("pluginInfo"),
            )
        elif load_type in ("empty", "NO_MATCHES"):
            return []
        elif load_type == "error":
            raise TrackLoadException.from_data(data["data"])

        # Lavalink v3 fallback
        elif load_type == "TRACK_LOADED":
            return [Track.from_data_with_info(data["tracks"][0])]
        elif load_type == "PLAYLIST_LOADED":
            return Playlist(
                info=data["playlistInfo"],
                tracks=data["tracks"],
                plugin_info={},
            )
        elif load_type == "SEARCH_RESULT":
            return [Track.from_data_with_info(t) for t in data["tracks"]]
        elif load_type == "LOAD_FAILED":
            raise TrackLoadException.from_data(data["exception"])

        _log.warning("Unknown loadType %r — returning None.", load_type)
        return None

    async def decode_track(self, encoded: str) -> Track:
        """Decode a base64-encoded track string.

        Parameters
        ----------
        encoded : str

        Returns
        -------
        :class:`~wavecord.Track`
        """
        data: TrackWithInfo = await self.__request(
            "GET", "decodetrack", params={"encodedTrack": encoded}
        )
        return Track.from_data_with_info(data)

    async def decode_tracks(self, tracks: list[str]) -> list[Track]:
        r"""Batch-decode multiple base64 track strings.

        Parameters
        ----------
        tracks : list[str]

        Returns
        -------
        list[:class:`~wavecord.Track`]
        """
        data: list[TrackWithInfo] = await self.__request(
            "POST", "decodetracks", json=tracks
        )
        return [Track.from_data_with_info(t) for t in data]

    # REST — plugins
    async def fetch_plugins(self) -> list[Plugin]:
        r"""Fetch installed Lavalink plugins.

        Returns
        -------
        list[:class:`~wavecord.Plugin`]
        """
        plugins: list[PluginData] = await self.__request("GET", "plugins")
        return [Plugin(p) for p in plugins]

    # REST — route planner
    async def fetch_route_planner_status(self) -> RoutePlannerStatus | None:
        """Fetch the Lavalink IP route planner status.

        Returns
        -------
        :data:`~wavecord.ip.RoutePlannerStatus` or None
            ``None`` when no route planner is configured.
        """
        data: RoutePlannerStatusPayload = await self.__request(
            "GET", "routeplanner/status"
        )

        cls = data.get("cls") or data.get("class")

        if cls == "RotatingIpRoutePlanner":
            return RotatingIPRoutePlannerStatus(
                cast(RotatingIPRouteDetails, data["details"])
            )
        elif cls == "NanoIpRoutePlanner":
            return NanoIPRoutePlannerStatus(
                cast(NanoIPRouteDetails, data["details"])
            )
        elif cls == "RotatingNanoIpRoutePlanner":
            return RotatingNanoIPRoutePlannerStatus(
                cast(RotatingNanoIPRouteDetails, data["details"])
            )
        elif cls == "BalancingIpRoutePlanner":
            return BalancingIPRoutePlannerStatus(
                cast(BalancingIPRouteDetails, data["details"])
            )
        elif cls is None:
            return None
        else:
            msg = f"Unknown route planner class: {cls!r}"
            raise RuntimeError(msg)

    async def unmark_failed_address(self, address: str) -> None:
        """Remove an address from the route planner's failing list.

        Parameters
        ----------
        address : str
            The IP address to unmark.
        """
        await self.__request(
            "POST", "routeplanner/free/address", json={"address": address}
        )

    async def unmark_all_addresses(self) -> None:
        """Remove all addresses from the route planner's failing list."""
        await self.__request("POST", "routeplanner/free/all")

    # Player sync (after session resume)
    async def _add_unknown_player(
        self,
        player_id: int,
        state: Any,
        cls: type[Player[ClientT]] | None = None,
    ) -> None:
        guild = self._client.get_guild(player_id)
        if guild is None:
            guild = await self._client.fetch_guild(player_id)

        voice_state = guild.me.voice
        if voice_state is None or voice_state.channel is None:
            return

        from .player import Player

        player = (cls or Player)(self._client, voice_state.channel)
        player.set_state(state)
        player._node = self # pyright: ignore[reportPrivateUsage]
        self._players[player_id] = player

        key, _ = player.channel._get_voice_client_key() # pyright: ignore
        self._client._connection._add_voice_client(key, player) # pyright: ignore

    async def _remove_unknown_player(self, player_id: int) -> None:
        await self._players[player_id].disconnect(force=True)
        self.remove_player(player_id)

    async def sync_players(
        self, player_cls: type[Player[ClientT]] | None = None
    ) -> None:
        """Sync local player cache with Lavalink after a session resume.

        You should not need to call this manually.
        """
        players: list[Any] = await self.__request(
            "GET", f"sessions/{self._session_id}/players"
        )
        actual = {int(p["guildId"]): p for p in players}
        actual_ids = set(actual)
        expected_ids = set(self._players)

        await gather(
            *(
                self._add_unknown_player(pid, actual[pid], cls=player_cls)
                for pid in actual_ids - expected_ids
            ),
            *(
                self._remove_unknown_player(pid)
                for pid in expected_ids - actual_ids
            ),
        )

    # Internal HTTP helper
    async def __request(
        self,
        method: str,
        path: str,
        json: OutgoingMessage | None = None,
        params: OutgoingMessage | None = None,
    ) -> Any:
        if self.__session is None:
            self.__session = await self._create_session()

        uri = self._rest_uri / path
        _log.debug(
            "%s %s payload=%r params=%r", method, uri, json, params,
            extra={"label": self._label},
        )

        async with self.__session.request(
            method,
            uri,
            json=json,
            params=params,
            headers={"Authorization": self.__password},
        ) as resp:
            if resp.status == 204:
                return None

            if not (200 <= resp.status < 300):
                text = await resp.text()
                if resp.status == 400:
                    raise HTTPBadRequest(text)
                elif resp.status == 401:
                    raise HTTPUnauthorized(text)
                elif resp.status == 404:
                    raise HTTPNotFound(text)
                else:
                    raise HTTPException(resp.status, text)

            return await resp.json(loads=loads)

    # Dunder
    def __repr__(self) -> str:
        return (
            f"<Node label={self._label!r} "
            f"host={self._host!r} "
            f"port={self._port} "
            f"version={self._version} "
            f"available={self._available}>"
        )
