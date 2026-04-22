.. _guide-filters:

Audio Filters
=============

WaveCord supports all Lavalink v4 audio filters.  Filters are **stacked by
name** on a player, so you can layer multiple effects simultaneously and
remove them individually.

Available Filters
-----------------

.. list-table::
   :header-rows: 1
   :widths: 20 60 20

   * - Class
     - Effect
     - Key params
   * - :class:`~wavecord.Equalizer`
     - 15-band EQ (−0.25 to 1.0 gain per band)
     - ``bands``
   * - :class:`~wavecord.Timescale`
     - Speed, pitch, rate
     - ``speed``, ``pitch``, ``rate``
   * - :class:`~wavecord.Rotation`
     - 8D / binaural stereo rotation
     - ``rotation_hz``
   * - :class:`~wavecord.Tremolo`
     - Wavering volume (amplitude modulation)
     - ``frequency``, ``depth``
   * - :class:`~wavecord.Vibrato`
     - Wavering pitch (frequency modulation)
     - ``frequency``, ``depth``
   * - :class:`~wavecord.Karaoke`
     - Vocal removal
     - ``level``, ``filter_band``
   * - :class:`~wavecord.Distortion`
     - Mathematical audio distortion
     - ``sin_scale``, ``offset``, …
   * - :class:`~wavecord.ChannelMix`
     - Left/right channel mixing (mono, wide stereo)
     - ``left_to_left``, ``right_to_right``, …
   * - :class:`~wavecord.LowPass`
     - Cuts high frequencies (bass emphasis)
     - ``smoothing``

Adding a Filter
---------------

Wrap your filter in a :class:`~wavecord.Filter` container and call
:meth:`~wavecord.Player.add_filter` with a unique **label**:

.. code-block:: python

   nightcore = wavecord.Filter(
       timescale=wavecord.Timescale(speed=1.25, pitch=1.25),
   )
   await player.add_filter(nightcore, label="nightcore")

The ``fast_apply=True`` flag seeks to the current position after applying,
which clears Lavalink's audio buffer and makes the effect audible immediately:

.. code-block:: python

   await player.add_filter(nightcore, label="nightcore", fast_apply=True)

Removing a Filter
-----------------

.. code-block:: python

   await player.remove_filter("nightcore", fast_apply=True)

Toggling
--------

.. code-block:: python

   if await player.has_filter("nightcore"):
       await player.remove_filter("nightcore", fast_apply=True)
   else:
       await player.add_filter(nightcore, label="nightcore", fast_apply=True)

Stacking Filters
----------------

Multiple filters are automatically merged with ``|`` before being sent to
Lavalink.  Each filter is identified by its label, so you can stack as many
as you like:

.. code-block:: python

   await player.add_filter(
       wavecord.Filter(rotation=wavecord.Rotation(rotation_hz=0.2)),
       label="8d",
   )
   await player.add_filter(
       wavecord.Filter(equalizer=wavecord.Equalizer(bands=[(0, 0.5)])),
       label="bassboost",
   )
   # Both "8d" and "bassboost" are active simultaneously

Clearing All Filters
--------------------

.. code-block:: python

   await player.clear_filters(fast_apply=True)

Preset Examples
---------------

**Nightcore** (faster + higher pitch):

.. code-block:: python

   wavecord.Filter(timescale=wavecord.Timescale(speed=1.25, pitch=1.25))

**Vaporwave** (slower + lower pitch):

.. code-block:: python

   wavecord.Filter(timescale=wavecord.Timescale(speed=0.85, pitch=0.85))

**Bass Boost**:

.. code-block:: python

   wavecord.Filter(
       equalizer=wavecord.Equalizer(
           bands=[(0, 0.6), (1, 0.5), (2, 0.4), (3, 0.3), (4, 0.2)]
       )
   )

**Mono downmix**:

.. code-block:: python

   wavecord.Filter(
       channel_mix=wavecord.ChannelMix(
           left_to_left=0.5, left_to_right=0.5,
           right_to_left=0.5, right_to_right=0.5,
       )
   )
