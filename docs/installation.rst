Installation
============

Requirements
------------

- Python **3.9** or newer
- Lavalink **3.7.x** or **4.x**
- One of the following Discord libraries:

  - `discord.py <https://github.com/Rapptz/discord.py>`_ ≥ 2.4
  - `nextcord <https://github.com/nextcord/nextcord>`_ ≥ 2.6 / 3.x
  - `disnake <https://github.com/DisnakeDev/disnake>`_ ≥ 2.9
  - `py-cord <https://github.com/Pycord-Development/pycord>`_ ≥ 2.6

Installing WaveCord
-------------------

Install from PyPI:

.. code-block:: bash

   pip install wavecord

Install with optional JSON speedups (requires Python ≥ 3.10):

.. code-block:: bash

   pip install wavecord[speedups]

The ``speedups`` extra installs `orjson <https://github.com/ijl/orjson>`_,
which is significantly faster than the stdlib ``json`` module.

Setting Up Lavalink
-------------------

WaveCord requires a running Lavalink server.  Download the latest release from
the `Lavalink GitHub <https://github.com/freyacodes/Lavalink/releases>`_ and
run it with Java 17+:

.. code-block:: bash

   java -jar Lavalink.jar

The default configuration listens on port ``2333`` with password
``youshallnotpass``.  See the Lavalink docs for a full ``application.yml``
reference.

Verifying the Installation
--------------------------

Run the WaveCord CLI to print version info:

.. code-block:: bash

   python -m wavecord
