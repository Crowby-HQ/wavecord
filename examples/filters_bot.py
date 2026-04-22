# SPDX-License-Identifier: MIT
"""Filters and multi-node example using WaveCord + discord.py.

Demonstrates:
- Stacking named filters (nightcore, bassboost, 8d, etc.)
- Listing and removing active filters
- Multi-node setup with geographic regions

Usage: !nightcore, !bassboost, !8d, !slowreverb, !filters, !clearfilters
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


# Pre-built filter presets
PRESETS: dict[str, wavecord.Filter] = {
    "nightcore": wavecord.Filter(
        timescale=wavecord.Timescale(speed=1.25, pitch=1.25),
    ),
    "bassboost": wavecord.Filter(
        equalizer=wavecord.Equalizer(
            bands=[
                (0, 0.6), (1, 0.5), (2, 0.4), (3, 0.3), (4, 0.2),
                (5, 0.1), (6, 0.0), (7, -0.05),
            ]
        ),
    ),
    "8d": wavecord.Filter(
        rotation=wavecord.Rotation(rotation_hz=0.2),
    ),
    "slowreverb": wavecord.Filter(
        timescale=wavecord.Timescale(speed=0.8, pitch=0.9),
        tremolo=wavecord.Tremolo(frequency=2.0, depth=0.3),
    ),
    "vaporwave": wavecord.Filter(
        timescale=wavecord.Timescale(speed=0.85, pitch=0.85),
        equalizer=wavecord.Equalizer(bands=[(0, 0.3), (1, 0.2)]),
    ),
    "karaoke": wavecord.Filter(
        karaoke=wavecord.Karaoke(level=1.0, mono_level=1.0),
    ),
    "mono": wavecord.Filter(
        channel_mix=wavecord.ChannelMix(
            left_to_left=0.5, left_to_right=0.5,
            right_to_left=0.5, right_to_right=0.5,
        ),
    ),
}


# Events
@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} ({bot.user.id})")  # type: ignore[union-attr]

    # Multi-node setup: EU + US nodes with region routing
    await pool.create_node(
        host=os.getenv("LAVALINK_HOST_EU", "127.0.0.1"),
        port=int(os.getenv("LAVALINK_PORT_EU", "2333")),
        label="eu-main",
        password=os.getenv("LAVALINK_PASS", "youshallnotpass"),
        regions=[wavecord.Region.WEST_EUROPE, wavecord.Region.CENTRAL_EUROPE],
    )

    # Second node (US) — comment out if you only have one
    # await pool.create_node(
    #     host=os.getenv("LAVALINK_HOST_US", "127.0.0.1"),
    #     port=int(os.getenv("LAVALINK_PORT_US", "2334")),
    #     label="us-east",
    #     password=os.getenv("LAVALINK_PASS", "youshallnotpass"),
    #     regions=[wavecord.Region.EAST_NA, wavecord.Region.CENTRAL_NA],
    # )


@bot.event
async def on_node_ready(node: wavecord.Node) -> None:
    print(f"Node '{node.label}' ready — regions: {node.regions}")


# Helper
async def _get_player(ctx: commands.Context) -> wavecord.Player | None:
    player: wavecord.Player | None = ctx.voice_client  # type: ignore[assignment]
    if not player:
        if ctx.author.voice and ctx.author.voice.channel:  # type: ignore[union-attr]
            player = await ctx.author.voice.channel.connect(cls=wavecord.Player)  # type: ignore[union-attr]
        else:
            await ctx.send("Join a voice channel first.")
            return None
    return player


# Play command
@bot.command(name="play")
async def play(ctx: commands.Context, *, query: str) -> None:
    """Play a track. Usage: !play <URL or search>"""
    player = await _get_player(ctx)
    if not player:
        return

    async with ctx.typing():
        results = await player.fetch_tracks(query)

    if not results:
        await ctx.send("❌ Nothing found.")
        return

    track = results[0] if isinstance(results, list) else results.tracks[0]
    await player.play(track)
    await ctx.send(f"▶ Playing **{track}**.")


# Filter commands
@bot.command(name="nightcore")
async def nightcore(ctx: commands.Context) -> None:
    """Toggle nightcore effect (faster + higher pitch)."""
    player = await _get_player(ctx)
    if not player:
        return

    if await player.has_filter("nightcore"):
        await player.remove_filter("nightcore", fast_apply=True)
        await ctx.send("✅ Nightcore removed.")
    else:
        await player.add_filter(PRESETS["nightcore"], label="nightcore", fast_apply=True)
        await ctx.send("🌙 Nightcore enabled!")


@bot.command(name="bassboost")
async def bassboost(ctx: commands.Context) -> None:
    """Toggle bass boost equalizer."""
    player = await _get_player(ctx)
    if not player:
        return

    if await player.has_filter("bassboost"):
        await player.remove_filter("bassboost", fast_apply=True)
        await ctx.send("✅ Bass boost removed.")
    else:
        await player.add_filter(PRESETS["bassboost"], label="bassboost", fast_apply=True)
        await ctx.send("🔊 Bass boost enabled!")


@bot.command(name="8d")
async def eightd(ctx: commands.Context) -> None:
    """Toggle 8D audio (stereo rotation effect)."""
    player = await _get_player(ctx)
    if not player:
        return

    if await player.has_filter("8d"):
        await player.remove_filter("8d", fast_apply=True)
        await ctx.send("✅ 8D audio removed.")
    else:
        await player.add_filter(PRESETS["8d"], label="8d", fast_apply=True)
        await ctx.send("🎧 8D audio enabled!")


@bot.command(name="slowreverb")
async def slowreverb(ctx: commands.Context) -> None:
    """Toggle slow + reverb (slowed + tremolo)."""
    player = await _get_player(ctx)
    if not player:
        return

    if await player.has_filter("slowreverb"):
        await player.remove_filter("slowreverb", fast_apply=True)
        await ctx.send("✅ Slow reverb removed.")
    else:
        await player.add_filter(PRESETS["slowreverb"], label="slowreverb", fast_apply=True)
        await ctx.send("🌊 Slow reverb enabled!")


@bot.command(name="karaoke")
async def karaoke(ctx: commands.Context) -> None:
    """Toggle karaoke mode (removes vocals)."""
    player = await _get_player(ctx)
    if not player:
        return

    if await player.has_filter("karaoke"):
        await player.remove_filter("karaoke", fast_apply=True)
        await ctx.send("✅ Karaoke removed.")
    else:
        await player.add_filter(PRESETS["karaoke"], label="karaoke", fast_apply=True)
        await ctx.send("🎤 Karaoke mode enabled!")


@bot.command(name="filters")
async def filters(ctx: commands.Context) -> None:
    """List all active filters on the player."""
    player: wavecord.Player | None = ctx.voice_client  # type: ignore[assignment]
    if not player:
        await ctx.send("Not connected.")
        return

    active = list(player._filters.keys())
    if not active:
        await ctx.send("No filters are currently active.")
        return

    await ctx.send(f"🎚 Active filters: **{', '.join(active)}**")


@bot.command(name="clearfilters")
async def clearfilters(ctx: commands.Context) -> None:
    """Remove all active filters."""
    player: wavecord.Player | None = ctx.voice_client  # type: ignore[assignment]
    if not player:
        await ctx.send("Not connected.")
        return

    await player.clear_filters(fast_apply=True)
    await ctx.send("✅ All filters cleared.")


# Node info command
@bot.command(name="nodeinfo")
async def nodeinfo(ctx: commands.Context) -> None:
    """Show info about all connected Lavalink nodes."""
    nodes = wavecord.NodePool.nodes
    if not nodes:
        await ctx.send("No nodes connected.")
        return

    embed = discord.Embed(title="WaveCord Nodes", color=0x5865F2)
    for node in nodes:
        stats = node.stats
        if stats:
            value = (
                f"Players: {stats.player_count} ({stats.playing_player_count} playing)\n"
                f"CPU: {stats.cpu.lavalink_load:.1%}\n"
                f"Memory: {stats.memory.used // 1024 // 1024}MB / "
                f"{stats.memory.reservable // 1024 // 1024}MB\n"
                f"Uptime: {stats.uptime}"
            )
        else:
            value = "No stats yet."
        embed.add_field(name=f"🟢 {node.label}", value=value, inline=False)

    await ctx.send(embed=embed)


# Entry point
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN environment variable is not set.")
    bot.run(token)
