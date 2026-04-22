Quickstart
==========

This page walks you through building a minimal music bot with WaveCord and
discord.py.  The same pattern works for nextcord, disnake, and py-cord.

Creating a NodePool
-------------------

:class:`~wavecord.NodePool` is the entry point.  Create one instance per bot
and call :meth:`~wavecord.NodePool.create_node` once the client is ready:

.. code-block:: python

   import wavecord
   import discord
   from discord.ext import commands

   intents = discord.Intents.default()
   intents.message_content = True

   bot = commands.Bot(command_prefix="!", intents=intents)
   pool = wavecord.NodePool(bot)

   @bot.event
   async def on_ready():
       await pool.create_node(
           host="127.0.0.1",
           port=2333,
           label="main",
           password="youshallnotpass",
       )

   @bot.event
   async def on_node_ready(node: wavecord.Node):
       print(f"Node '{node.label}' is ready!")

Connecting a Player
-------------------

Pass :class:`~wavecord.Player` as the ``cls`` argument to your channel's
``connect()`` call:

.. code-block:: python

   @bot.command()
   async def join(ctx):
       if not ctx.author.voice:
           return await ctx.send("Join a voice channel first.")

       player = await ctx.author.voice.channel.connect(cls=wavecord.Player)
       await ctx.send(f"Joined {player.channel}.")

Playing Tracks
--------------

Use :meth:`~wavecord.Player.fetch_tracks` to search, then
:meth:`~wavecord.Player.play` to start playback:

.. code-block:: python

   @bot.command()
   async def play(ctx, *, query: str):
       if not ctx.voice_client:
           await ctx.author.voice.channel.connect(cls=wavecord.Player)

       player: wavecord.Player = ctx.voice_client

       results = await player.fetch_tracks(query)
       if not results:
           return await ctx.send("Nothing found.")

       track = results[0] if isinstance(results, list) else results.tracks[0]
       await player.play(track)
       await ctx.send(f"▶ Now playing: **{track}**")

Handling Events
---------------

WaveCord dispatches events via your bot's ``dispatch`` mechanism:

.. code-block:: python

   @bot.event
   async def on_track_start(event: wavecord.TrackStartEvent):
       print(f"Started: {event.track} in {event.player.guild}")

   @bot.event
   async def on_track_end(event: wavecord.TrackEndEvent):
       if event.may_start_next:
           # play next track from your queue here
           pass

   @bot.event
   async def on_track_exception(event: wavecord.TrackExceptionEvent):
       print(f"Error: {event.message}")

See :doc:`guides/events` for the full list of events.

Next Steps
----------

- :doc:`guides/filters` — Apply audio effects like nightcore, bass boost, and 8D
- :doc:`guides/nodes` — Connect multiple Lavalink nodes with region routing
- :doc:`guides/players` — Full player API reference walkthrough
