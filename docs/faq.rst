FAQ
===

.. contents::
   :local:
   :depth: 1

Why does WaveCord raise ``NoCompatibleLibraries``?
--------------------------------------------------

You need to install at least one supported Discord library.  WaveCord works
with ``discord.py``, ``nextcord``, ``disnake``, and ``py-cord``.

.. code-block:: bash

   pip install discord.py   # or nextcord / disnake / py-cord

If you have multiple libraries installed and want to suppress the check
(for example in a testing environment), set the environment variable:

.. code-block:: bash

   export WAVECORD_IGNORE_LIBRARY_CHECK=1

Why is my node not connecting?
------------------------------

Check that:

1. Lavalink is running and accessible on the configured host and port.
2. The ``password`` matches the one in your Lavalink ``application.yml``.
3. Firewall rules allow the connection.
4. You are calling :meth:`~wavecord.NodePool.create_node` **inside**
   ``on_ready`` (or another event that fires after the client is logged in).

How do I use WaveCord with a Cog?
----------------------------------

Create the :class:`~wavecord.NodePool` at module level or in ``setup``,
and store the reference on the cog:

.. code-block:: python

   import wavecord
   from discord.ext import commands

   class MusicCog(commands.Cog):
       def __init__(self, bot):
           self.bot = bot
           self.pool = wavecord.NodePool(bot)

       @commands.Cog.listener()
       async def on_ready(self):
           await self.pool.create_node(
               host="127.0.0.1", port=2333,
               label="main", password="youshallnotpass",
           )

How do I implement a queue?
----------------------------

WaveCord does not include a built-in queue; you manage it yourself.
A simple approach:

.. code-block:: python

   from collections import deque

   queues: dict[int, deque] = {}  # guild_id → deque of Track

   @bot.event
   async def on_track_end(event: wavecord.TrackEndEvent):
       if not event.may_start_next:
           return
       q = queues.get(event.player.guild.id)
       if q:
           await event.player.play(q.popleft())

Can I use WaveCord with Lavalink v3?
-------------------------------------

Yes.  WaveCord auto-detects the server version and adjusts the API
accordingly.  Lavalink **3.7.x** and all **4.x** releases are supported.

How do I transfer a player to another node?
--------------------------------------------

Use :meth:`~wavecord.Player.transfer_to`:

.. code-block:: python

   target = wavecord.NodePool.get_node_by_label("backup")
   await player.transfer_to(target)

All state (position, filters, volume, current track) is preserved.
