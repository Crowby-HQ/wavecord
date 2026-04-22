.. _guide-events:

Events
======

WaveCord dispatches events through your bot's normal event system.

Player Events
-------------

.. list-table::
   :header-rows: 1

   * - Event name
     - Class
     - When
   * - ``on_track_start``
     - :class:`~wavecord.TrackStartEvent`
     - A track starts playing
   * - ``on_track_end``
     - :class:`~wavecord.TrackEndEvent`
     - A track ends (finished, skipped, stopped)
   * - ``on_track_exception``
     - :class:`~wavecord.TrackExceptionEvent`
     - An error occurs during playback
   * - ``on_track_stuck``
     - :class:`~wavecord.TrackStuckEvent`
     - Lavalink detects a stuck track
   * - ``on_websocket_closed``
     - :class:`~wavecord.WebSocketClosedEvent`
     - Discord closes the voice WebSocket

Node Events
-----------

These are dispatched directly on the bot client (no event class wrapper):

.. list-table::
   :header-rows: 1

   * - Event name
     - Arguments
     - When
   * - ``on_node_ready``
     - ``node: Node``
     - Node connects and is ready
   * - ``on_node_unavailable``
     - ``node: Node``
     - Node WebSocket closes (before reconnect)
   * - ``on_node_stats``
     - ``node: Node``
     - Node sends a stats update

Usage Examples
--------------

.. code-block:: python

   @bot.event
   async def on_track_start(event: wavecord.TrackStartEvent):
       channel = event.player.guild.system_channel
       if channel:
           await channel.send(f"▶ Now playing: **{event.track}**")

   @bot.event
   async def on_track_end(event: wavecord.TrackEndEvent):
       # reason: "finished" | "loadFailed" | "stopped" | "replaced" | "cleanup"
       if event.may_start_next:
           # pop next item from your queue here
           pass

   @bot.event
   async def on_track_exception(event: wavecord.TrackExceptionEvent):
       print(f"[{event.severity}] {event.message}: {event.cause}")

   @bot.event
   async def on_track_stuck(event: wavecord.TrackStuckEvent):
       print(f"Track stuck after {event.threshold_ms}ms — skipping.")
       await event.player.stop()

   @bot.event
   async def on_websocket_closed(event: wavecord.WebSocketClosedEvent):
       # code 4014 = bot was moved / disconnected by an admin
       if event.code == 4014:
           await event.player.disconnect(force=True)

   @bot.event
   async def on_node_ready(node: wavecord.Node):
       print(f"Node '{node.label}' ready (Lavalink v{node.version})")
