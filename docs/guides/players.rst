.. _guide-players:

Players
=======

:class:`~wavecord.Player` extends your Discord library's ``VoiceProtocol``
and handles all playback for a single guild.

Connecting
----------

Pass :class:`~wavecord.Player` as ``cls`` when connecting:

.. code-block:: python

   player = await voice_channel.connect(cls=wavecord.Player)

   # Or with discord.py's ctx shorthand:
   player: wavecord.Player = ctx.voice_client

Playback
--------

.. code-block:: python

   # Play a track
   await player.play(track)

   # Play from a specific time (ms)
   await player.play(track, start_time=30_000)

   # Stop (keeps the player connected)
   await player.stop()

   # Pause / resume
   await player.pause()
   await player.resume()

   # Seek to position (ms)
   await player.seek(60_000)

   # Set volume (0–1000, default 100)
   await player.set_volume(80)

State
-----

.. code-block:: python

   player.current      # Track | None
   player.position     # int (ms, interpolated)
   player.paused       # bool
   player.volume       # int
   player.connected    # bool
   player.ping         # int (ms, -1 if unknown)

Searching
---------

.. code-block:: python

   # Search YouTube (default)
   results = await player.fetch_tracks("lofi hip hop")

   # Search SoundCloud
   results = await player.fetch_tracks("query", wavecord.SearchType.SOUNDCLOUD)

   # Load a URL directly
   results = await player.fetch_tracks("https://open.spotify.com/track/...")

   # results is list[Track] | Playlist | None

Disconnecting
-------------

.. code-block:: python

   await player.disconnect()

This stops playback, removes the player from Lavalink, and leaves the channel.

Transferring to Another Node
-----------------------------

All state is preserved when moving between nodes:

.. code-block:: python

   target = wavecord.NodePool.get_node_by_label("backup")
   await player.transfer_to(target)
