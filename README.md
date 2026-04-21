<div align="center">

![WaveCord](https://i.imgur.com/c6p2lDQ.png)

A modern, async-first Lavalink v4 client for Python Discord libraries.

[![PyPI](https://img.shields.io/pypi/v/wavecord?style=for-the-badge&color=blueviolet&logo=pypi&logoColor=white)](https://pypi.org/project/wavecord)
[![Python](https://img.shields.io/pypi/pyversions/wavecord?style=for-the-badge&logo=python&logoColor=white)](https://pypi.org/project/wavecord)
[![CI](https://img.shields.io/github/actions/workflow/status/Crowby-HQ/wavecord/lint.yml?label=build&style=for-the-badge&logo=github)](https://github.com/Crowby-HQ/wavecord/actions)
[![License](https://img.shields.io/pypi/l/wavecord?style=for-the-badge)](LICENSE)
[![Docs](https://img.shields.io/readthedocs/wavecord?style=for-the-badge&logo=readthedocs&logoColor=white)](https://wavecord.readthedocs.io)
![Typing](https://img.shields.io/badge/typing-checked-blue?style=for-the-badge)

</div>

---

### Features

- Full **Lavalink v4** WebSocket + REST support (v3 backwards-compatible)
- **Multi-library**: works with `discord.py`, `nextcord`, `disnake`, `py-cord`
- **Node strategy system**: SHARD, LOCATION, USAGE, RANDOM or bring your own
- **Voice regions**: route guilds to the geographically closest node automatically
- **Stackable named filters**: EQ, Timescale, Rotation, Karaoke, Distortion, and more
- **Session resuming**: survive Lavalink restarts without dropping players
- **Node transfer**: move players between nodes at runtime with no interruption
- **IP route planner**: full API for Lavalink's rotating IP feature
- **Exponential backoff**: automatic reconnection with jitter
- **Typed with Pyright strict**: full generic typing through the public API
- Optional **orjson** speedups

---

### Requirements

- Python **3.9+**
- Lavalink **3.7.x** or **4.x**
- One of: `discord.py`, `nextcord`, `disnake`, `py-cord`

---

### Installation

```bash
pip install wavecord
```

With faster JSON (recommended):

```bash
pip install wavecord[speedups]
```

---

### Quick Start

```python
import wavecord

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

@bot.command()
async def play(ctx, *, query: str):
    if not ctx.author.voice:
        return await ctx.send("Join a voice channel first.")

    player: wavecord.Player = ctx.voice_client or await ctx.author.voice.channel.connect(cls=wavecord.Player)
    results = await player.fetch_tracks(query)

    if not results:
        return await ctx.send("Nothing found.")

    track = results[0] if isinstance(results, list) else results.tracks[0]
    await player.play(track)
    await ctx.send(f"▶ Now playing: **{track}**")

@bot.command()
async def nightcore(ctx):
    player: wavecord.Player = ctx.voice_client
    if player is None:
        return
    await player.add_filter(
        wavecord.Filter(timescale=wavecord.Timescale(speed=1.25, pitch=1.25)),
        label="nightcore",
    )

@bot.command()
async def stop(ctx):
    player: wavecord.Player = ctx.voice_client
    if player:
        await player.disconnect()
```

---

### Events

```python
@bot.event
async def on_track_start(event: wavecord.TrackStartEvent):
    print(f"[{event.player.guild}] ▶ {event.track}")

@bot.event
async def on_track_end(event: wavecord.TrackEndEvent):
    if event.may_start_next:
        # play next track in your queue here
        pass

@bot.event
async def on_track_exception(event: wavecord.TrackExceptionEvent):
    print(f"Error [{event.severity}]: {event.message}")
```

---

### Multi-Node with Regions

```python
await pool.create_node(
    host="lavalink-eu.example.com",
    port=2333,
    label="europe",
    password="secret",
    regions=[wavecord.Region.WEST_EUROPE, wavecord.Region.CENTRAL_EUROPE],
)

await pool.create_node(
    host="lavalink-us.example.com",
    port=2333,
    label="us-east",
    password="secret",
    regions=[wavecord.Region.EAST_NA],
)
```

---

<p align="center">
	<img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/footers/gray0_ctp_on_line.svg?sanitize=true" />
</p>

<p align="center">
        <code>&copy 2024-Present <a href="https://github.com/Crowby-HQ">Crowby Inc.</a></code>
</p>
