# SPDX-License-Identifier: MIT
"""Basic music bot example using WaveCord + discord.py.

Run with:
    python examples/basic_bot.py

Environment variables:
    DISCORD_TOKEN   Your bot token.
    LAVALINK_HOST   Lavalink hostname (default: 127.0.0.1).
    LAVALINK_PORT   Lavalink port (default: 2333).
    LAVALINK_PASS   Lavalink password (default: youshallnotpass).
"""

from __future__ import annotations

import os

import discord
from discord.ext import commands

import wavecord

# Bot setup
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
pool = wavecord.NodePool(bot)


# Events
@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} ({bot.user.id})")  # type: ignore[union-attr]

    await pool.create_node(
        host=os.getenv("LAVALINK_HOST", "127.0.0.1"),
        port=int(os.getenv("LAVALINK_PORT", "2333")),
        label="main",
        password=os.getenv("LAVALINK_PASS", "youshallnotpass"),
    )


@bot.event
async def on_node_ready(node: wavecord.Node) -> None:
    print(f"Node '{node.label}' connected and ready!")


@bot.event
async def on_track_start(event: wavecord.TrackStartEvent) -> None:
    guild = event.player.guild
    channel = guild.system_channel
    if channel:
        await channel.send(f"▶ Now playing: **{event.track}**")


@bot.event
async def on_track_end(event: wavecord.TrackEndEvent) -> None:
    if event.may_start_next:
        # Add your own queue logic here.
        pass


@bot.event
async def on_track_exception(event: wavecord.TrackExceptionEvent) -> None:
    print(f"[{event.severity.upper()}] Track error: {event.message}")


# Commands
@bot.command(name="join")
async def join(ctx: commands.Context) -> None:
    """Join the caller's voice channel."""
    if not ctx.author.voice or not ctx.author.voice.channel:  # type: ignore[union-attr]
        await ctx.send("You need to be in a voice channel first.")
        return

    channel = ctx.author.voice.channel  # type: ignore[union-attr]
    await channel.connect(cls=wavecord.Player)
    await ctx.send(f"Joined **{channel.name}**.")


@bot.command(name="play")
async def play(ctx: commands.Context, *, query: str) -> None:
    """Play a track or add it to the queue.

    Usage: !play <URL or search query>
    """
    if not ctx.voice_client:
        if not ctx.author.voice or not ctx.author.voice.channel:  # type: ignore[union-attr]
            await ctx.send("Join a voice channel first.")
            return
        await ctx.author.voice.channel.connect(cls=wavecord.Player)  # type: ignore[union-attr]

    player: wavecord.Player = ctx.voice_client  # type: ignore[assignment]

    async with ctx.typing():
        results = await player.fetch_tracks(query)

    if not results:
        await ctx.send("❌ Nothing found.")
        return

    if isinstance(results, wavecord.Playlist):
        track = results.selected_track or results.tracks[0]
        await ctx.send(
            f"▶ Playing **{track}** from playlist **{results.name}** "
            f"({len(results)} tracks)."
        )
    else:
        track = results[0]
        await ctx.send(f"▶ Playing **{track}**.")

    await player.play(track)


@bot.command(name="pause")
async def pause(ctx: commands.Context) -> None:
    """Pause playback."""
    player: wavecord.Player | None = ctx.voice_client  # type: ignore[assignment]
    if not player:
        await ctx.send("Not connected.")
        return
    await player.pause()
    await ctx.send("⏸ Paused.")


@bot.command(name="resume")
async def resume(ctx: commands.Context) -> None:
    """Resume playback."""
    player: wavecord.Player | None = ctx.voice_client  # type: ignore[assignment]
    if not player:
        await ctx.send("Not connected.")
        return
    await player.resume()
    await ctx.send("▶ Resumed.")


@bot.command(name="stop")
async def stop(ctx: commands.Context) -> None:
    """Stop playback and leave the voice channel."""
    player: wavecord.Player | None = ctx.voice_client  # type: ignore[assignment]
    if not player:
        await ctx.send("Not connected.")
        return
    await player.disconnect()
    await ctx.send("⏹ Stopped and disconnected.")


@bot.command(name="volume")
async def volume(ctx: commands.Context, vol: int) -> None:
    """Set the volume (0–1000).

    Usage: !volume 80
    """
    player: wavecord.Player | None = ctx.voice_client  # type: ignore[assignment]
    if not player:
        await ctx.send("Not connected.")
        return
    if not 0 <= vol <= 1000:
        await ctx.send("Volume must be between 0 and 1000.")
        return
    await player.set_volume(vol)
    await ctx.send(f"🔊 Volume set to **{vol}**.")


@bot.command(name="nowplaying", aliases=["np"])
async def nowplaying(ctx: commands.Context) -> None:
    """Show the currently playing track."""
    player: wavecord.Player | None = ctx.voice_client  # type: ignore[assignment]
    if not player or not player.current:
        await ctx.send("Nothing is playing right now.")
        return

    track = player.current
    position = player.position // 1000
    duration = track.length // 1000

    bar_length = 20
    filled = int(bar_length * position / max(duration, 1))
    bar = "█" * filled + "░" * (bar_length - filled)

    embed = discord.Embed(title="Now Playing", color=0x5865F2)
    embed.description = f"**{track}**"
    embed.add_field(name="Progress", value=f"`{bar}` {position}s / {duration}s", inline=False)
    embed.add_field(name="Source", value=track.source.capitalize(), inline=True)
    embed.add_field(name="Volume", value=f"{player.volume}", inline=True)
    if track.artwork_url:
        embed.set_thumbnail(url=track.artwork_url)

    await ctx.send(embed=embed)


@bot.command(name="seek")
async def seek(ctx: commands.Context, seconds: int) -> None:
    """Seek to a position in the current track (in seconds).

    Usage: !seek 60
    """
    player: wavecord.Player | None = ctx.voice_client  # type: ignore[assignment]
    if not player:
        await ctx.send("Not connected.")
        return
    await player.seek(seconds * 1000)
    await ctx.send(f"⏩ Seeked to **{seconds}s**.")


# Entry point
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN environment variable is not set.")
    bot.run(token)
