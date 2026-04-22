.. _guide-nodes:

Nodes
=====

A :class:`~wavecord.Node` represents a single Lavalink server connection.
Most bots only need one node, but WaveCord supports multiple for
load-balancing and geographic routing.

Creating a Node
---------------

Always create nodes inside ``on_ready``:

.. code-block:: python

   @bot.event
   async def on_ready():
       await pool.create_node(
           host="127.0.0.1",
           port=2333,
           label="main",
           password="youshallnotpass",
       )

Multiple Nodes
--------------

.. code-block:: python

   @bot.event
   async def on_ready():
       await pool.create_node(
           host="lavalink-eu.example.com", port=2333,
           label="eu", password="secret",
           regions=[wavecord.Region.WEST_EUROPE, wavecord.Region.CENTRAL_EUROPE],
       )
       await pool.create_node(
           host="lavalink-us.example.com", port=2333,
           label="us-east", password="secret",
           regions=[wavecord.Region.EAST_NA],
       )

With regions configured, :meth:`~wavecord.NodePool.get_node` automatically
routes each guild to its geographically closest node.  See :doc:`regions`
for the full region reference.

Node Selection Strategies
--------------------------

:class:`~wavecord.NodePool` uses an ordered strategy pipeline to select the
best node for each request:

.. list-table::
   :header-rows: 1

   * - Strategy
     - What it does
   * - :attr:`~wavecord.Strategy.SHARD`
     - Prefer nodes whose ``shard_ids`` match the guild's shard
   * - :attr:`~wavecord.Strategy.LOCATION`
     - Prefer nodes whose ``regions`` match the guild's voice server
   * - :attr:`~wavecord.Strategy.USAGE`
     - Pick the node with the lowest load (CPU + player count)
   * - :attr:`~wavecord.Strategy.RANDOM`
     - Pick at random

The default order is ``SHARD → LOCATION → USAGE``.  You can override it:

.. code-block:: python

   pool = wavecord.NodePool(
       bot,
       default_strategies=[wavecord.Strategy.LOCATION, wavecord.Strategy.USAGE],
   )

Session Resuming
----------------

WaveCord configures session resuming automatically.  If Lavalink restarts,
the node reconnects and the existing players resume without interruption.

For Lavalink v4 you can also pass a previous ``resuming_session_id``:

.. code-block:: python

   await pool.create_node(
       ...,
       resuming_session_id="your-previous-session-id",
   )

Removing a Node
---------------

.. code-block:: python

   # Transfers all players to other nodes before disconnecting
   await pool.remove_node("main", transfer_players=True)

Node Stats
----------

.. code-block:: python

   node = wavecord.NodePool.get_node_by_label("main")
   stats = node.stats  # NodeStats | None

   if stats:
       print(f"Players: {stats.player_count}")
       print(f"CPU: {stats.cpu.lavalink_load:.1%}")
       print(f"Memory: {stats.memory.used // 1024 // 1024} MB")
