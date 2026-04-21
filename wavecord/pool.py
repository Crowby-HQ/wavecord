# SPDX-License-Identifier: MIT
"""NodePool - manages a collection of Lavalink nodes."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from functools import partial
from logging import getLogger
from random import choice
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Generic, List, Optional, cast

from .errors import NoNodesAvailable, PlayerNotConnected
from .node import Node
from .strategy import Strategy, StrategyCallable, StrategyList, call_strategy
from .type_variables import ClientT
from .utils import classproperty

if TYPE_CHECKING:
    import aiohttp

    from .player import Player
    from .region import Group, Region, VoiceRegion

_log = getLogger(__name__)
__all__ = ("NodePool",)


class NodePool(Generic[ClientT]):
    r"""Manages a collection of :class:`~wavecord.Node` instances.

    There is normally one :class:`NodePool` per bot. It acts as both a
    factory (via :meth:`create_node`) and a registry that the
    :class:`~wavecord.Player` uses to pick the best node for each guild.

    Parameters
    ----------
    client : ClientT
        Your Discord client instance.
    default_strategies : StrategyList or None
        Ordered list of strategies used when selecting a node.
        Defaults to ``[Strategy.SHARD, Strategy.LOCATION, Strategy.USAGE]``.

    Examples
    --------
    .. code-block:: python

        pool = NodePool(bot)

        @bot.event
        async def on_ready():
            await pool.create_node(
                host="127.0.0.1",
                port=2333,
                label="main",
                password="youshallnotpass",
            )
    """

    __slots__ = ()

    # Class-level state — shared across all NodePool instances.
    _nodes: ClassVar[Dict[str, Node[Any]]] = {}
    _client: ClassVar[Any] = None
    _default_strategies: ClassVar[Any] = None

    def __init__(
        self,
        client: ClientT,
        default_strategies: Optional[StrategyList] = None,
    ) -> None:
        NodePool._client = client
        NodePool._default_strategies = default_strategies or [
            Strategy.SHARD,
            Strategy.LOCATION,
            Strategy.USAGE,
        ]

    # Class properties
    @classproperty
    def label_to_node(cls) -> Dict[str, Node[ClientT]]:  # type: ignore[misc]
        """All nodes keyed by their label."""
        return cls._nodes  # type: ignore[return-value]

    @classproperty
    def nodes(cls) -> List[Node[ClientT]]:  # type: ignore[misc]
        """All nodes that are currently available."""
        return [n for n in cls._nodes.values() if n.available]  # type: ignore[return-value]

    # Node lifecycle
    async def create_node(
        self,
        *,
        host: str,
        port: int,
        label: str,
        password: str,
        secure: bool = False,
        heartbeat: int = 30,
        timeout: float = 10,
        session: Optional[aiohttp.ClientSession] = None,
        resume_key: Optional[str] = None,
        regions: Optional[Sequence[Group | Region | VoiceRegion]] = None,
        shard_ids: Optional[Sequence[int]] = None,
        resuming_session_id: Optional[str] = None,
        player_cls: Optional[type[Player[ClientT]]] = None,
    ) -> Node[ClientT]:
        r"""Create and connect a new Lavalink node.

        Parameters
        ----------
        host : str
            Lavalink server hostname.
        port : int
            Lavalink server port.
        label : str
            Unique identifier for this node.
        password : str
            Lavalink server password.
        secure : bool
            Use HTTPS/WSS. Default ``False``.
        heartbeat : int
            WebSocket heartbeat interval in seconds.
        timeout : float
            Seconds to wait for the node to become ready.
        session : :class:`aiohttp.ClientSession` or None
            Reuse an existing session.
        resume_key : str or None
            Lavalink v3 resume key.
        regions : sequence or None
            Voice regions this node should be preferred for.
        shard_ids : sequence[int] or None
            Shard IDs this node handles.
        resuming_session_id : str or None
            Lavalink v4 session ID to resume.
        player_cls : type[:class:`~wavecord.Player`] or None
            Custom player class for resumed players.

        Returns
        -------
        :class:`~wavecord.Node`

        Raises
        ------
        RuntimeError
            If :class:`NodePool` has not been initialised.
        """
        if self._client is None:
            msg = "NodePool has not been initialised with a client."
            raise RuntimeError(msg)

        node: Node[ClientT] = Node(
            host=host,
            port=port,
            label=label,
            password=password,
            client=self._client,
            secure=secure,
            heartbeat=heartbeat,
            timeout=timeout,
            session=session,
            resume_key=resume_key,
            regions=regions,
            shard_ids=shard_ids,
            resuming_session_id=resuming_session_id,
        )
        await self.add_node(node, player_cls=player_cls)
        return node

    async def add_node(
        self,
        node: Node[ClientT],
        *,
        player_cls: Optional[type[Player[ClientT]]] = None,
    ) -> None:
        """Add an already-constructed node to the pool and connect it.

        .. note::
            Prefer :meth:`create_node` for normal usage.  This method is
            useful when re-adding a node that was removed via
            :meth:`remove_node`.

        Parameters
        ----------
        node : :class:`~wavecord.Node`
        player_cls : type[:class:`~wavecord.Player`] or None
        """
        _log.info("Connecting node '%s'…", node.label, extra={"label": node.label})
        await node.connect(player_cls=player_cls)
        self._nodes[node.label] = node
        _log.info("Node '%s' added to pool.", node.label, extra={"label": node.label})

    async def remove_node(
        self,
        node: Node[ClientT] | str,
        *,
        transfer_players: bool = True,
    ) -> None:
        """Remove a node from the pool.

        Parameters
        ----------
        node : :class:`~wavecord.Node` or str
            The node instance or its label.
        transfer_players : bool
            If ``True`` (default), attempt to move all players to another
            node before closing. If ``False``, all players are destroyed.
        """
        if isinstance(node, str):
            node = self._nodes[node]

        # Remove early so it is not chosen as a transfer target.
        del self._nodes[node.label]

        if transfer_players:

            async def _transfer(player: Player[ClientT]) -> None:
                try:
                    target = self.get_node(
                        guild_id=player.guild.id,
                        endpoint=player.endpoint,
                    )
                    await player.transfer_to(target)
                except (RuntimeError, NoNodesAvailable, PlayerNotConnected):
                    _log.error(
                        "Failed to transfer player %d — destroying it.",
                        player.guild.id,
                        exc_info=True,
                        extra={"label": node.label},
                    )
                    await player.destroy()

            await asyncio.gather(*(_transfer(p) for p in node.players))
        else:
            await asyncio.gather(*(p.destroy() for p in node.players))

        await node.close()

    async def close(self) -> None:
        """Disconnect all nodes and clear the pool."""
        for node in list(self._nodes.values()):
            await node.close()
        self._nodes.clear()
        _log.info("NodePool closed.")

    # Node selection
    @classmethod
    def get_node(
        cls,
        *,
        guild_id: int | str,
        endpoint: Optional[str],
        strategies: Optional[StrategyList] = None,
    ) -> Node[ClientT]:
        r"""Select the best available node for a guild.

        The selection runs through each strategy in order, narrowing the
        candidate list.  If only one candidate remains after a strategy,
        that node is returned immediately.  If the list is exhausted
        without a single candidate, a :exc:`~wavecord.NoNodesAvailable` is raised.

        Parameters
        ----------
        guild_id : int or str
            The Discord guild ID.
        endpoint : str or None
            The Discord voice server endpoint.
        strategies : StrategyList or None
            Override the pool's default strategies for this call.

        Returns
        -------
        :class:`~wavecord.Node`

        Raises
        ------
        RuntimeError
            If the pool has not been initialised.
        :exc:`~wavecord.NoNodesAvailable`
            If no nodes pass all strategies.
        """
        if cls._client is None:
            msg = "NodePool has not been initialised."
            raise RuntimeError(msg)

        chosen_strategies = strategies or cls._default_strategies
        actual: list[StrategyCallable | Strategy] = (
            [chosen_strategies]
            if callable(chosen_strategies)
            else list(chosen_strategies)
        )

        candidates: list[Node[Any]] = cast("list[Node[ClientT]]", cls.nodes)  # pyright: ignore

        for strategy in actual:
            if isinstance(strategy, Strategy):
                fn = partial(call_strategy, strategy)
            else:
                fn = strategy

            candidates = fn(
                candidates,
                int(guild_id),
                getattr(cls._client, "shard_count", None),
                endpoint,
            )

            _log.debug(
                "Strategy %s → candidates: %s",
                strategy.__name__ if callable(strategy) else strategy.name,
                [n.label for n in candidates],
            )

            if len(candidates) == 1:
                return candidates[0]
            if len(candidates) == 0:
                raise NoNodesAvailable

        return choice(candidates)

    @classmethod
    def get_random_node(cls) -> Node[ClientT]:
        """Return a random available node.

        Returns
        -------
        :class:`~wavecord.Node`

        Raises
        ------
        :exc:`~wavecord.NoNodesAvailable`
        """
        available = cast("list[Node[ClientT]]", cls.nodes)  # pyright: ignore
        if not available:
            raise NoNodesAvailable
        return choice(available)

    @classmethod
    def get_node_by_label(cls, label: str) -> Optional[Node[ClientT]]:
        """Look up a node by its exact label.

        Parameters
        ----------
        label : str

        Returns
        -------
        :class:`~wavecord.Node` or None
        """
        return cls._nodes.get(label)  # type: ignore[return-value]

    # Dunder
    def __repr__(self) -> str:
        total = len(self._nodes)
        available = len(self.nodes)
        return f"<NodePool nodes={total} available={available}>"
