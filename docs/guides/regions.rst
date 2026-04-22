.. _guide-regions:

Voice Regions
=============

WaveCord can route each guild to the geographically closest Lavalink node
automatically, using the Discord voice server endpoint to detect the region.

How it Works
------------

When a player connects, Discord sends a voice server update containing an
endpoint like ``us-east1.discord.media``.  WaveCord's
:attr:`~wavecord.Strategy.LOCATION` strategy extracts the region from this
endpoint and picks a node whose ``regions`` list contains that
:class:`~wavecord.VoiceRegion`.

The hierarchy is:

- :class:`~wavecord.VoiceRegion` — a single Discord voice region (e.g. ``US_EAST``)
- :class:`~wavecord.Region` — a named group of ``VoiceRegion`` values (e.g. ``EAST_NA``)
- :class:`~wavecord.Group` — a broad continental group of ``Region`` values (e.g. ``WEST``)

You can pass any mix of these three types to ``create_node``.

Example
-------

.. code-block:: python

   # Fine-grained: specific regions
   await pool.create_node(
       ..., label="eu-west",
       regions=[
           wavecord.Region.WEST_EUROPE,
           wavecord.Region.CENTRAL_EUROPE,
       ],
   )

   # Broad: entire continent
   await pool.create_node(
       ..., label="asia",
       regions=[wavecord.Group.EAST],
   )

   # Mixed
   await pool.create_node(
       ..., label="mixed",
       regions=[
           wavecord.Region.EAST_NA,
           wavecord.VoiceRegion.BRAZIL,
       ],
   )

Region Reference
----------------

North America
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Region
     - VoiceRegions
   * - ``EAST_NA``
     - MONTREAL, US_EAST, ATLANTA, NEWARK
   * - ``CENTRAL_NA``
     - US_CENTRAL
   * - ``WEST_NA``
     - OREGON, SANTA_CLARA, SEATTLE, US_WEST
   * - ``SOUTH_NA``
     - US_SOUTH

South America
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Region
     - VoiceRegions
   * - ``SOUTH_AMERICA``
     - BRAZIL, SANTIAGO, BUENOS_AIRES

Europe
~~~~~~

.. list-table::
   :header-rows: 1

   * - Region
     - VoiceRegions
   * - ``WEST_EUROPE``
     - LONDON, AMSTERDAM, ROTTERDAM, MADRID, NEWARK
   * - ``CENTRAL_EUROPE``
     - FRANKFURT, EUROPE
   * - ``NORTH_EUROPE``
     - STOCKHOLM, FINLAND, ST_PETE
   * - ``SOUTH_EUROPE``
     - MILAN
   * - ``EAST_EUROPE``
     - BUCHAREST

Asia / Pacific
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Region
     - VoiceRegions
   * - ``EAST_ASIA``
     - JAPAN, HONG_KONG, SOUTH_KOREA
   * - ``SOUTH_ASIA``
     - INDIA, SINGAPORE
   * - ``WEST_ASIA``
     - DUBAI
   * - ``NORTH_ASIA``
     - RUSSIA
   * - ``OCEANIA``
     - SYDNEY

Africa
~~~~~~

.. list-table::
   :header-rows: 1

   * - Region
     - VoiceRegions
   * - ``SOUTH_AFRICA``
     - SOUTH_AFRICA
